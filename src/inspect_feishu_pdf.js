/**
 * 检查飞书文档页面内的嵌入文件结构
 * 用法: node inspect_feishu_pdf.js <url>
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const USER_DATA_DIR = path.join(__dirname, '..', 'data', 'browser_profile');
const url = process.argv[2] || 'https://nd9fgiy0w0.feishu.cn/wiki/VfJQwgnfqi1MSDks9WlctZ0Wnih';

async function main() {
  const browser = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: true,
    viewport: { width: 1280, height: 900 },
  });

  const page = await browser.newPage();

  console.log('Opening:', url);
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(5000);

  // Check all iframes
  const frames = page.frames();
  console.log(`\nFrames: ${frames.length}`);
  for (const frame of frames) {
    console.log(`  Frame: ${frame.url().substring(0, 120)}`);
  }

  // Look for embedded file links in the page
  const fileInfo = await page.evaluate(() => {
    const results = [];

    // Check for file viewer components
    const viewers = document.querySelectorAll('.progress-viewer-wrapper, .file-viewer, [class*="file"], [class*="attachment"]');
    viewers.forEach(el => {
      results.push({
        type: 'viewer',
        class: el.className,
        text: el.innerText?.substring(0, 100),
      });
    });

    // Check for links to files
    const links = document.querySelectorAll('a[href*="feishu.cn"], a[href*="drive"], a[href*="file"]');
    links.forEach(el => {
      results.push({
        type: 'link',
        href: el.href?.substring(0, 200),
        text: el.innerText?.substring(0, 50),
      });
    });

    // Check for data attributes
    const dataEls = document.querySelectorAll('[data-token], [data-file-token], [data-obj-token]');
    dataEls.forEach(el => {
      results.push({
        type: 'data-attr',
        'data-token': el.dataset.token,
        'data-file-token': el.dataset.fileToken,
        'data-obj-token': el.dataset.objToken,
        class: el.className?.substring(0, 80),
      });
    });

    // Check iframes
    const iframes = document.querySelectorAll('iframe');
    iframes.forEach(el => {
      results.push({
        type: 'iframe',
        src: el.src?.substring(0, 200),
      });
    });

    // Check embed elements
    const embeds = document.querySelectorAll('embed, object');
    embeds.forEach(el => {
      results.push({
        type: 'embed',
        src: el.src || el.data,
      });
    });

    return results;
  });

  console.log('\nFound elements:', fileInfo.length);
  for (const info of fileInfo) {
    console.log(JSON.stringify(info, null, 2));
  }

  // Try to find file blocks in docx content
  const blockInfo = await page.evaluate(() => {
    // Look for file block elements
    const blocks = document.querySelectorAll('[data-block-id]');
    const fileBlocks = [];
    for (const block of blocks) {
      const text = block.innerText?.trim() || '';
      if (text.includes('.pdf') || text.includes('MB') || text.includes('KB')) {
        fileBlocks.push({
          blockId: block.dataset.blockId,
          text: text.substring(0, 200),
          tag: block.tagName,
          class: block.className?.substring(0, 80),
        });
      }
    }
    return fileBlocks;
  });

  console.log('\nFile-related blocks:', blockInfo.length);
  for (const b of blockInfo) {
    console.log(JSON.stringify(b));
  }

  // Intercept network requests for PDF URLs
  const pdfUrls = [];
  page.on('response', resp => {
    const url = resp.url();
    if (url.includes('.pdf') || url.includes('file_token') || url.includes('download') || url.includes('obj/lark')) {
      pdfUrls.push({ url: url.substring(0, 200), status: resp.status(), contentType: resp.headers()['content-type'] || '' });
    }
  });

  // Scroll to trigger lazy loading
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(3000);

  console.log('\nPDF-related network requests:', pdfUrls.length);
  for (const r of pdfUrls) {
    console.log(JSON.stringify(r));
  }

  // Save page HTML for debugging
  const html = await page.content();
  const debugPath = path.join(__dirname, '..', 'data', 'debug_feishu_page.html');
  fs.writeFileSync(debugPath, html, 'utf-8');
  console.log(`\nHTML saved to ${debugPath} (${html.length} chars)`);

  await browser.close();
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
