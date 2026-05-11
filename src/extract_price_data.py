"""从聊天记录中提取价格/库存/产量等结构化数据
- 解析实时报盘、实时成交、库存报告等消息
- 输出为 Markdown 表格
- 支持按月份提取，默认当前月
"""

import re
import glob
import os
import sys
import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime

CHAT_BASE = "D:/Wechat_File/Wechat_ChatHistory"
IMAGE_BASE = "D:/Wechat_File/Wechat_Image"

# 默认提取当前月份，可通过命令行参数覆盖
DEFAULT_MONTH = datetime.now().strftime("%Y_%m")

# 实时报盘正则
# 格式: 实时报盘: 港口 品种 价格 涨跌 （前一日行情 前值）
# 品种泛化匹配：港口和价格之间的非空白字符序列
PRICE_PATTERN = re.compile(
    r'实时报盘:\s*'
    r'(\S+)\s+'
    r'(\S+)\s+'
    r'(\d+)'
    r'(?:\s+(涨\d+|跌\d+|平))?'
    r'\s*(?:（前一日行情\s*(\d+)）)?'
)

# 成交正则
# 格式: [玫瑰]实时成交【n】: 港口 品种 价格 涨跌 [盘中/清底] （前一日行情 前值）
DEAL_PATTERN = re.compile(
    r'(?:\[玫瑰\])?实时成交【\d+】:\s*'
    r'(\S+)\s+'
    r'(\S+)\s+'
    r'(\d+)'
    r'(?:\s+(涨\d+|跌\d+|平))?'
    r'\s*(?:盘中|清底)?'
    r'\s*(?:（前一日行情\s*(\d+)）)?'
)

# 情绪/日报正则
DAILY_PRICE_PATTERN = re.compile(
    r'(\d{2}:\d{2})\s*【我的钢铁】\s*'
    r'.*?'
    r'(进口矿价格|日报|价格)'
)


# 品种名映射：将具体品种归类到标准名称
PRODUCT_KEYWORDS = {
    'PB粉': ['PB粉'],
    'PB块': ['PB块'],
    '麦克粉': ['麦克粉'],
    '卡粉': ['卡粉', '特卡粉'],
    '超特粉': ['超特粉'],
    '混合粉': ['混合粉', '低铝印粉'],
    '金布巴粉': ['金布巴粉', '金宝粉'],
    '纽曼粉': ['纽曼粉', '纽曼筛后粉'],
    '巴西精粉': ['巴西精粉', '巴精'],
    '巴西粉': ['巴西粉', '巴粉', '巴混', '高硅巴粉', '高硅巴粗'],
    'SP10粉': ['SP10粉'],
    'SP10块': ['SP10块'],
    'IOC6': ['IOC6'],
    '智利精粉': ['智利精粉'],
    '乌克兰精粉': ['乌克兰精粉'],
    '印度粉': ['印度粉'],
    '高硅印度粉': ['高硅印度粉'],
    '塞拉利昂粉': ['塞拉利昂粉'],
    '托克粉': ['托克粉'],
    'FMG筛后块': ['FMG筛后块'],
    '巴西筛后块': ['巴西筛后块'],
    '镍矿': ['镍矿'],
}


def normalize_product(product):
    """将具体品种名归一化为标准名称"""
    for key, keywords in PRODUCT_KEYWORDS.items():
        for kw in keywords:
            if kw in product:
                return key
    return product


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
        port, product, price, change, prev = m.groups()
        return {
            "type": "成交",
            "port": port,
            "product": product.strip(),
            "price": int(price),
            "change": change or "",
            "prev_price": int(prev) if prev else None,
        }
    return None


