"""微信群成员活跃度分析
- 读取已导出的 Markdown 聊天记录
- 统计每个成员的发言次数、活跃时间段
- 输出 JSON 报告
"""

import os
import json
import re
import glob
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

# Markdown 导出格式中的消息行正则
# 格式: **发送者** [时间]: 消息内容
# 或: [时间] **发送者**: 消息内容
MSG_RE = re.compile(
    r"(?:\*\*(.+?)\*\*\s*\[(.+?)\]|\[(.+?)\]\s*\*\*(.+?)\*\*)\s*:\s*(.+)",
    re.MULTILINE,
)
# 备选格式
ALT_RE = re.compile(r"\[(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[^\]]*)\]\s*\*\*(.+?)\*\*\s*:\s*(.+)", re.MULTILINE)


def parse_sender_and_time(line):
    """从消息行解析发送者和时间
    格式: - [YYYY-MM-DD HH:MM] 发送者: 内容
    """
    m = re.match(r"- \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\] (.+?): (.+)", line)
    if m:
        return m.group(2).strip(), m.group(1).strip(), m.group(3).strip()

    return None, None, None


def analyze_group(group_dir):
    """分析一个群聊的成员活跃度"""
    md_files = sorted(glob.glob(os.path.join(group_dir, "*.md")))
    if not md_files:
        return None

    sender_counts = Counter()
    sender_words = defaultdict(int)
    hourly_activity = Counter()
    monthly_senders = defaultdict(lambda: Counter())

    for f in md_files:
        month = Path(f).stem
        text = Path(f).read_text(encoding="utf-8")

        for line in text.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            sender, time_str, content = parse_sender_and_time(line)
            if not sender:
                continue

            sender_counts[sender] += 1
            sender_words[sender] += len(content)
            monthly_senders[month][sender] += 1

            # 统计小时活跃度
            try:
                dt = datetime.strptime(time_str[:19], "%Y-%m-%d %H:%M:%S")
                hourly_activity[dt.hour] += 1
            except ValueError:
                pass

    if not sender_counts:
        return None

    total_messages = sum(sender_counts.values())

    return {
        "total_messages": total_messages,
        "unique_members": len(sender_counts),
        "top_senders": [
            {
                "name": name,
                "messages": count,
                "words": sender_words[name],
                "percentage": round(count / total_messages * 100, 2),
            }
            for name, count in sender_counts.most_common(30)
        ],
        "hourly_distribution": {
            str(h): hourly_activity.get(h, 0)
            for h in range(24)
        },
        "monthly_top_senders": {
            month: [
                {"name": name, "messages": count}
                for name, count in counter.most_common(5)
            ]
            for month, counter in sorted(monthly_senders.items())
        },
    }


def main():
    import yaml

    with open(Path(__file__).parent.parent / "config" / "groups.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    output_base = Path(config.get("export", {}).get("output_base", "D:/Wechat_File/Wechat_ChatHistory"))
    report_file = output_base / "_member_activity.json"

    print(f"群成员活跃度分析")
    print(f"数据目录: {output_base}")
    print(f"=" * 50)

    all_reports = {}

    for group in config["groups"]:
        if not group.get("enabled", True):
            continue
        alias = group.get("alias", group["name"])
        group_dir = output_base / alias

        print(f"\n分析: {group['name']}")
        if not group_dir.exists():
            print(f"  目录不存在，跳过")
            continue

        report = analyze_group(group_dir)
        if report:
            all_reports[alias] = report
            print(f"  成员: {report['unique_members']}, 消息: {report['total_messages']}")
            top3 = ", ".join([f"{s['name']}({s['messages']})" for s in report['top_senders'][:3]])
            print(f"  Top 3: {top3}")
        else:
            print(f"  无数据")

    report_file.write_text(
        json.dumps(all_reports, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n报告已保存: {report_file}")


if __name__ == "__main__":
    main()
