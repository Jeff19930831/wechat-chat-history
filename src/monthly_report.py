"""生成月度分析报告（Markdown格式）
- 读取指定月份的聊天记录和图片摘要
- 统计消息数、活跃成员、关键词、图片分类
- 输出为 Markdown 报告
"""

import json
import glob
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

CHAT_BASE = "D:/Wechat_File/Wechat_ChatHistory"
IMAGE_BASE = "D:/Wechat_File/Wechat_Image"
OUTPUT_BASE = "D:/Wechat_File/Wechat_Image"

# 群聊别名映射
GROUP_ALIASES = {
    "jianlong-beijing": "【VIP】建龙北京",
    "jianlong-market": "建龙集团市场分析交流群",
    "mysteel-miner": "Mysteel-铁矿石矿工群（正式）",
    "mysteel-svip": "Mysteel铁矿石资讯SVIP正式2群",
    "zhongkuang-report": "中国矿产市场报告联系人群",
}


def parse_chat_file(filepath):
    """解析聊天记录 Markdown 文件"""
    text = Path(filepath).read_text(encoding="utf-8")
    lines = text.split("\n")

    messages = []
    msg_pattern = re.compile(r"- \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\] (.+?): (.+)")

    for line in lines:
        m = msg_pattern.match(line.strip())
        if m:
            time_str, sender, content = m.groups()
            messages.append({
                "time": time_str,
                "sender": sender.strip(),
                "content": content.strip(),
            })

    return messages


