"""从聊天记录中提取价格/库存/产量等结构化数据
- 解析实时报盘、实时成交、库存报告等消息
- 输出为 Markdown 表格
"""

import re
import glob
import os
import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime

CHAT_BASE = "D:/Wechat_File/Wechat_ChatHistory"
IMAGE_BASE = "D:/Wechat_File/Wechat_Image"
OUTPUT_FILE = "D:/Wechat_File/Wechat_Image/_price_data_2026_04.md"

# 实时报盘正则
# 格式: 实时报盘: 港口 品种 价格 涨跌 （前一日行情 前值）
PRICE_PATTERN = re.compile(
    r'实时报盘:\s*'
    r'(\S+?)\s+'
    r'(PB粉\d+[\d.]*%?|麦克粉|卡粉|超特粉|混合粉(?:\（?[\d.]+%?\）?)?|'
    r'巴西精粉(?:\（?[\d.]+%?\）?)?|乌克兰精粉|塞拉利昂粉|'
    r'PB块\d+[\d.]*%?)\s+'
    r'(\d+)\s*'
    r'(涨\d+|跌\d+|平)?\s*'
    r'(?:（前一日行情\s*(\d+)）)?'
)

# 成交正则
DEAL_PATTERN = re.compile(
    r'\[玫瑰\]实时成交\[\d+\]:\s*'
    r'(\S+?)\s+'
    r'(.*?)\s+'
    r'(\d+)\s*'
    r'(昨日成交|今日成交)?'
)

# 情绪/日报正则
DAILY_PRICE_PATTERN = re.compile(
    r'(\d{2}:\d{2})\s*【我的钢铁】\s*'
    r'.*?'
    r'(进口矿价格|日报|价格)'
)


def parse_price_line(line):
    """从单行提取报盘数据"""
    m = PRICE_PATTERN.search(line)
    if m:
        port, product, price, change, prev = m.groups()
        return {
            "type": "报盘",
            "port": port,
            "product": product,
            "price": int(price),
            "change": change or "",
            "prev_price": int(prev) if prev else None,
        }

    m = DEAL_PATTERN.search(line)
    if m:
        port, product, price, deal_type = m.groups()
        return {
            "type": "成交",
            "port": port,
            "product": product.strip(),
            "price": int(price),
            "change": deal_type or "",
            "prev_price": None,
        }
    return None


def extract_from_chat(filepath):
    """从聊天记录提取所有价格数据"""
    text = Path(filepath).read_text(encoding="utf-8")
    lines = text.split("\n")

    records = []
    for line in lines:
        line = line.strip()
        if not line.startswith("- ["):
            continue

        # 提取时间
        time_match = re.match(r"- \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]", line)
        if not time_match:
            continue
        datetime_str = time_match.group(1)

        # 提取价格数据
        data = parse_price_line(line)
        if data:
            data["datetime"] = datetime_str
            records.append(data)

    return records


