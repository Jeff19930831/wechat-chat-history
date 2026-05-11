"""用 Kimi 对典型图片进行深度结构化数据提取
- 从每个群聊每个类别选取最新图片
- 用 Kimi k2.6 多模态模型分析图片内容
- 提取结构化数据：类型、日期、关键数值、来源、结论
"""

import json
import glob
import os
import sys
import time
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from collections import defaultdict

KIMI_CLI = os.path.expanduser("~/.local/bin/kimi")
MODEL = "kimi-code/kimi-for-coding"
TEMP_DIR = "D:/ClaudeCode/kimi_temp"
IMAGE_BASE = "D:/Wechat_File/Wechat_Image"
MAX_WORKERS = 4  # Kimi 并行数（降低避免 429）

# 每个类别每群选取的数量（0 = 不限）
SAMPLES_PER_CATEGORY = 0

# API 调用间隔（秒），防止 429
API_DELAY = 5

EXTRACT_PROMPT = """请仔细分析这张钢铁行业数据图片，提取以下结构化信息：

1. **报告类型**: 这是什么类型的报告？（价格/库存/产量/到港/利润/情绪/成交/其他）
2. **日期**: 报告对应的日期（YYYY-MM-DD格式）
3. **数据来源**: 数据来自哪家机构？（Mysteel/华泰期货/建龙集团/中矿智库/其他）
4. **关键数据**: 列出图片中的核心数值数据（格式：指标名=数值 单位）
5. **核心结论**: 用一句话概括图片传达的主要信息

请以 JSON 格式输出，不要包含其他解释文字：
{
  "type": "...",
  "date": "...",
  "source": "...",
  "key_data": [
    {"indicator": "...", "value": "...", "unit": "..."}
  ],
  "conclusion": "..."
}"""


def parse_date_from_path(path):
    """从路径解析日期"""
    try:
        month_part = path.split('\\')[0]
        return datetime.strptime(month_part, '%Y_%m')
    except:
        return datetime(2000, 1, 1)


def get_typical_images():
    """从过滤后的摘要中选取典型图片"""
    typical = defaultdict(lambda: defaultdict(list))

    for summary_file in glob.glob(f"{IMAGE_BASE}/*/_image_filtered.json"):
        group = os.path.basename(os.path.dirname(summary_file))
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for path, info in data.items():
            cat = info["category"]
            dt = parse_date_from_path(path)
            typical[group][cat].append((dt, path, info["summary"]))

    # 每类每群取最新的 N 张（0 = 全部）
    result = []
    for group in sorted(typical.keys()):
        for cat in sorted(typical[group].keys()):
            items = sorted(typical[group][cat], key=lambda x: x[0], reverse=True)
            if SAMPLES_PER_CATEGORY > 0:
                items = items[:SAMPLES_PER_CATEGORY]
            for dt, path, summary in items:
                result.append({
                    "group": group,
                    "category": cat,
                    "path": path,
                    "summary": summary,
                })

    return result


