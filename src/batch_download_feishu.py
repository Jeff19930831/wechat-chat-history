"""批量下载 Port News T3 飞书文档
- PDF (研报/刊物): curl 下载
- Text (Port News Selected): web reader 抓内容保存为 md
- 3s 间隔防限流
"""
import json
import os
import re
import sys
import time
import subprocess
from pathlib import Path

DATA_FILE = "D:/ClaudeCode/wechat-chat-history/data/feishu_links.json"
PDF_DIR = "D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/pdf"
TEXT_DIR = "D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/text"
DELAY = 3  # seconds between requests


def download_pdf(url, out_path):
    """用 curl 下载飞书文档页面，尝试提取 PDF"""
    try:
        result = subprocess.run(
            ["curl", "-sL", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
             "-H", "Accept: text/html,application/pdf,*/*",
             "-o", out_path, "-w", "%{http_code}|%{content_type}",
             url],
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
        info = result.stdout.strip()
        parts = info.split("|")
        code = parts[0] if parts else "?"
        ctype = parts[1] if len(parts) > 1 else ""
        return code, ctype
    except Exception as e:
        return "ERR", str(e)


def fetch_text(url):
    """用 curl 抓取飞书文档文字内容"""
    try:
        result = subprocess.run(
            ["curl", "-sL", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
             url],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        html = result.stdout

        # 提取标题
        title_m = re.search(r'<title>(.*?)</title>', html)
        title = title_m.group(1) if title_m else "Unknown"

        # 从 SSR JSON 中提取 content
        content_m = re.search(r'"content":"(.*?)"(?:,|})', html)
        if content_m:
            content = content_m.group(1)
            content = content.replace("\\n", "\n").replace('\\"', '"')
            content = re.sub(r'​', '', content)
            if len(content) > 100:
                return title, content

        # Fallback: 从 article 标签提取
        article_m = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
        if article_m:
            text = article_m.group(1)
            text = re.sub(r'<[^>]+>', '', text).strip()
            if len(text) > 100:
                return title, text

        return title, None
    except Exception as e:
        return f"Error: {e}", None


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    pdf_links = data["pdf"]
    text_links = data["text"]

    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(TEXT_DIR, exist_ok=True)

    # === 下载 PDF ===
    print(f"{'='*60}")
    print(f"下载 PDF (研报/刊物): {len(pdf_links)} 个")
    print(f"{'='*60}")

    pdf_ok = 0
    pdf_fail = 0

    for i, item in enumerate(pdf_links, 1):
        date = item["date"]
        url = item["url"]
        dtype = item["type"]
        token = url.split("/")[-1].split("?")[0]
        out_name = f"{date}_{dtype}_{token}"
        out_path = os.path.join(PDF_DIR, out_name)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f"[{i}/{len(pdf_links)}] 跳过 {date} {dtype}")
            pdf_ok += 1
            continue

        print(f"[{i}/{len(pdf_links)}] {date} {dtype} {url[:60]}...")
        code, ctype = download_pdf(url, out_path)

        size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
        if size > 1000:
            print(f"  OK ({size} bytes, HTTP {code}, {ctype[:30]})")
            pdf_ok += 1
        else:
            print(f"  FAIL (HTTP {code}, {size} bytes)")
            # 如果不是 PDF，可能是 HTML 页面，尝试重命名为 .html
            if os.path.exists(out_path):
                html_path = out_path + ".html"
                os.rename(out_path, html_path)
            pdf_fail += 1

        if i < len(pdf_links):
            time.sleep(DELAY)

    # === 下载文字内容 ===
    print(f"\n{'='*60}")
    print(f"下载文字 (Port News Selected): {len(text_links)} 个")
    print(f"{'='*60}")

    text_ok = 0
    text_fail = 0

    for i, item in enumerate(text_links, 1):
        date = item["date"]
        url = item["url"]
        token = url.split("/")[-1].split("?")[0]
        out_path = os.path.join(TEXT_DIR, f"{date}_PortNews_{token}.md")

        if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
            print(f"[{i}/{len(text_links)}] 跳过 {date}")
            text_ok += 1
            continue

        print(f"[{i}/{len(text_links)}] {date} {url[:60]}...")
        title, content = fetch_text(url)

        if content:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n")
                f.write(f"> 来源: {url}\n> 日期: {date}\n\n")
                f.write(content)
            print(f"  OK ({len(content)} chars)")
            text_ok += 1
        else:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n> 来源: {url}\n> 日期: {date}\n\n> 抓取失败\n")
            print(f"  FAIL")
            text_fail += 1

        if i < len(text_links):
            time.sleep(DELAY)

    print(f"\n{'='*60}")
    print(f"完成!")
    print(f"  PDF: 成功={pdf_ok}, 失败={pdf_fail}")
    print(f"  文字: 成功={text_ok}, 失败={text_fail}")


if __name__ == "__main__":
    main()