def extract_from_images(group_name):
    """从图片摘要提取 2026-04 数据"""
    summary_file = os.path.join(IMAGE_BASE, group_name, "_image_summary.json")
    if not os.path.exists(summary_file):
        return []

    with open(summary_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = []
    for path, summary in data.items():
        if not path.startswith("2026_04"):
            continue

        # 提取价格
        price_matches = re.findall(r'(\d+)\s*元/湿吨', summary)
        if price_matches:
            for price in price_matches:
                records.append({
                    "datetime": path.split("\\")[0].replace("_", "-"),
                    "type": "图片",
                    "product": summary[:30],
                    "price": int(price),
                    "source": "summary",
                })

    return records


def generate_md_report():
    """生成 Markdown 报告"""
    all_records = []

    # 从 Mysteel 矿工群提取价格
    miner_file = os.path.join(CHAT_BASE, "mysteel-miner", "2026_04.md")
    if os.path.exists(miner_file):
        records = extract_from_chat(miner_file)
        for r in records:
            r["group"] = "Mysteel矿工群"
        all_records.extend(records)

    # 从 Mysteel SVIP 群提取
    svip_file = os.path.join(CHAT_BASE, "mysteel-svip", "2026_04.md")
    if os.path.exists(svip_file):
        records = extract_from_chat(svip_file)
        for r in records:
            r["group"] = "Mysteel SVIP群"
        all_records.extend(records)

    # 从图片摘要提取
    for group in ["Mysteel-铁矿石矿工群（正式）", "Mysteel铁矿石资讯SVIP正式2群",
                   "【VIP】建龙北京", "中国矿产市场报告联系人群", "建龙集团市场分析交流群"]:
        records = extract_from_images(group)
        for r in records:
            r["group"] = group
        all_records.extend(records)

    # 按时间排序
    all_records.sort(key=lambda x: x.get("datetime", ""))

    lines = []
    lines.append("# 2026年4月 铁矿石价格数据提取")
    lines.append("")
    lines.append(f"**提取日期**: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"**数据范围**: 2026-04-01 ~ 2026-04-27")
    lines.append(f"**总记录数**: {len(all_records)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 一、实时报盘数据
    price_records = [r for r in all_records if r.get("type") == "报盘"]
    if price_records:
        lines.append("## 一、实时报盘数据")
        lines.append("")
        lines.append("| 日期 | 时间 | 港口 | 品种 | 价格(元) | 涨跌 | 前一日 |")
        lines.append("|------|------|------|------|---------|------|--------|")

        for r in price_records:
            dt = r["datetime"]
            date = dt[:10]
            time = dt[11:]
            prev = str(r.get("prev_price", "")) if r.get("prev_price") else ""
            lines.append(f"| {date} | {time} | {r['port']} | {r['product']} | {r['price']} | {r.get('change', '')} | {prev} |")

        lines.append("")

    # 二、实时成交数据
    deal_records = [r for r in all_records if r.get("type") == "成交"]
    if deal_records:
        lines.append("## 二、实时成交数据")
        lines.append("")
        lines.append("| 日期 | 时间 | 港口 | 品种 | 价格(元) | 类型 |")
        lines.append("|------|------|------|------|---------|------|")

        for r in deal_records:
            dt = r["datetime"]
            date = dt[:10]
            time = dt[11:]
            lines.append(f"| {date} | {time} | {r['port']} | {r['product']} | {r['price']} | {r.get('change', '')} |")

        lines.append("")

    # 三、按品种汇总
    lines.append("## 三、按品种价格汇总")
    lines.append("")

    product_groups = defaultdict(list)
    for r in price_records:
        # 简化品种名
        product = r['product']
        if 'PB粉' in product:
            key = 'PB粉'
        elif '麦克粉' in product:
            key = '麦克粉'
        elif '卡粉' in product:
            key = '卡粉'
        elif '超特粉' in product:
            key = '超特粉'
        elif '混合粉' in product:
            key = '混合粉'
        elif 'PB块' in product:
            key = 'PB块'
        else:
            key = product
        product_groups[key].append(r)

    for product in sorted(product_groups.keys()):
        records = product_groups[product]
        records.sort(key=lambda x: x.get("datetime", ""))

        lines.append(f"### {product}")
        lines.append("")

        # 统计
        prices = [r['price'] for r in records]
        if prices:
            lines.append(f"- 记录数: {len(records)}")
            lines.append(f"- 最高价: {max(prices)} 元")
            lines.append(f"- 最低价: {min(prices)} 元")
            lines.append(f"- 均价: {sum(prices)/len(prices):.1f} 元")
            lines.append("")

            # 最新5条
            lines.append("| 日期 | 港口 | 价格 | 涨跌 |")
            lines.append("|------|------|------|------|")
            for r in records[-5:]:
                dt = r["datetime"]
                lines.append(f"| {dt[:10]} {dt[11:]} | {r['port']} | {r['price']} | {r.get('change', '')} |")
            lines.append("")

    # 四、港口价格对比
    lines.append("## 四、港口价格对比（最新）")
    lines.append("")

    # 取每种品种各港口的最新价格
    latest_by_product_port = {}
    for r in price_records:
        product = r['product']
        if 'PB粉' in product:
            product_key = 'PB粉'
        elif '麦克粉' in product:
            product_key = '麦克粉'
        elif '卡粉' in product:
            product_key = '卡粉'
        elif '超特粉' in product:
            product_key = '超特粉'
        elif 'PB块' in product:
            product_key = 'PB块'
        else:
            product_key = product

        port = r['port']
        key = (product_key, port)
        if key not in latest_by_product_port or r['datetime'] > latest_by_product_port[key]['datetime']:
            latest_by_product_port[key] = r

    if latest_by_product_port:
        lines.append("| 品种 | 港口 | 最新价格 | 日期 |")
        lines.append("|------|------|---------|------|")
        for (product, port), r in sorted(latest_by_product_port.items()):
            dt = r['datetime']
            lines.append(f"| {product} | {port} | {r['price']} | {dt[:10]} |")
        lines.append("")

    # 五、4月图片数据摘要
    lines.append("## 五、4月图片数据摘要")
    lines.append("")

    for group in ["【VIP】建龙北京", "中国矿产市场报告联系人群", "Mysteel-铁矿石矿工群（正式）"]:
        summary_file = os.path.join(IMAGE_BASE, group, "_image_summary.json")
        if not os.path.exists(summary_file):
            continue

        with open(summary_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        april_images = [(p, s) for p, s in data.items() if p.startswith("2026_04")]
        if not april_images:
            continue

        lines.append(f"### {group} ({len(april_images)}张)")
        lines.append("")
        for path, summary in april_images:
            lines.append(f"- **{path}**: {summary}")
        lines.append("")

    # 写入
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"报告已生成: {OUTPUT_FILE}")
    print(f"  报盘记录: {len(price_records)}")
    print(f"  成交记录: {len(deal_records)}")
    print(f"  图片记录: {len([r for r in all_records if r.get('type') == '图片'])}")


if __name__ == "__main__":
    generate_md_report()