def extract_image_data(task):
    """用 Kimi 分析单张图片"""
    idx = task["idx"]
    group = task["group"]
    cat = task["category"]
    rel_path = task["path"]
    summary = task["summary"]

    # 构建完整图片路径
    img_path = os.path.join(IMAGE_BASE, group, rel_path.replace('\\', '/'))
    if not os.path.exists(img_path):
        return {
            "group": group, "category": cat, "path": rel_path,
            "status": "error", "error": "图片不存在",
        }

    # 复制到临时目录（避免中文路径问题）
    tmp_path = os.path.join(TEMP_DIR, f"extract_{idx}.jpg")
    try:
        shutil.copy2(img_path, tmp_path)
    except Exception as e:
        return {
            "group": group, "category": cat, "path": rel_path,
            "status": "error", "error": f"复制失败: {e}",
        }

    # 调用 Kimi
    prompt = EXTRACT_PROMPT + f"\n\n图片摘要参考: {summary}"
    try:
        result = subprocess.run(
            [KIMI_CLI, "-m", MODEL, "--quiet", "-p", prompt],
            capture_output=True, text=True, encoding="utf-8",
            timeout=180, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        output = result.stdout.strip()

        if "429" in output or "reached" in output.lower():
            return {
                "group": group, "category": cat, "path": rel_path,
                "status": "rate_limited", "error": "Kimi API 限流",
            }

        # 尝试解析 JSON
        try:
            # 找到 JSON 部分
            start = output.find('{')
            end = output.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(output[start:end])
            else:
                data = {"raw": output}
        except json.JSONDecodeError:
            data = {"raw": output}

        return {
            "group": group, "category": cat, "path": rel_path,
            "status": "success", "data": data,
        }

    except subprocess.TimeoutExpired:
        return {
            "group": group, "category": cat, "path": rel_path,
            "status": "timeout", "error": "超时",
        }
    except Exception as e:
        return {
            "group": group, "category": cat, "path": rel_path,
            "status": "error", "error": str(e),
        }


def main():
    os.makedirs(TEMP_DIR, exist_ok=True)

    output_file = "D:/Wechat_File/Wechat_Image/_image_data_extracted.json"

    # 断点续传：加载已有结果
    existing = {}
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            old = json.load(f)
        for r in old.get("results", []):
            existing[r["path"]] = r
        print(f"已有 {len(existing)} 条历史结果，将跳过")

    typical = get_typical_images()
    total = len(typical)
    print(f"=" * 60)
    print(f"Kimi 图片深度数据提取")
    print(f"待提取图片数: {total}")
    print(f"API 间隔: {API_DELAY}s")
    print(f"=" * 60)

    # 跳过已处理的
    tasks = []
    for i, t in enumerate(typical):
        if t["path"] in existing:
            continue
        tasks.append({"idx": i, **t})

    skipped = total - len(tasks)
    print(f"跳过已处理: {skipped}")
    print(f"待处理: {len(tasks)}")

    # 合并已有结果
    results = list(existing.values())
    success = sum(1 for r in results if r.get("status") == "success")
    failed = sum(1 for r in results if r.get("status") == "error")
    rate_limited = sum(1 for r in results if r.get("status") == "rate_limited")

    # 串行执行
    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] {task['group']} | {task['category']}")
        print(f"  图片: {task['path']}")
        print(f"  摘要: {task['summary'][:50]}...")

        result = extract_image_data(task)
        results.append(result)

        if result["status"] == "success":
            success += 1
            data = result.get("data", {})
            print(f"  类型: {data.get('type', 'N/A')}")
            print(f"  来源: {data.get('source', 'N/A')}")
            print(f"  日期: {data.get('date', 'N/A')}")
        elif result["status"] == "rate_limited":
            rate_limited += 1
            print(f"  状态: ⚠️ 限流，等待 60s...")
            time.sleep(60)
        else:
            failed += 1
            print(f"  状态: ❌ {result.get('error', '未知错误')}")

        # 每次处理后保存（断点续传）
        if i % 10 == 0 or i == len(tasks):
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "meta": {
                        "total": total,
                        "processed": skipped + i,
                        "success": success,
                        "failed": failed,
                        "rate_limited": rate_limited,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                    "results": results,
                }, f, ensure_ascii=False, indent=2)
            print(f"  [已保存进度 {skipped + i}/{total}]")

        # API 间隔
        if i < len(tasks):
            time.sleep(API_DELAY)

    # 最终保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "meta": {
                "total": total,
                "processed": total,
                "success": success,
                "failed": failed,
                "rate_limited": rate_limited,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "results": results,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"提取完成!")
    print(f"  成功: {success}")
    print(f"  限流: {rate_limited}")
    print(f"  失败: {failed}")
    print(f"  输出: {output_file}")


if __name__ == "__main__":
    main()
