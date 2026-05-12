# WeChat Chat History — 当前交接

> 给下一个 Agent / 下一台设备快速接手用。保持短、准、最新。

## 当前目标

飞书嵌入PDF下载和图片AI提取两个后台任务运行中。核心pipeline已完成，等待全量数据采集完成后进行结构化分析。

## 最近完成

1. **飞书嵌入PDF下载** — `cdp_download_real_pdf.js` 可正确下载实际嵌入PDF（非打印页面），后台运行中
2. **飞书文字内容提取** — `cdp_fetch_text.js` 193/193 成功
3. **飞书链接提取** — `extract_feishu_links.py` 分类224 PDF + 193 text链接
4. **Git push修复** — SSL问题已解决，代码已推送
5. **增量导出** — 2026-05聊天数据已导出
6. **正则优化** — `extract_price_data.py` 扩展品种匹配

## 下一步

1. **等待PDF下载完成** — 后台任务 `bayc39niy` 运行中（224页面）
2. **等待图片提取完成** — 1515张图片Kimi AI提取（约57%进度）
3. **价格数据集成** — 将结构化价格数据推送到飞书/邮件
4. **Port News T3综合分析** — 整合PDF研报、文字内容、价格数据

## 阻塞点

- 无

## 关键文件

| 文件 | 作用 | 注意事项 |
|------|------|----------|
| `src/cdp_download_real_pdf.js` | 飞书嵌入PDF下载 | 后台运行，有进度追踪 |
| `src/cdp_fetch_text.js` | 飞书文字内容提取 | 已完成193/193 |
| `src/extract_feishu_links.py` | 飞书链接提取分类 | 输出feishu_links.json |
| `src/extract_price_data.py` | 价格数据提取 | 正则已优化 |
| `src/image_data_extract.py` | Kimi图片深度提取 | 后台运行中 |
| `src/export_chats.py` | 聊天记录导出 | 支持--refresh |
| `data/feishu_links.json` | 链接分类数据 | 224 PDF + 193 text |
| `data/pdf_download_progress.json` | PDF下载进度 | 按页面追踪 |
| `data/browser_profile/` | Playwright浏览器profile | 包含登录状态，勿删 |

## 验证命令

```bash
# 检查PDF下载进度
ls D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/pdf_real/ | wc -l
du -sh D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/pdf_real/

# 检查文字内容
ls D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/text/ | wc -l

# 重新运行PDF下载（如需）
cd D:/ClaudeCode/wechat-chat-history
node src/cdp_download_real_pdf.js --start 0 --count 5

# Git 状态
cd D:/ClaudeCode/wechat-chat-history
git status && git log --oneline -3
```

## 当前工作区

- 分支：master
- 最近提交：`35443a0 feat: refresh mode, full image extraction, regex improvements`
- 未提交改动：飞书下载相关脚本（cdp_*.js, extract_feishu_links.py等）
