# WeChat Chat History — handoff

> v3.3 | 给下一个 Agent / 下一台设备快速接手用

---

## 🟢 常驻层（半永久设施信息）

### 核心 pipeline

| 模块 | 脚本 | 说明 |
|------|------|------|
| 聊天导出 | `src/export_chats.py` | wechat-cli → 按月 Markdown，支持 `--refresh` |
| 飞书PDF下载 | `src/cdp_download_real_pdf.js` | Playwright CDP，点击文件块→拦截API→下载实际PDF |
| 飞书文字提取 | `src/cdp_fetch_text.js` | Playwright CDP，193/193 已完成 |
| 飞书链接分类 | `src/extract_feishu_links.py` | 输出 `feishu_links.json`（224 PDF + 193 text） |
| 价格提取 | `src/extract_price_data.py` | 正则匹配报盘/成交，品种映射已优化 |
| 图片AI提取 | `src/image_data_extract.py` | Kimi API，暂停（余额不足） |
| 图片分类 | `src/image_filter.py` | 1515张有效图片，10类别 |
| 月度报告 | `src/monthly_report.py` | 硬编码 month 参数 |
| 文件整理 | `src/organize_files.py` | 按月份移动到 `D:\SyncThing\PortNews\` |
| **PortNews分析** | `src/analyze_portnews.py` | DeepSeek-v4-pro，每日增量+月度报告，输出到 `D:\SyncThing\PortNews\analysis\` |

### API 配置

| API | 用途 | 模型 | 状态 |
|-----|------|------|------|
| DeepSeek | PortNews分析 | deepseek-v4-pro | 正常 |
| Kimi | 图片AI提取 | - | 余额不足，暂停 |

API key 环境变量: `DEEPSEEK_API_KEY`（DeepSeek）

### 定时任务

| 任务 | 频率 | 脚本 |
|------|------|------|
| 每日增量分析 | 每天 22:07 | `scripts/daily_portnews_analysis.sh` |
| 月度综合报告 | 每月28-31日 23:30 | `src/analyze_portnews.py --month` |

### 关键配置

| 项目 | 值 |
|------|-----|
| 群聊配置 | `config/groups.yaml`（6个群，含 port-news-t3） |
| Playwright profile | `data/browser_profile/`（含飞书登录态，勿删） |
| 下载进度 | `data/pdf_download_progress.json`（按页面追踪） |

### 数据位置

```
D:\SyncThing\PortNews\
├── 2026-01/  (47 PortNews + 92 研报)
├── 2026-02/  (37 PortNews + 94 研报)
├── 2026-03/  (49 PortNews + 99 研报)
├── 2026-04/  (47 PortNews + 94 研报)
├── 2026-05/  (13 PortNews + 27 研报)
├── analysis/           ← PortNews 综合分析输出
│   ├── 2026-01/_daily/ + _structured.json + _monthly_summary.md
│   ├── 2026-02/ ...
│   ├── 2026-03/ ...
│   ├── 2026-04/ ...
│   └── 2026-05/ ...
├── wechat_cached/  (42 files)
└── 未知月份/  (2 files)
```

### 验证命令

```bash
cd D:/ClaudeCode/wechat-chat-history
git status && git log --oneline -3
ls D:/SyncThing/PortNews/analysis/
```

---

## 🟡 任务层（当前接力状态）

### 当前目标

PortNews 综合分析已完成 1-5 月历史数据，每日增量分析已自动化。待 Kimi 余额恢复后继续图片提取。

### 最近完成

1. **PortNews 综合分析 pipeline** — DeepSeek-v4-pro，每日增量+月度报告
2. **1-5 月历史分析完成** — 183/193 文件成功（95%），5份月度报告
3. **每日/月度定时任务** — 22:07 增量 + 月底综合报告
4. **输出迁移** — 从 `data/portnews_structured/` 迁至 `D:\SyncThing\PortNews\analysis\`

### 下一步

1. **Kimi 余额恢复后重试图片提取** — 1257/1515 限流待重试
2. **重试 ~11 个失败分析文件** — parse_error 类型，可重新跑
3. **重试 21 个超时PDF** — 可用更长 timeout（120s）

### 阻塞点

- Kimi API 余额不足，图片 AI 提取暂停

### 当前工作区

- 分支：master
- 最近提交：`af12eb4 [CHECKPOINT] 2026-05-12 wechat-chat-history: v3.2 handoff format`
- 与远程同步：已 push
- 未提交改动：.gitignore + src/analyze_portnews.py + scripts/ + data/portnews_structured/