def extract_from_chat(filepath):
    """从聊天记录提取所有价格数据"""
    text = Path(filepath).read_text(encoding="utf-8")
    lines = text.split("\n")

    records = []
    last_datetime = None
    for line in lines:
        stripped = line.strip()

        # 普通消息: - [2026-05-01 12:00] ...
        time_match = re.match(r"- \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]", stripped)
        if time_match:
            last_datetime = time_match.group(1)

        # 回复消息: ↳ 回复 xxx: HH:MM ...
        reply_time_match = re.match(r"↳ 回复 \S+: (\d{2}:\d{2})", stripped)
        if reply_time_match and last_datetime:
            time_only = reply_time_match.group(1)
            date_part = last_datetime[:10]
            last_datetime = f"{date_part} {time_only}"

        if not stripped.startswith("- [") and not stripped.startswith("↳ 回复"):
            continue

        if not last_datetime:
            continue

        # 提取价格数据
        data = parse_price_line(stripped)
        if data:
            data["datetime"] = last_datetime
            records.append(data)

    return records


def extract_from_images(group_name, month_label):
    """从图片摘要提取指定月份数据"""
    summary_file = os.path.join(IMAGE_BASE, group_name, "_image_summary.json")
    if not os.path.exists(summary_file):
        return []

    with open(summary_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = []
    for path, summary in data.items():
        if not path.startswith(month_label):
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


def generate_md_report(month_label=None):
    """生成 Markdown 报告
    Args:
        month_label: 月份标签，如 "2026_05"，默认当前月
    """
    month_label = month_label or DEFAULT_MONTH
    year, month = month_label.split("_")
    output_file = f"D:/Wechat_File/Wechat_Image/_price_data_{month_label}.md"

    all_records = []

    # 从 Mysteel 矿工群提取价格
    miner_file = os.path.join(CHAT_BASE, "mysteel-miner", f"{month_label}.md")
    if os.path.exists(miner_file):
        records = extract_from_chat(miner_file)
        for r in records:
            r["group"] = "Mysteel矿工群"
        all_records.extend(records)

    # 从 Mysteel SVIP 群提取
    svip_file = os.path.join(CHAT_BASE, "mysteel-svip", f"{month_label}.md")
    if os.path.exists(svip_file):
        records = extract_from_chat(svip_file)
        for r in records:
            r["group"] = "Mysteel SVIP群"
        all_records.extend(records)

    # 从图片摘要提取
    for group in ["Mysteel-铁矿石矿工群（正式）", "Mysteel铁矿石资讯SVIP正式2群",
                   "【VIP】建龙北京", "中国矿产市场报告联系人群", "建龙集团市场分析交流群"]:
        records = extract_from_images(group, month_label)
        for r in records:
            r["group"] = group
        all_records.extend(records)

    # 按时间排序
    all_records.sort(key=lambda x: x.get("datetime", ""))

    # 计算数据范围
    dates = [r["datetime"][:10] for r in all_records if r.get("datetime")]
    date_range = f"{min(dates)} ~ {max(dates)}" if dates else "N/A"

    lines = []
    lines.append(f"# {year}年{int(month)}月 铁矿石价格数据提取")
    lines.append("")
    lines.append(f"**提取日期**: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"**数据范围**: {date_range}")
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
        key = normalize_product(r['product'])
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

    latest_by_product_port = {}
    for r in price_records:
        product_key = normalize_product(r['product'])
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

    # 五、图片数据摘要
    lines.append(f"## 五、{int(month)}月图片数据摘要")
    lines.append("")

    for group in ["【VIP】建龙北京", "中国矿产市场报告联系人群", "Mysteel-铁矿石矿工群（正式）"]:
        summary_file = os.path.join(IMAGE_BASE, group, "_image_summary.json")
        if not os.path.exists(summary_file):
            continue

        with open(summary_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        month_images = [(p, s) for p, s in data.items() if p.startswith(month_label)]
        if not month_images:
            continue

        lines.append(f"### {group} ({len(month_images)}张)")
        lines.append("")
        for path, summary in month_images:
            lines.append(f"- **{path}**: {summary}")
        lines.append("")

    # 写入
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"报告已生成: {output_file}")
    print(f"  报盘记录: {len(price_records)}")
    print(f"  成交记录: {len(deal_records)}")
    print(f"  图片记录: {len([r for r in all_records if r.get('type') == '图片'])}")

    return output_file


if __name__ == "__main__":
    month = sys.argv[1] if len(sys.argv) > 1 else None
    generate_md_report(month)
