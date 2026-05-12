"""从 Port News T3 聊天记录提取飞书链接并分类
- 研报/刊物 → nd9fgiy0w0.feishu.cn 链接（PDF 下载）
- Port News Selected → my.feishu.cn/ai.feishu.cn 链接（文字内容）
"""
import re
import json
from pathlib import Path

CHAT_DIR = "D:/Wechat_File/Wechat_ChatHistory/port-news-t3"
OUTPUT = "D:/ClaudeCode/wechat-chat-history/data/feishu_links.json"

pdf_links = []
text_links = []

for md_file in sorted(Path(CHAT_DIR).glob("*.md")):
    month = md_file.stem
    text = md_file.read_text(encoding="utf-8")
    lines = text.split("\n")

    # Build context: scan for URLs and look backwards for message context
    last_date = ""
    context_lines = []  # buffer of recent non-URL lines for context

    for line in lines:
        dm = re.match(r"- \[(\d{4}-\d{2}-\d{2})", line)
        if dm:
            last_date = dm.group(1)
            context_lines = [line]
            continue

        context_lines.append(line)
        # Keep only recent context (last 10 lines)
        if len(context_lines) > 10:
            context_lines = context_lines[-10:]

        urls = re.findall(r'https://\S+feishu\.cn\S*', line)
        for url in urls:
            url = url.rstrip(",.;>)\"")
            ctx = " ".join(context_lines)

            if "研报" in ctx or "刊物" in ctx:
                pdf_links.append({
                    "date": last_date, "month": month, "url": url,
                    "type": "研报" if "研报" in ctx else "刊物",
                })
            elif "Port News Selected" in ctx or ("港口精选" in ctx and "Port" in ctx):
                text_links.append({
                    "date": last_date, "month": month, "url": url,
                    "type": "Port News Selected",
                })

# 去重
seen_pdf = set()
unique_pdf = []
for l in pdf_links:
    if l["url"] not in seen_pdf:
        seen_pdf.add(l["url"])
        unique_pdf.append(l)

seen_text = set()
unique_text = []
for l in text_links:
    if l["url"] not in seen_text:
        seen_text.add(l["url"])
        unique_text.append(l)

print(f"PDF (研报/刊物): {len(unique_pdf)} 个唯一链接")
print(f"Text (Port News Selected): {len(unique_text)} 个唯一链接")

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({"pdf": unique_pdf, "text": unique_text}, f, ensure_ascii=False, indent=2)

print(f"已保存到 {OUTPUT}")
