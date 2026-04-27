"""批量导出微信群聊聊天记录
- 按群名/年_月.md 组织
- 支持增量导出（跳过已存在的月份）
- 调用 wechat-cli export 命令
"""

import os
import sys
import json
import re
import subprocess
import yaml
from datetime import datetime, timedelta
from pathlib import Path

# ---------- 配置 ----------
CONFIG_FILE = Path(__file__).parent.parent / "config" / "groups.yaml"
# --------------------------


def run_wechat_cli(args, timeout=300):
    """运行 wechat-cli 命令，返回 stdout"""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    cmd = ["wechat-cli"] + args
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8",
        timeout=timeout, env=env,
    )
    if result.returncode != 0:
        print(f"  Error: {result.stderr.strip()}")
        return None
    return result.stdout


def get_chat_stats(chat_name):
    """获取群聊统计信息，包括消息总数和时间范围"""
    output = run_wechat_cli(["stats", chat_name, "--format", "json"])
    if not output:
        return None
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return None


def get_month_range(start_date, end_date):
    """生成从 start_date 到 end_date 的每个月份范围"""
    months = []
    current = datetime(start_date.year, start_date.month, 1)
    end = datetime(end_date.year, end_date.month, 1)
    while current <= end:
        month_start = current
        if current.month == 12:
            next_month = datetime(current.year + 1, 1, 1)
        else:
            next_month = datetime(current.year, current.month + 1, 1)
        month_end = next_month - timedelta(days=1)
        months.append((
            current.strftime("%Y_%m"),
            month_start.strftime("%Y-%m-%d"),
            min(month_end, end_date).strftime("%Y-%m-%d"),
        ))
        current = next_month
    return months


def export_chat_month(chat_name, output_dir, month_label, start_time, end_time):
    """导出指定月份的聊天记录"""
    out_file = output_dir / f"{month_label}.md"
    if out_file.exists():
        print(f"    跳过 {month_label}（已存在）")
        return True

    print(f"    导出 {month_label} ({start_time} ~ {end_time})...", end=" ")

    output = run_wechat_cli([
        "export", chat_name,
        "--format", "markdown",
        "--start-time", start_time,
        "--end-time", end_time,
    ], timeout=600)

    if output is None:
        print("失败")
        return False

    # 检查是否有内容
    if len(output.strip()) < 50:
        print("无内容")
        return True  # 空月份不算失败

    out_file.write_text(output, encoding="utf-8")
    print(f"完成 ({len(output)} chars)")
    return True


def sanitize_folder_name(name):
    """清理文件夹名中的非法字符"""
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def main():
    # 读取配置
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    groups = [g for g in config["groups"] if g.get("enabled", True)]
    export_cfg = config.get("export", {})
    output_base = Path(export_cfg.get("output_base", "D:/Wechat_File/Wechat_ChatHistory"))
    incremental = export_cfg.get("incremental", True)

    print(f"=" * 60)
    print(f"微信群聊聊天记录批量导出")
    print(f"输出目录: {output_base}")
    print(f"目标群聊: {len(groups)} 个")
    print(f"=" * 60)

    total_exported = 0
    total_skipped = 0
    total_failed = 0

    for i, group in enumerate(groups, 1):
        name = group["name"]
        alias = group.get("alias", sanitize_folder_name(name))
        print(f"\n[{i}/{len(groups)}] {name}")

        # 获取统计信息
        stats = get_chat_stats(name)
        if not stats:
            print(f"  无法获取统计信息，跳过")
            total_failed += 1
            continue

        total_msgs = stats.get("total_messages", 0)
        print(f"  消息总数: {total_msgs}")

        # 获取时间范围
        # stats 可能包含 first_message_time 和 last_message_time
        # 如果没有，尝试从 history 获取最早消息
        first_time = stats.get("first_message_time")
        last_time = stats.get("last_message_time")

        if not first_time or not last_time:
            # 尝试获取最近一条消息的时间作为参考
            history = run_wechat_cli(["history", name, "--limit", "1", "--format", "json"])
            if history:
                try:
                    msgs = json.loads(history)
                    if msgs:
                        last_time = msgs[0].get("time", "")
                except Exception:
                    pass

        if not first_time:
            # 默认从 2023-08 开始（与图片数据一致）
            first_time = "2023-08-01"
        if not last_time:
            last_time = datetime.now().strftime("%Y-%m-%d")

        try:
            start_date = datetime.strptime(first_time[:10], "%Y-%m-%d")
            end_date = datetime.strptime(last_time[:10], "%Y-%m-%d")
        except ValueError:
            print(f"  时间解析失败，跳过")
            total_failed += 1
            continue

        # 创建输出目录
        group_dir = output_base / alias
        group_dir.mkdir(parents=True, exist_ok=True)

        # 按月导出
        months = get_month_range(start_date, end_date)
        for month_label, start_t, end_t in months:
            if incremental:
                out_file = group_dir / f"{month_label}.md"
                if out_file.exists():
                    total_skipped += 1
                    continue

            ok = export_chat_month(name, group_dir, month_label, start_t, end_t)
            if ok:
                total_exported += 1
            else:
                total_failed += 1

    print(f"\n{'=' * 60}")
    print(f"导出完成!")
    print(f"  成功: {total_exported} 个月份文件")
    print(f"  跳过: {total_skipped} 个（已存在）")
    print(f"  失败: {total_failed} 个")
    print(f"  输出: {output_base}")


if __name__ == "__main__":
    main()
