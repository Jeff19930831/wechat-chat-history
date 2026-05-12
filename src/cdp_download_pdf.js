/**
 * 用 Playwright CDP 批量下载飞书 PDF（研报/刊物）
 *
 * 策略：
 * 1. 启动浏览器，先手动登录飞书（或复用已登录的 profile）
 * 2. 逐个打开飞书链接
 * 3. 等待页面加载后，尝试触发 PDF 导出/下载
 *
 * 用法：
 *   node cdp_download_pdf.js [--headed] [--start 0] [--count 10]
 *
 * --headed  : 显示浏览器窗口（首次登录需要）
 * --start N : 从第 N 个链接开始
 * --count N : 下载 N 个链接
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const LINKS_FILE = path.join(__dirname, '..', 'data', 'feishu_links.json');
const OUTPUT_DIR = 'D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/pdf';
const USER_DATA_DIR = path.join(__dirname, 'data', 'browser_profile');

const args = process.argv.slice(2);
const HEADED = args.includes('--headed');
const startIdx = parseInt(args[args.indexOf('--start') + 1]) || 0;
const count = parseInt(args[args.indexOf('--count') + 1]) || 999;
const DELAY = 3000;

async function main() {
  const linksData = JSON.parse(fs.readFileSync(LINKS_FILE, 'utf-8'));
  const pdfLinks = linksData.pdf.slice(startIdx, startIdx + count);

  console.log(`PDF links to download: ${pdfLinks.length} (starting from ${startIdx})`);

  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  fs.mkdirSync(USER_DATA_DIR, { recursive: true });

  const browser = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: !HEADED,
    viewport: { width: 1280, height: 900 },
    acceptDownloads: true,
    // 不自动下载，我们手动处理
  });

  const page = await browser.newPage();

  // 设置下载行为
  const downloadDir = OUTPUT_DIR;

  let ok = 0;
  let fail = 0;

  for (let i = 0; i < pdfLinks.length; i++) {
    const item = pdfLinks[i];
    const { date, type, url } = item;
    const token = url.split('/').pop().split('?')[0];
    const outName = `${date}_${type}_${token}.pdf`;
    const outPath = path.join(downloadDir, outName);

    if (fs.existsSync(outPath) && fs.statSync(outPath).size > 5000) {
      console.log(`[${i + 1}/${pdfLinks.length}] SKIP ${date} ${type}`);
      ok++;
      continue;
    }

    console.log(`[${i + 1}/${pdfLinks.length}] ${date} ${type} ${url.substring(0, 60)}...`);

    try {
      // 监听下载事件
      const downloadPromise = page.waitForEvent('download', { timeout: 15000 }).catch(() => null);

      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });

      // 等页面加载
      await page.waitForTimeout(2000);

      // 尝试找到下载/导出按钮
      // 飞书文档页面可能有不同的 UI，尝试几种方式

      // 方式1：直接打印为 PDF（通用方式）
      // 检查是否是 PDF 内嵌页面
      const isPdfEmbed = await page.evaluate(() => {
        return document.querySelector('embed[type="application/pdf"]') !== null ||
               document.querySelector('iframe[src*="pdf"]') !== null;
      });

      if (isPdfEmbed) {
        // 如果是 PDF 内嵌，直接获取 PDF URL
        const pdfSrc = await page.evaluate(() => {
          const embed = document.querySelector('embed[type="application/pdf"]');
          if (embed) return embed.src;
          const iframe = document.querySelector('iframe[src*="pdf"]');
          if (iframe) return iframe.src;
          return null;
        });

        if (pdfSrc) {
          console.log(`  Found embedded PDF, downloading...`);
          const resp = await page.request.get(pdfSrc);
          const body = await resp.body();
          fs.writeFileSync(outPath, body);
          console.log(`  OK (${body.length} bytes)`);
          ok++;
          continue;
        }
      }

      // 方式2：尝试用页面 PDF 打印
      await page.pdf({
        path: outPath,
        format: 'A4',
        printBackground: true,
        margin: { top: '20px', bottom: '20px', left: '20px', right: '20px' }
      });

      const size = fs.statSync(outPath).size;
      if (size > 3000) {
        console.log(`  OK via print (${size} bytes)`);
        ok++;
      } else {
        fs.unlinkSync(outPath);
        console.log(`  FAIL (too small: ${size} bytes)`);
        fail++;
      }

    } catch (err) {
      console.log(`  FAIL: ${err.message.substring(0, 80)}`);
      fail++;
    }

    if (i < pdfLinks.length - 1) {
      await page.waitForTimeout(DELAY);
    }
  }

  console.log(`\n完成! OK=${ok}, FAIL=${fail}`);
  await browser.close();
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
