# WeChat Chat History — 当前交接

> 给下一个 Agent / 下一台设备快速接手用。保持短、准、最新。

## 当前目标

飞书嵌入PDF下载已完成（409个/20GB）。图片AI提取仍在后台进行。下一步是价格数据集成和综合分析。

## 最近完成

1. **飞书嵌入PDF下载完成** — 409个真实PDF（20GB），224页面处理，385成功
2. **飞书文字内容提取** — 193/193 markdown文件
3. **垃圾数据清理** — 删除旧假PDF（86MB）、5个废弃脚本、调试文件
4. **飞书链接提取** — 224 PDF + 193 text链接分类
5. **Git push + 增量导出 + 正则优化** — 基础pipeline任务全部完成

## 下一步

1. **图片AI提取** — 后台仍在运行（1515张，Kimi API）
2. **价格数据集成** — 将结构化价格数据推送到飞书/邮件
3. **Port News T3综合分析** — 整合PDF研报、文字内容、价格数据
4. **重试失败的21个大文件PDF** — 超时导致，可用更长timeout重试

## 阻塞点

- 无

## 关键文件

| 文件 | 作用 | 注意事项 |
|------|------|----------|
| `src/cdp_download_real_pdf.js` | 飞书嵌入PDF下载 | 已完成409个，可重试失败项 |
| `src/cdp_fetch_text.js` | 飞书文字内容提取 | 已完成193/193 |
| `src/extract_feishu_links.py` | 飞书链接提取分类 | 输出feishu_links.json |
| `src/extract_price_data.py` | 价格数据提取 | 正则已优化 |
| `src/image_data_extract.py` | Kimi图片深度提取 | 后台运行中 |
| `src/export_chats.py` | 聊天记录导出 | 支持--refresh |
| `data/feishu_links.json` | 链接分类数据 | 224 PDF + 193 text |
| `data/browser_profile/` | Playwright浏览器profile | 包含登录状态，勿删 |

## 数据目录

| 目录 | 内容 | 数量 | 大小 |
|------|------|------|------|
| `feishu/pdf_real/` | 飞书嵌入真实PDF | 409个 | 20GB |
| `feishu/text/` | Port News Selected markdown | 193个 | 1.7MB |
| `pdf/` | WeChat缓存PDF | 42个 | 63MB |

## 验证命令

```bash
# 检查PDF数量
ls D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/pdf_real/ | wc -l
du -sh D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/pdf_real/

# Git 状态
cd D:/ClaudeCode/wechat-chat-history
git status && git log --oneline -3
```

## 当前工作区

- 分支：master
- 最近提交：`712084f [CHECKPOINT] feishu embedded PDF download + text extraction pipeline`
- 未提交改动：清理废弃脚本、更新文档
