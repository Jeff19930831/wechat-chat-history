"""微信群聊关键词统计分析
- 读取已导出的 Markdown 聊天记录
- 统计高频词、热词趋势
- 输出 JSON 报告
"""

import os
import json
import re
import glob
from pathlib import Path
from collections import Counter
from datetime import datetime

# 停用词（中文常见无意义词汇）
STOPWORDS = set([
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也",
    "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
    "啊", "呢", "吧", "吗", "哦", "嗯", "哈", "哈哈", "嘿嘿", "呵呵",
])

# 正则：匹配中文字符和英文单词
WORD_RE = re.compile(r"[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}")


def extract_words(text):
    """从文本中提取有意义的词汇"""
    words = WORD_RE.findall(text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) >= 2]


def analyze_group(group_dir):
    """分析一个群聊的所有月份文件"""
    md_files = sorted(glob.glob(os.path.join(group_dir, "*.md")))
    if not md_files:
        return None

    all_words = []
    monthly_words = {}

    for f in md_files:
        month = Path(f).stem  # YYYY_MM
        text = Path(f).read_text(encoding="utf-8")
        words = extract_words(text)
        all_words.extend(words)
        monthly_words[month] = Counter(words)

    total_counter = Counter(all_words)

    return {
        "total_messages_approx": len(md_files) * 1000,  # 粗略估计
        "total_words": len(all_words),
        "unique_words": len(total_counter),
        "top_keywords": [
            {"word": w, "count": c}
            for w, c in total_counter.most_common(50)
        ],
        "monthly_trend": {
            month: [
                {"word": w, "count": c}
                for w, c in counter.most_common(10)
            ]
            for month, counter in sorted(monthly_words.items())
        },
    }


def main():
    import yaml

    with open(Path(__file__).parent.parent / "config" / "groups.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    output_base = Path(config.get("export", {}).get("output_base", "D:/Wechat_File/Wechat_ChatHistory"))
    report_file = output_base / "_keyword_stats.json"

    print(f"关键词统计分析")
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
            print(f"  总词汇: {report['total_words']}, 唯一词: {report['unique_words']}")
            top3 = ", ".join([f"{w['word']}({w['count']})" for w in report['top_keywords'][:3]])
            print(f"  Top 3: {top3}")
        else:
            print(f"  无数据文件")

    # 保存报告
    report_file.write_text(
        json.dumps(all_reports, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n报告已保存: {report_file}")


if __name__ == "__main__":
    main()
