/**
 * 用 Playwright CDP 批量抓取 Port News Selected 文字内容
 * 将飞书文档渲染后提取文本，保存为 Markdown
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const LINKS_FILE = path.join(__dirname, '..', 'data', 'feishu_links.json');
const TEXT_DIR = 'D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/text';
const USER_DATA_DIR = path.join(__dirname, '..', 'data', 'browser_profile');

async function main() {
  const linksData = JSON.parse(fs.readFileSync(LINKS_FILE, 'utf-8'));
  const textLinks = linksData.text;

  console.log(`Text links to fetch: ${textLinks.length}`);

  fs.mkdirSync(TEXT_DIR, { recursive: true });

  const browser = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: true,
    viewport: { width: 1280, height: 900 },
  });

  const page = await browser.newPage();

  let ok = 0;
  let fail = 0;

  for (let i = 0; i < textLinks.length; i++) {
    const item = textLinks[i];
    const { date, url } = item;
    const token = url.split('/').pop().split('?')[0];
    const outName = `${date}_PortNews_${token}.md`;
    const outPath = path.join(TEXT_DIR, outName);

    if (fs.existsSync(outPath) && fs.statSync(outPath).size > 200) {
      console.log(`[${i + 1}/${textLinks.length}] SKIP ${date}`);
      ok++;
      continue;
    }

    console.log(`[${i + 1}/${textLinks.length}] ${date} ${url.substring(0, 60)}...`);

    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      // 等待内容渲染
      await page.waitForTimeout(3000);

      // 提取标题
      const title = await page.title();

      // 提取正文内容：飞书文档的正文通常在 .docx-container 或 article 等区域
      const content = await page.evaluate(() => {
        // 尝试多种选择器
        const selectors = [
          '.docx-container',
          '.docx-page-content',
          '[data-block-id]',
          'article',
          '.render-unit-wrapper',
          '.title-container',
          '#content-container',
        ];

        let texts = [];
        for (const sel of selectors) {
          const els = document.querySelectorAll(sel);
          if (els.length > 0) {
            els.forEach(el => {
              const t = el.innerText?.trim();
              if (t && t.length > 20) texts.push(t);
            });
          }
        }

        if (texts.length > 0) {
          return texts.join('\n\n');
        }

        // Fallback: 取 body 的文本，但排除 header/footer
        const body = document.body.cloneNode(true);
        // 移除导航、侧边栏等
        body.querySelectorAll('nav, header, footer, .sidebar, .header-bar, .comment-panel').forEach(el => el.remove());
        const bodyText = body.innerText?.trim();
        if (bodyText && bodyText.length > 200) {
          return bodyText;
        }

        return null;
      });

      if (content && content.length > 100) {
        // 清理内容
        const cleanTitle = (title || 'Unknown').replace(/ - 飞书云文档$/, '').replace(/飞书文档.*$/, '').trim();
        const cleanContent = content
          .replace(/\n{3,}/g, '\n\n')
          .trim();

        fs.writeFileSync(outPath,
          `# ${cleanTitle}\n\n> 来源: ${url}\n> 日期: ${date}\n\n${cleanContent}`,
          'utf-8');
        console.log(`  OK (${cleanContent.length} chars)`);
        ok++;
      } else {
        // 保存页面 HTML 以便调试
        const htmlContent = await page.content();
        const debugPath = path.join(TEXT_DIR, `${date}_debug.html`);
        fs.writeFileSync(debugPath, htmlContent, 'utf-8');

        fs.writeFileSync(outPath,
          `# ${title || 'Unknown'}\n\n> 来源: ${url}\n> 日期: ${date}\n\n> 抓取失败（内容不足）\n`,
          'utf-8');
        console.log(`  FAIL (content too short or empty)`);
        fail++;
      }

    } catch (err) {
      console.log(`  FAIL: ${err.message.substring(0, 80)}`);
      fs.writeFileSync(outPath,
        `# Unknown\n\n> 来源: ${url}\n> 日期: ${date}\n\n> 抓取失败: ${err.message}\n`,
        'utf-8');
      fail++;
    }

    // 3s delay between requests
    if (i < textLinks.length - 1) {
      await page.waitForTimeout(3000);
    }
  }

  console.log(`\n完成! OK=${ok}, FAIL=${fail}`);
  await browser.close();
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
