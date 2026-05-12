"""批量抓取飞书文档内容并保存为 Markdown
- 从聊天记录中提取飞书链接
- 用 web reader 抓取内容
- 保存为 Markdown 文件
"""

import re
import os
import sys
import json
import time
import subprocess
from pathlib import Path

CHAT_DIR = "D:/Wechat_File/Wechat_ChatHistory/port-news-t3"
OUTPUT_DIR = "D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu"


def extract_links():
    """从聊天记录中提取所有飞书链接"""
    links = {}  # url -> date
    for md_file in sorted(Path(CHAT_DIR).glob("*.md")):
        month = md_file.stem  # e.g. 2026_05
        text = md_file.read_text(encoding="utf-8")
        for line in text.split("\n"):
            # 提取日期
            date_match = re.match(r"- \[(\d{4}-\d{2}-\d{2})", line)
            if not date_match:
                continue
            date = date_match.group(1)
            # 提取飞书链接
            urls = re.findall(r'https://[^\s]+feishu\.cn[^\s]*', line)
            for url in urls:
                url = url.rstrip(",.;>)")
                if url not in links:
                    links[url] = {"date": date, "month": month}
    return links


def fetch_url(url):
    """用 curl 抓取飞书文档页面"""
    try:
        result = subprocess.run(
            ["curl", "-sL", "-H", "User-Agent: Mozilla/5.0", url],
            capture_output=True, text=True, encoding="utf-8",
            timeout=30,
        )
        html = result.stdout
        # 提取 SSR 内容
        title_match = re.search(r'<title>(.*?)</title>', html)
        title = title_match.group(1) if title_match else "Unknown"

        # 尝试从 meta 提取
        content_match = re.search(r'"content":"(.*?)"(?:,|})', html)
        if content_match:
            content = content_match.group(1)
            content = content.replace("\\n", "\n").replace('\\"', '"')
            content = re.sub(r'​', '', content)
            return title, content

        # 尝试从 SSR 渲染的内容提取
        ssr_match = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
        if ssr_match:
            text = ssr_match.group(1)
            text = re.sub(r'<[^>]+>', '', text)
            text = text.strip()
            if len(text) > 100:
                return title, text

        return title, None
    except Exception as e:
        return f"Error: {e}", None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    links = extract_links()
    print(f"找到 {len(links)} 个唯一飞书链接")

    # 按日期排序
    sorted_links = sorted(links.items(), key=lambda x: x[1]["date"])

    success = 0
    failed = 0

    for i, (url, meta) in enumerate(sorted_links, 1):
        date = meta["date"]
        # 提取 token
        token_match = re.search(r'/([A-Za-z0-9]+)(?:\?|$)', url)
        token = token_match.group(1) if token_match else f"doc_{i}"

        out_file = os.path.join(OUTPUT_DIR, f"{date}_{token}.md")
        if os.path.exists(out_file):
            print(f"[{i}/{len(sorted_links)}] 跳过 {date} (已存在)")
            success += 1
            continue

        print(f"[{i}/{len(sorted_links)}] 抓取 {date} {url[:60]}...")

        title, content = fetch_url(url)

        if content and len(content) > 50:
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n")
                f.write(f"> 来源: {url}\n")
                f.write(f"> 日期: {date}\n\n")
                f.write(content)
            print(f"  保存成功 ({len(content)} chars)")
            success += 1
        else:
            # 保存一个占位文件
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n")
                f.write(f"> 来源: {url}\n")
                f.write(f"> 日期: {date}\n\n")
                f.write(f"> 抓取失败，内容不可用\n")
            print(f"  抓取失败")
            failed += 1

        time.sleep(1)  # 避免过快

    print(f"\n完成! 成功: {success}, 失败: {failed}")


if __name__ == "__main__":
    main()
