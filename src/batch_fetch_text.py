"""用 MCP web reader 批量抓取 Port News Selected 文字内容
从 feishu_links.json 读取 text 链接，用 web reader 获取内容
"""
import json
import os
import re
import sys
import time
import subprocess
from pathlib import Path

DATA_FILE = "D:/ClaudeCode/wechat-chat-history/data/feishu_links.json"
TEXT_DIR = "D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/text"
DELAY = 3


def fetch_with_web_reader(url):
    """用 mcp web-reader 抓取飞书文档"""
    try:
        # 使用 node 调用 web reader
        result = subprocess.run(
            ["npx", "-y", "@anthropic-ai/mcp-web-reader", url],
            capture_output=True, text=True, encoding="utf-8",
            timeout=30,
        )
        output = result.stdout
        if output and len(output) > 200:
            # 提取内容
            title_m = re.search(r'"title":\s*"([^"]*)"', output)
            content_m = re.search(r'"content":\s*"([^"]*)"', output)

            title = title_m.group(1) if title_m else "Unknown"
            if content_m:
                content = content_m.group(1)
                content = content.replace("\\n", "\n").replace('\\"', '"')
                content = re.sub(r'​', '', content)
                return title, content

        return None, None
    except:
        return None, None


def fetch_with_curl(url):
    """用 curl 抓取并从 HTML 提取内容"""
    try:
        result = subprocess.run(
            ["curl", "-sL", "-H",
             "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
             url],
            capture_output=True, text=True, encoding="utf-8",
            timeout=30,
        )
        html = result.stdout
        if not html or len(html) < 500:
            return None, None

        # 提取标题
        title_m = re.search(r'<title>(.*?)</title>', html)
        title = title_m.group(1) if title_m else "Unknown"

        # 从 SSR JSON 提取 content
        content_m = re.search(r'"content"\s*:\s*"(.*?)"(?:\s*,|\s*})', html)
        if content_m:
            content = content_m.group(1)
            content = content.replace("\\n", "\n").replace('\\"', '"')
            content = re.sub(r'​', '', content)
            if len(content) > 100:
                return title, content

        return title, None
    except:
        return None, None


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    text_links = data["text"]
    os.makedirs(TEXT_DIR, exist_ok=True)

    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    count = int(sys.argv[2]) if len(sys.argv) > 2 else len(text_links)
    items = text_links[start:start + count]

    print(f"Text links to fetch: {len(items)} (from index {start})")

    ok = 0
    fail = 0

    for i, item in enumerate(items, 1):
        date = item["date"]
        url = item["url"]
        token = url.split("/")[-1].split("?")[0]
        out_path = os.path.join(TEXT_DIR, f"{date}_PortNews_{token}.md")

        if os.path.exists(out_path) and os.path.getsize(out_path) > 200:
            print(f"[{i}/{len(items)}] SKIP {date}")
            ok += 1
            continue

        print(f"[{i}/{len(items)}] {date} {url[:60]}...")

        title, content = fetch_with_curl(url)

        if not content:
            title, content = fetch_with_web_reader(url)

        if content and len(content) > 100:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n")
                f.write(f"> 来源: {url}\n> 日期: {date}\n\n")
                f.write(content)
            print(f"  OK ({len(content)} chars)")
            ok += 1
        else:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# {title or 'Unknown'}\n\n")
                f.write(f"> 来源: {url}\n> 日期: {date}\n\n> 抓取失败\n")
            print(f"  FAIL")
            fail += 1

        if i < len(items):
            time.sleep(DELAY)

    print(f"\n完成! OK={ok}, FAIL={fail}")


if __name__ == "__main__":
    main()
