# WeChat Chat History — 进展记录

> 按时间倒序排列，最新的在最上面

---

## 2026-05-27 — PortNews 综合分析 pipeline

### 已完成
- [x] 开发 `src/analyze_portnews.py` — DeepSeek-v4-pro 综合分析
  - 每日增量提取（品种/价格信号/宏观事件/供应链/情绪 → JSON）
  - 评论主题提取（THE PORT 群聊，分块30条/次）
  - 月度综合报告生成（市场概览/宏观/品种/供应链/情绪/展望）
  - 幂等缓存（`_daily/` 目录），已提取文件跳过
- [x] 1-5 月历史数据全量分析 — 183/193 文件成功（95%），5份月度报告
- [x] 创建 `scripts/daily_portnews_analysis.sh` — 每日增量包装脚本
- [x] 定时任务配置 — 每天 22:07 增量 + 月底综合报告
- [x] 输出迁移至 `D:\SyncThing\PortNews\analysis\`

### 关键技术决策
- 从 GLM 5.1（余额不足429）切换到 DeepSeek-v4-pro
- 评论提取分块处理（30条/次）避免输出截断
- `extract_json_from_output()` 处理 DeepSeek 的 ```json``` 包装

### 已产出
- `D:\SyncThing\PortNews\analysis\2026-{01..05}\` — 5个月的分析数据
  - 每月：`_daily/*.json` + `_structured.json` + `_monthly_summary.md`

---

## 2026-05-12 — Port News T3 飞书文档下载 + Pipeline 优化

### 已完成
- [x] 修复 Git push SSL 问题 — 成功 push 到 GitHub
- [x] 增量导出 2026-05 聊天数据 — export_chats.py --refresh
- [x] 正则优化 extract_price_data.py — `[玫瑰]` 可选、回复行处理、品种映射
- [x] 新增 Port News T3 群配置 — config/groups.yaml
- [x] 飞书链接提取与分类 — extract_feishu_links.py（224 PDF + 193 text 链接）
- [x] 飞书文字内容提取 — cdp_fetch_text.js（193/193 成功，输出 markdown）
- [x] 飞书嵌入PDF下载 — cdp_download_real_pdf.js 全量完成
  - 409个真实PDF，20GB（224个页面，203页完成，385成功/21超时失败）
  - 清理旧的假PDF（page.pdf()打印页面，86MB）和废弃脚本
- [x] WeChat缓存PDF整理 — 42个PDF从 WeChat 文件缓存复制

### 关键技术发现
- 飞书 docx 页面内嵌入PDF文件：`data-block-type="file"` + `data-record-id`
- 点击文件块后拦截 `box/stream/download/preview/{token}` 获取真实PDF
- `page.pdf()` 只是打印网页为PDF，不是实际嵌入的PDF
- 需要用 Playwright CDP（非curl）因飞书需要登录

### 已产出
- `data/feishu_links.json` — 224 PDF + 193 text 链接分类
- `D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/pdf_real/` — 409个实际嵌入PDF（20GB）
- `D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/text/` — 193 个 markdown 文件
- `D:/Wechat_File/Wechat_ChatHistory/port-news-t3/pdf/` — 42 个 WeChat 缓存PDF

---

## 2026-04-27 — 图片分析与数据提取 pipeline 完成

### 已完成
- [x] 开发 `image_filter.py` — 图片过滤与分类
  - 去除 AQI、新闻等无用图片（17 张）
  - 按 10 个类别自动分类（价格、库存、产量、到港、利润、情绪、成交、基差、废钢、其他）
  - 输出 `_image_filtered.json`
- [x] 开发 `image_data_extract.py` — Kimi 深度数据提取
  - 从典型图片中提取结构化数据（类型、日期、来源、关键数据、结论）
  - 22/28 张成功提取，1 张限流，5 张超时
  - 输出 `_image_data_extracted.json`
- [x] 开发 `organize_by_category.py` — 图片分类整理
  - 将 1515 张有效图片按类别复制到独立目录
  - 类别名中的 `/` 替换为 `_` 避免嵌套目录
  - 输出到 `Wechat_Image_Categorized/`
- [x] 开发 `monthly_report.py` — 月度统计报告
  - 统计各群消息数、活跃成员、关键词 Top 10
  - 图片分类统计与典型摘要
  - 输出 `_monthly_report_2026_04.md`
- [x] 开发 `extract_price_data.py` — 实时价格数据提取
  - 正则匹配「实时报盘」格式：港口 + 品种 + 价格 + 涨跌 + 前一日行情
  - 正则匹配「实时成交」格式
  - 按品种汇总（最高价/最低价/均价/最新5条）
  - 港口价格对比（各品种各港口最新价）
  - 输出 `_price_data_2026_04.md`
- [x] 更新 README.md — 补充全部 8 个功能模块说明
- [x] 更新本 PROGRESS.md
- [x] 创建 HANDOFF.md

### 已产出
- `_image_filtered.json` × 5（每群一个，共 1515 张有效图片）
- `_image_data_extracted.json`（28 张典型图片的深度提取）
- `Wechat_Image_Categorized/`（10 个类别 × 5 群 × 多月份）
- `_monthly_report_2026_04.md`（5 群消息统计 + 图片分类）
- `_price_data_2026_04.md`（276 条报盘记录，7 个品种汇总）
- 20 个 Markdown 月份文件（`Wechat_ChatHistory/`）
- `_keyword_stats.json` — 5 群关键词统计
- `_member_activity.json` — 5 群成员活跃度分析

### 数据亮点（2026-04）
- 总消息数：1720 条（5 群）
- 总图片数：15 张（过滤后 1515 张历史图片）
- 实时报盘：276 条记录
- PB粉均价：781.2 元（范围 772~795）
- 麦克粉均价：776.1 元（范围 764~785）
- 超特粉均价：664.7 元（范围 653~685）

### 下一步
1. 将价格数据提取结果集成到飞书日报或单独推送
2. 优化正则匹配，覆盖更多品种格式（如巴西精粉、乌克兰精粉等）
3. 考虑将图片深度提取扩展到全部 1515 张（当前仅 28 张典型样本）
4. 根据用户反馈调整停用词和解析逻辑

---

## 2026-04-27 — 项目启动与核心功能开发

### 已完成
- [x] 项目立项，创建目录结构
- [x] 设计归档目录结构（群别名/年_月.md）
- [x] 开发 `export_chats.py` — 批量导出脚本
  - 按月分段导出
  - 支持增量导出（跳过已存在文件）
  - 自动探测群聊时间范围
- [x] 开发 `keyword_stats.py` — 关键词统计分析
  - Top 50 高频词
  - 月度热词趋势
- [x] 开发 `member_activity.py` — 成员活跃度分析
  - 发言量排名
  - 小时段分布
  - 月度 Top 5 发送者
- [x] 创建 `config/groups.yaml` — 目标群聊配置
- [x] 创建 README.md / PROGRESS.md
- [x] 初始化 Git 仓库
- [x] 创建 GitHub 仓库并 push
- [x] 更新 .project-status.yaml（规划中 → 运行中）
- [x] 同步 Dashboard

### 待验证
- [x] 运行 export_chats.py 验证 wechat-cli export 输出格式
- [x] 根据实际导出格式调整消息解析正则
- [x] 验证导出性能（4 个月 × 5 群聊）

### 已产出
- 20 个 Markdown 月份文件（`D:\Wechat_File\Wechat_ChatHistory\`）
- `_keyword_stats.json` — 5 群关键词统计
- `_member_activity.json` — 5 群成员活跃度分析

---

## 2026-04-27 — 项目立项

- 明确项目目标：聊天记录整理、分析、归档、结构化数据提取
- 确定技术方案：基于 wechat-cli + Kimi AI
- 需求来源：微信群聊 AI 分析项目的延伸需求
