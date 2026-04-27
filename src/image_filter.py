"""图片过滤与分类
- 根据摘要内容去除无用图片
- 对有效图片进行分类
- 输出 _image_filtered.json 和分类统计报告
"""

import json
import glob
import os
from collections import Counter, defaultdict
from pathlib import Path

# 无用关键词
USELESS_KEYWORDS = ['aqi', '空气质量', '财联社', 'wind', '万得', '电报']

def is_useful(summary):
    s_lower = summary.lower()
    if any(kw in s_lower for kw in USELESS_KEYWORDS):
        return False
    return True

def classify(summary):
    s = summary.lower()
    if '价格' in summary or '报价' in summary or '现货' in summary or 'pb粉' in s or '实时报盘' in summary:
        return '价格/报价'
    if '库存' in summary:
        return '库存'
    if '产量' in summary or '日均铁水' in summary or '开工率' in summary:
        return '产量/铁水'
    if '到港' in summary or '发运' in summary or '通关' in summary:
        return '到港/发运'
    if '基差' in summary or '价差' in summary:
        return '基差/价差'
    if '利润' in summary:
        return '利润'
    if '情绪' in summary or '心态' in summary:
        return '情绪/心态'
    if '成交' in summary:
        return '成交'
    if '废钢' in summary or '到货' in summary:
        return '废钢/到货'
    return '其他'

def main():
    base_dir = "D:/Wechat_File/Wechat_Image"
    all_summaries = []
    filtered_by_group = {}

    for summary_file in glob.glob(f"{base_dir}/*/_image_summary.json"):
        group = os.path.basename(os.path.dirname(summary_file))
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        useful = {}
        for path, summary in data.items():
            if is_useful(summary):
                useful[path] = {
                    "summary": summary,
                    "category": classify(summary),
                }
            all_summaries.append((group, path, summary))

        filtered_by_group[group] = useful

        # 保存过滤后的摘要
        out_file = os.path.join(os.path.dirname(summary_file), "_image_filtered.json")
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(useful, f, ensure_ascii=False, indent=2)

    # 统计报告
    total = len(all_summaries)
    useful_count = sum(len(v) for v in filtered_by_group.values())
    useless_count = total - useful_count

    print(f"=" * 60)
    print(f"图片过滤报告")
    print(f"=" * 60)
    print(f"总图片数: {total}")
    print(f"有效图片: {useful_count} ({useful_count/total*100:.1f}%)")
    print(f"去除图片: {useless_count} ({useless_count/total*100:.1f}%)")
    print(f"\n按群聊统计:")

    for group in sorted(filtered_by_group.keys()):
        data = filtered_by_group[group]
        cats = Counter(v["category"] for v in data.values())
        print(f"\n  {group}:")
        print(f"    有效: {len(data)} 张")
        for cat, count in cats.most_common():
            print(f"      {cat}: {count}")

    print(f"\n过滤结果已保存到各群目录的 _image_filtered.json")

if __name__ == "__main__":
    main()
