#!/bin/bash
# PortNews 每日增量分析（只提取当天新文件）
# 每天执行，月底由 monthly_portnews_analysis.sh 跑全月报告

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

TODAY=$(date +%Y-%m-%d)

echo "=== PortNews 每日增量: $TODAY ==="
echo "启动时间: $(date '+%Y-%m-%d %H:%M:%S')"

PYTHONIOENCODING=utf-8 python src/analyze_portnews.py --date "$TODAY"

echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=== 完成 ==="
