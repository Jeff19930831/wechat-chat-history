"""按数据类型对图片进行分类整理
- 读取 _image_filtered.json
- 将图片按类别复制到新的分类目录
- 输出分类统计报告
"""

import json
import glob
import os
import shutil
from collections import Counter, defaultdict
from pathlib import Path

IMAGE_BASE = "D:/Wechat_File/Wechat_Image"
OUTPUT_BASE = "D:/Wechat_File/Wechat_Image_Categorized"


def main():
    os.makedirs(OUTPUT_BASE, exist_ok=True)

    # 收集所有过滤后的图片
    all_images = []
    for summary_file in glob.glob(f"{IMAGE_BASE}/*/_image_filtered.json"):
        group = os.path.basename(os.path.dirname(summary_file))
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for rel_path, info in data.items():
            all_images.append({
                "group": group,
                "path": rel_path,
                "category": info["category"],
                "summary": info["summary"],
            })

    print(f"=" * 60)
    print(f"图片分类整理")
    print(f"=" * 60)
    print(f"总图片数: {len(all_images)}")

    # 按类别统计
    cats = Counter(img["category"] for img in all_images)
    print(f"\n分类统计:")
    for cat, count in cats.most_common():
        print(f"  {cat}: {count}")

    # 复制图片到分类目录
    total = len(all_images)
    copied = 0
    skipped = 0
    errors = 0

    print(f"\n开始整理...")
    for i, img in enumerate(all_images, 1):
        group = img["group"]
        cat = img["category"]
        rel_path = img["path"]

        # 源文件路径
        src = os.path.join(IMAGE_BASE, group, rel_path)
        if not os.path.exists(src):
            print(f"  文件不存在: {src}")
            errors += 1
            continue

        # 目标路径: 分类/群聊/年月/文件名
        month_dir = os.path.dirname(rel_path)
        filename = os.path.basename(rel_path)
        dst_dir = os.path.join(OUTPUT_BASE, cat, group, month_dir)
        dst = os.path.join(dst_dir, filename)

        os.makedirs(dst_dir, exist_ok=True)

        if os.path.exists(dst):
            skipped += 1
            continue

        try:
            shutil.copy2(src, dst)
            copied += 1
        except Exception as e:
            print(f"  复制失败 {src}: {e}")
            errors += 1

        if i % 100 == 0:
            print(f"  进度: {i}/{total} ({copied} 已复制)")

    print(f"\n{'=' * 60}")
    print(f"整理完成!")
    print(f"  已复制: {copied}")
    print(f"  已跳过: {skipped}")
    print(f"  错误: {errors}")
    print(f"  输出: {OUTPUT_BASE}")


if __name__ == "__main__":
    main()
