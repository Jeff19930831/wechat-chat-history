# WeChat Chat History — 当前计划

> 未完成事项只放这里。完成后移到 progress.md。

## 进行中

- [ ] **Git push** — 将最新代码 push 到 GitHub（上次 push 因 SSL 失败）
- [ ] **价格数据集成** — 考虑将 `_price_data_YYYY_MM.md` 推送到飞书或邮件
- [ ] **正则优化** — `extract_price_data.py` 的 PRICE_PATTERN 和 DEAL_PATTERN 扩展覆盖更多品种格式（巴西精粉、乌克兰精粉等）
- [ ] **图片提取扩展** — 当前仅提取 28 张典型图片，考虑扩展到全部 1515 张
- [ ] **下月数据** — 5 月初运行 export_chats.py 增量导出 2026-05 数据

## 阻塞

- Git push SSL 错误：上次 push 失败，需检查网络或 GitHub token
- Kimi 429 限流：image_data_extract.py 高并发时触发，已降低 MAX_WORKERS=4

## 待开始

- [ ] 根据用户反馈调整停用词和解析逻辑
