# WeChat Chat History — handoff

> v3.2 两层格式 | 给下一个 Agent / 下一台设备快速接手用

---

## 🟢 常驻层（半永久设施信息）

### 核心pipeline

| 模块 | 脚本 | 说明 |
|------|------|------|
| 聊天导出 | `src/export_chats.py` | wechat-cli → 按月 Markdown，支持 `--refresh` |
| 飞书PDF下载 | `src/cdp_download_real_pdf.js` | Playwright CDP，点击文件块→拦截API→下载实际PDF |
| 飞书文字提取 | `src/cdp_fetch_text.js` | Playwright CDP，193/193 已完成 |
| 飞书链接分类 | `src/extract_feishu_links.py` | 输出 `feishu_links.json`（224 PDF + 193 text） |
| 价格提取 | `src/extract_price_data.py` | 正则匹配报盘/成交，品种映射已优化 |
| 图片AI提取 | `src/image_data_extract.py` | Kimi API，MAX_WORKERS=4，API_DELAY=5s |
| 图片分类 | `src/image_filter.py` | 1515张有效图片，10类别 |
| 月度报告 | `src/monthly_report.py` | 硬编码 month 参数 |
| 文件整理 | `src/organize_files.py` | 按月份移动到 `D:\SyncThing\PortNews\` |

### 运行中服务 / 后台任务

- **无持续运行服务**

### 关键配置

| 项目 | 值 |
|------|-----|
| 群聊配置 | `config/groups.yaml`（6个群，含 port-news-t3） |
| Playwright profile | `data/browser_profile/`（含飞书登录态，勿删） |
| 下载进度 | `data/pdf_download_progress.json`（按页面追踪） |

### 数据位置（已整理到 SyncThing）

```
D:\SyncThing\PortNews\
├── 2026-01/  (47 PortNews + 92 研报)
├── 2026-02/  (37 PortNews + 94 研报)
├── 2026-03/  (49 PortNews + 99 研报)
├── 2026-04/  (47 PortNews + 94 研报)
├── 2026-05/  (13 PortNews + 27 研报)
├── wechat_cached/  (42 files)
└── 未知月份/  (2 files)
```

### 验证命令

```bash
cd D:/ClaudeCode/wechat-chat-history
git status && git log --oneline -3
ls D:/SyncThing/PortNews/ | head
```

---

## 🟡 任务层（当前接力状态）

### 当前目标

数据采集阶段完成。待图片AI提取完成后，进入结构化分析与集成阶段。

### 最近完成

1. **飞书嵌入PDF下载** — 409个真实PDF（20GB），385成功/21超时
2. **飞书文字内容提取** — 193/193 markdown文件
3. **文件整理到SyncThing** — 按月份分文件夹，644个文件20GB
4. **垃圾数据清理** — 删除旧假PDF、废弃脚本、调试文件

### 下一步

1. **图片AI提取完成** — 检查后台任务状态，1515张Kimi提取
2. **价格数据集成** — 将结构化价格数据推送到飞书/邮件
3. **Port News T3综合分析** — 整合PDF研报、文字内容、价格数据
4. **重试21个超时PDF** — 可用更长timeout（120s）重试大文件

### 阻塞点

- 无

### 当前工作区

- 分支：master
- 最近提交：`f93dd80 feat: organize downloaded files to D:\SyncThing by month`
- 与远程同步：已 push
