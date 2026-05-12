/**
 * 用 Playwright CDP 从飞书文档中下载嵌入的实际 PDF 文件
 *
 * 策略：
 * 1. 打开飞书文档页面
 * 2. 找到所有 data-block-type="file" 的文件块
 * 3. 点击每个文件块，拦截网络请求获取 file token
 * 4. 通过 preview API 下载实际 PDF
 *
 * 用法：
 *   node cdp_download_real_pdf.js [--start 0] [--count 10] [--headed]
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const LINKS_FILE = path.join(__dirname, '..', 'data', 'feishu_links.json');
const OUTPUT_DIR = 'D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/pdf_real';
const USER_DATA_DIR = path.join(__dirname, '..', 'data', 'browser_profile');
const PROGRESS_FILE = path.join(__dirname, '..', 'data', 'pdf_download_progress.json');

const args = process.argv.slice(2);
const HEADED = args.includes('--headed');
const startIdx = parseInt(args[args.indexOf('--start') + 1]) || 0;
const count = parseInt(args[args.indexOf('--count') + 1]) || 999;

// Load or create progress tracker
let progress = {};
if (fs.existsSync(PROGRESS_FILE)) {
  progress = JSON.parse(fs.readFileSync(PROGRESS_FILE, 'utf-8'));
}

function saveProgress() {
  fs.writeFileSync(PROGRESS_FILE, JSON.stringify(progress, null, 2));
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function downloadFilesFromPage(page, pageUrl, pageLabel) {
  console.log(`\nOpening: ${pageLabel}`);
  console.log(`  URL: ${pageUrl.substring(0, 80)}...`);

  try {
    await page.goto(pageUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await sleep(5000);
  } catch (err) {
    console.log(`  FAIL to load page: ${err.message.substring(0, 80)}`);
    return { ok: 0, fail: 0 };
  }

  // Get all file blocks
  const fileInfo = await page.evaluate(() => {
    const blocks = document.querySelectorAll('[data-block-type="file"]');
    return Array.from(blocks).map(block => ({
      recordId: block.dataset.recordId,
      name: block.querySelector('.file-name')?.innerText?.trim(),
      size: block.querySelector('.file-desc')?.innerText?.trim(),
    })).filter(f => f.recordId && f.name);
  });

  if (fileInfo.length === 0) {
    // Check if we need to login
    const needsLogin = await page.evaluate(() => {
      return document.querySelector('.login-btn') !== null ||
             document.title?.includes('登录');
    });
    if (needsLogin) {
      console.log('  NEED LOGIN - run with --headed first');
      return { ok: 0, fail: 0 };
    }
    console.log(`  No embedded files found`);
    return { ok: 0, fail: 0 };
  }

  console.log(`  Found ${fileInfo.length} embedded file(s)`);
  let ok = 0, fail = 0;

  for (let i = 0; i < fileInfo.length; i++) {
    const file = fileInfo[i];
    const safeName = file.name.replace(/[<>:"/\\|?*]/g, '_');
    const outPath = path.join(OUTPUT_DIR, safeName);

    // Skip if already downloaded
    if (fs.existsSync(outPath) && fs.statSync(outPath).size > 5000) {
      console.log(`  [${i + 1}/${fileInfo.length}] SKIP ${file.name}`);
      ok++;
      continue;
    }

    console.log(`  [${i + 1}/${fileInfo.length}] ${file.name} (${file.size})`);

    // Capture file token from network
    let capturedToken = null;
    let capturedVersion = null;

    const handler = (req) => {
      const u = req.url();
      const tm = u.match(/box\/stream\/download\/(?:preview|v2\/cover)\/([a-zA-Z0-9]+)\?/);
      if (tm) capturedToken = tm[1];
      const vm = u.match(/version=(\d+)/);
      if (vm) capturedVersion = vm[1];
    };
    page.on('request', handler);

    try {
      // Click the file card
      const selector = `[data-record-id="${file.recordId}"] .file-card`;
      await page.click(selector, { timeout: 10000 });
      await sleep(4000);

      if (!capturedToken) {
        console.log(`    FAIL: could not capture file token`);
        fail++;
        continue;
      }

      // Download using preview API
      const downloadUrl = `https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/preview/${capturedToken}?preview_type=16&version=${capturedVersion || ''}&mount_point=docx_file`;

      const resp = await page.request.get(downloadUrl, { timeout: 120000 });
      const body = await resp.body();

      if (body.length > 5000) {
        fs.writeFileSync(outPath, body);
        console.log(`    OK (${(body.length / 1024 / 1024).toFixed(2)} MB)`);
        ok++;
      } else {
        console.log(`    FAIL: too small (${body.length} bytes)`);
        fail++;
      }

      // Close preview/go back
      // Try pressing Escape to close the preview panel
      await page.keyboard.press('Escape');
      await sleep(2000);

    } catch (err) {
      console.log(`    FAIL: ${err.message.substring(0, 100)}`);
      fail++;
      // Navigate back to the page
      try {
        await page.goto(pageUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await sleep(3000);
      } catch (e) {}
    } finally {
      page.removeListener('request', handler);
    }
  }

  return { ok, fail };
}

async function main() {
  const linksData = JSON.parse(fs.readFileSync(LINKS_FILE, 'utf-8'));
  const pdfLinks = linksData.pdf.slice(startIdx, startIdx + count);

  console.log(`PDF pages to process: ${pdfLinks.length} (starting from ${startIdx})`);
  console.log(`Output: ${OUTPUT_DIR}`);

  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: !HEADED,
    viewport: { width: 1280, height: 900 },
    acceptDownloads: true,
  });

  const page = await browser.newPage();

  let totalOk = 0, totalFail = 0;

  for (let i = 0; i < pdfLinks.length; i++) {
    const item = pdfLinks[i];
    const { date, type, url } = item;

    // Check if this page was already fully processed
    const progressKey = `${date}_${url}`;
    if (progress[progressKey] === 'done') {
      console.log(`[${i + 1}/${pdfLinks.length}] SKIP PAGE ${date} ${type}`);
      continue;
    }

    console.log(`\n[${i + 1}/${pdfLinks.length}] ${date} ${type}`);

    const result = await downloadFilesFromPage(page, url, `${date} ${type}`);
    totalOk += result.ok;
    totalFail += result.fail;

    // Mark as done
    if (result.fail === 0) {
      progress[progressKey] = 'done';
      saveProgress();
    }

    // Delay between pages
    if (i < pdfLinks.length - 1) {
      await sleep(3000);
    }
  }

  console.log(`\n${'='.repeat(60)}`);
  console.log(`Total: OK=${totalOk}, FAIL=${totalFail}`);

  saveProgress();
  await browser.close();
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