def analyze_chat(messages):
    """分析聊天记录"""
    if not messages:
        return None

    sender_counts = Counter(m["sender"] for m in messages)
    hourly = Counter(int(m["time"][11:13]) for m in messages)
    daily = Counter(m["time"][:10] for m in messages)

    # 关键词提取
    all_text = " ".join(m["content"] for m in messages)
    word_pattern = re.compile(r"[\u4e00-\u9fff]{2,}")
    words = word_pattern.findall(all_text)
    stopwords = set(["图片", "local", "local_id", "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "啊", "呢", "吧", "吗", "哦", "嗯", "哈"])
    keywords = Counter(w for w in words if w not in stopwords and len(w) >= 2)

    return {
        "total": len(messages),
        "unique_senders": len(sender_counts),
        "top_senders": sender_counts.most_common(10),
        "daily_count": len(daily),
        "peak_hour": hourly.most_common(1)[0] if hourly else (None, 0),
        "top_keywords": keywords.most_common(20),
    }


def get_april_images(group_alias):
    """获取 2026-04 月份的图片摘要"""
    summary_file = os.path.join(IMAGE_BASE, group_alias, "_image_summary.json")
    if not os.path.exists(summary_file):
        return []

    with open(summary_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    april_images = []
    for path, summary in data.items():
        if path.startswith("2026_04"):
            april_images.append({"path": path, "summary": summary})

    return april_images


def classify_summary(summary):
    """对摘要进行分类"""
    s = summary.lower()
    if "价格" in summary or "报价" in summary or "现货" in summary or "pb粉" in s:
        return "价格"
    if "库存" in summary:
        return "库存"
    if "产量" in summary or "铁水" in summary or "开工率" in summary:
        return "产量"
    if "到港" in summary or "发运" in summary:
        return "到港"
    if "利润" in summary:
        return "利润"
    if "情绪" in summary or "心态" in summary:
        return "情绪"
    if "成交" in summary:
        return "成交"
    if "基差" in summary or "价差" in summary:
        return "基差"
    return "其他"


def generate_report():
    """生成月度 Markdown 报告"""
    month = "2026_04"
    report_date = datetime.now().strftime("%Y-%m-%d")

    lines = []
    lines.append(f"# 微信群聊数据分析报告 — {month}")
    lines.append(f"")
    lines.append(f"**生成日期**: {report_date}")
    lines.append(f"**数据范围**: 2026-04-01 ~ 2026-04-27")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    total_messages = 0
    total_images = 0
    all_group_stats = []

    for alias, name in GROUP_ALIASES.items():
        # 聊天记录
        chat_file = os.path.join(CHAT_BASE, alias, f"{month}.md")
        messages = parse_chat_file(chat_file) if os.path.exists(chat_file) else []
        chat_stats = analyze_chat(messages)

        # 图片
        images = get_april_images(name)
        image_cats = Counter(classify_summary(img["summary"]) for img in images)

        total_messages += len(messages)
        total_images += len(images)

        all_group_stats.append({
            "alias": alias,
            "name": name,
            "messages": messages,
            "chat_stats": chat_stats,
            "images": images,
            "image_cats": image_cats,
        })

    # 总体概览
    lines.append(f"## 总体概览")
    lines.append(f"")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 群聊数 | {len(GROUP_ALIASES)} |")
    lines.append(f"| 总消息数 | {total_messages} |")
    lines.append(f"| 总图片数 | {total_images} |")
    lines.append(f"")

    # 各群聊详情
    for gs in all_group_stats:
        name = gs["name"]
        chat = gs["chat_stats"]
        images = gs["images"]
        img_cats = gs["image_cats"]

        lines.append(f"## {name}")
        lines.append(f"")

        # 消息统计
        if chat:
            lines.append(f"### 消息统计")
            lines.append(f"")
            lines.append(f"| 指标 | 数值 |")
            lines.append(f"|------|------|")
            lines.append(f"| 总消息数 | {chat['total']} |")
            lines.append(f"| 活跃成员 | {chat['unique_senders']} |")
            lines.append(f"| 活跃天数 | {chat['daily_count']} |")
            if chat['peak_hour'][0] is not None:
                lines.append(f"| 高峰时段 | {chat['peak_hour'][0]}:00 ({chat['peak_hour'][1]} 条) |")
            lines.append(f"")

            # 活跃成员 Top 5
            if chat['top_senders']:
                lines.append(f"**活跃成员 Top 5**:")
                lines.append(f"")
                lines.append(f"| 排名 | 成员 | 消息数 |")
                lines.append(f"|------|------|--------|")
                for i, (sender, count) in enumerate(chat['top_senders'][:5], 1):
                    lines.append(f"| {i} | {sender} | {count} |")
                lines.append(f"")

            # 关键词 Top 10
            if chat['top_keywords']:
                lines.append(f"**关键词 Top 10**:")
                lines.append(f"")
                kw_list = ", ".join([f"{w}({c})" for w, c in chat['top_keywords'][:10]])
                lines.append(f"{kw_list}")
                lines.append(f"")

        # 图片统计
        if images:
            lines.append(f"### 图片统计 ({len(images)} 张)")
            lines.append(f"")
            if img_cats:
                lines.append(f"| 类别 | 数量 |")
                lines.append(f"|------|------|")
                for cat, count in img_cats.most_common():
                    lines.append(f"| {cat} | {count} |")
                lines.append(f"")

            # 典型图片摘要
            lines.append(f"**典型图片**:")
            lines.append(f"")
            for i, img in enumerate(images[:5], 1):
                lines.append(f"{i}. {img['summary']}")
            lines.append(f"")
        else:
            lines.append(f"### 图片统计")
            lines.append(f"")
            lines.append(f"本月无图片数据。")
            lines.append(f"")

        lines.append(f"---")
        lines.append(f"")

    # 行业数据亮点
    lines.append(f"## 行业数据亮点")
    lines.append(f"")

    # 收集所有图片摘要中的关键数据点
    all_summaries = []
    for gs in all_group_stats:
        for img in gs["images"]:
            all_summaries.append(img["summary"])

    # 提取价格相关
    price_pattern = re.compile(r"(\d+)元/湿吨|(\d+)元/吨|PB粉.*?([\d.]+)")
    prices = []
    for s in all_summaries:
        m = price_pattern.search(s)
        if m:
            prices.append(s[:80])

    if prices:
        lines.append(f"### 价格动态")
        lines.append(f"")
        for p in prices[:5]:
            lines.append(f"- {p}...")
        lines.append(f"")

    # 提取库存相关
    inventory_pattern = re.compile(r"库存.*?([\d.]+).*?万吨|([\d.]+).*?万吨")
    inventory_items = [s[:80] for s in all_summaries if "库存" in s]
    if inventory_items:
        lines.append(f"### 库存变化")
        lines.append(f"")
        for item in inventory_items[:5]:
            lines.append(f"- {item}...")
        lines.append(f"")

    # 写入文件
    output_file = os.path.join(OUTPUT_BASE, f"_monthly_report_{month}.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"报告已生成: {output_file}")
    print(f"总消息: {total_messages}, 总图片: {total_images}")


if __name__ == "__main__":
    generate_report()
