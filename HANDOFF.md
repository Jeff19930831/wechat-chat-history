# WeChat Chat History — 当前交接

> 给下一个 Agent / 下一台设备快速接手用。保持短、准、最新。

## 当前目标

wechat-chat-history 项目已进入**运行中**状态。核心 pipeline 全部开发完成，本轮重点是完成图片 AI 分析 pipeline 和结构化数据提取。

## 最近完成

1. **聊天记录导出** — 5 群 × 4 个月 = 20 个 Markdown 文件
2. **关键词/活跃度分析** — `_keyword_stats.json` + `_member_activity.json`
3. **图片过滤分类** — 1515 张有效图片，去除 17 张无用图，按 10 类别分类
4. **Kimi 深度提取** — 28 张典型图片，22 张成功提取结构化数据
5. **分类整理** — 1515 张图片复制到 `Wechat_Image_Categorized/`
6. **月度报告** — `_monthly_report_2026_04.md`（5 群统计）
7. **价格数据提取** — `_price_data_2026_04.md`（276 条报盘记录，7 品种汇总）
8. **文档更新** — README.md / PROGRESS.md / HANDOFF.md 全部更新

## 下一步

1. **Git push** — 将最新代码 push 到 GitHub（上次 push 因 SSL 失败）
2. **价格数据集成** — 考虑将 `_price_data_YYYY_MM.md` 推送到飞书或邮件
3. **正则优化** — `extract_price_data.py` 的 PRICE_PATTERN 和 DEAL_PATTERN 可能需要扩展以覆盖更多品种格式
4. **图片提取扩展** — 当前仅提取 28 张典型图片，可考虑扩展到全部 1515 张
5. **下月数据** — 5 月初运行 export_chats.py 增量导出 2026-05 数据

## 阻塞点

- **Git push SSL 错误**：上次 push 失败，可能需要检查网络或 GitHub token
- **Kimi 429 限流**：image_data_extract.py 高并发时触发 API 限流，已降低 MAX_WORKERS=4

## 关键文件

| 文件 | 作用 | 注意事项 |
|------|------|----------|
| `src/extract_price_data.py` | 价格数据提取 | 正则需持续优化匹配更多品种 |
| `src/image_data_extract.py` | Kimi 图片深度提取 | SAMPLES_PER_CATEGORY=1，避免 429 |
| `src/monthly_report.py` | 月度统计报告 | 硬编码 month="2026_04"，下月需改 |
| `config/groups.yaml` | 群聊配置 | since 日期控制导出范围 |
| `README.md` | 项目总览 | 功能变化时同步 |
| `PROGRESS.md` | 进展记录 | 每轮工作结束更新 |

## 验证命令

```bash
# 价格数据提取
cd D:/ClaudeCode/wechat-chat-history/src
python extract_price_data.py

# 月度报告
cd D:/ClaudeCode/wechat-chat-history/src
python monthly_report.py

# Git 状态
cd D:/ClaudeCode/wechat-chat-history
git status
git log --oneline -5
```

## 当前工作区

- 分支：main
- 最近提交：（待确认，上次 push 失败）
- 未提交改动：README.md、PROGRESS.md、HANDOFF.md、全部 src/*.py
