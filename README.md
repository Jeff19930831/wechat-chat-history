# WeChat Chat History — 微信聊天记录整理与分析

## 项目概述

基于 [wechat-cli](../wechat-cli/) 工具，对微信聊天记录进行批量导出、整理、分析和结构化数据提取。覆盖文本消息的关键词统计、成员活跃度分析，以及图片的 AI 识别、分类归档和数值数据提取。

## 功能表

| 功能 | 状态 | 说明 |
|------|------|------|
| 群聊聊天记录批量导出 | 已完成 | 按月分段导出，支持增量更新 |
| 按时间段归档 | 已完成 | 按群名/年_月.md 组织 |
| Markdown 格式化 | 内置 | wechat-cli 原生支持 |
| 关键词搜索与统计 | 已完成 | Top 50 关键词 + 月度趋势 |
| 群成员活跃度分析 | 已完成 | 发言量、词数、时段分布 |
| 图片过滤与分类 | 已完成 | 去除无用图片，按数据类型分类 |
| 图片深度数据提取 | 已完成 | Kimi AI 提取结构化数据（价格/库存/产量等） |
| 图片分类整理 | 已完成 | 按类别复制到独立目录 |
| 月度统计报告 | 已完成 | 消息数、活跃成员、关键词、图片分类汇总 |
| 实时价格数据提取 | 已完成 | 从报盘/成交消息提取结构化价格表 |

## 技术栈

- Python 3.12
- wechat-cli（SQLCipher 解密 + 消息导出）
- PyYAML（配置管理）
- Kimi k2.6（图片 AI 分析）
- Markdown（归档格式，Obsidian 兼容）

## 关联项目

| 项目 | 关系 | 链接 |
|------|------|------|
| wechat-cli | 核心依赖 | [本地](../wechat-cli/) |
| wechat-decrypt | 依赖 | [本地](../wechat-decrypt/) |
| wechat-ai-daily | 关联项目 | [GitHub](https://github.com/Jeff19930831/wechat-ai-daily) |

## 代码仓库

- GitHub：[github.com/Jeff19930831/wechat-chat-history](https://github.com/Jeff19930831/wechat-chat-history)
- 本地：`D:\ClaudeCode\wechat-chat-history`

## 文档位置

- 知识库：`Win_Claude_Work\wechat-chat-history`

## 目录结构

```
wechat-chat-history/
├── config/
│   └── groups.yaml              # 目标群聊配置
├── src/
│   ├── export_chats.py          # 批量导出聊天记录
│   ├── keyword_stats.py         # 关键词统计分析
│   ├── member_activity.py       # 成员活跃度分析
│   ├── image_filter.py          # 图片过滤与分类
│   ├── image_data_extract.py    # Kimi 深度数据提取
│   ├── organize_by_category.py  # 按类别整理图片到目录
│   ├── monthly_report.py        # 月度统计报告生成
│   └── extract_price_data.py    # 实时价格数据提取
├── data/                         # 导出数据（运行时生成）
└── README.md / PROGRESS.md / HANDOFF.md
```

## 使用方式

### 1. 批量导出聊天记录

```bash
cd src
PYTHONIOENCODING=utf-8 python export_chats.py
```

输出：`D:\Wechat_File\Wechat_ChatHistory\群别名\YYYY_MM.md`

配置：`config/groups.yaml`
- `incremental: true` — 跳过已存在的月份
- `split_by_month: true` — 按月分割文件

### 2. 关键词统计

```bash
cd src
PYTHONIOENCODING=utf-8 python keyword_stats.py
```

输出：`D:\Wechat_File\Wechat_ChatHistory\_keyword_stats.json`

### 3. 成员活跃度分析

```bash
cd src
PYTHONIOENCODING=utf-8 python member_activity.py
```

输出：`D:\Wechat_File\Wechat_ChatHistory\_member_activity.json`

### 4. 图片过滤与分类

```bash
cd src
PYTHONIOENCODING=utf-8 python image_filter.py
```

输入：`D:\Wechat_File\Wechat_Image\群名\_image_summary.json`
输出：`D:\Wechat_File\Wechat_Image\群名\_image_filtered.json`

### 5. 图片深度数据提取（Kimi）

```bash
cd src
PYTHONIOENCODING=utf-8 python image_data_extract.py
```

输出：`D:\Wechat_File\Wechat_Image\_image_data_extracted.json`

### 6. 按类别整理图片

```bash
cd src
PYTHONIOENCODING=utf-8 python organize_by_category.py
```

输出：`D:\Wechat_File\Wechat_Image_Categorized\类别\群名\年月\文件名`

### 7. 月度统计报告

```bash
cd src
PYTHONIOENCODING=utf-8 python monthly_report.py
```

输出：`D:\Wechat_File\Wechat_Image\_monthly_report_YYYY_MM.md`

### 8. 实时价格数据提取

```bash
cd src
PYTHONIOENCODING=utf-8 python extract_price_data.py
```

输出：`D:\Wechat_File\Wechat_Image\_price_data_YYYY_MM.md`

## 配置

| 配置项 | 位置 | 说明 |
|--------|------|------|
| 微信密钥 | `C:\Users\lk\.wechat-cli\all_keys.json` | 26 个数据库密钥 |
| wechat-cli 配置 | `C:\Users\lk\.wechat-cli\config.json` | 数据库目录 |
| 群聊配置 | `config/groups.yaml` | 目标群聊列表 |

## 目标群聊（5 个）

与 wechat-ai-daily 保持一致：

| # | 群聊名称 | 别名 |
|---|---------|------|
| 1 | 【VIP】建龙北京 | jianlong-beijing |
| 2 | 中国矿产市场报告联系人群 | zhongkuang-report |
| 3 | 建龙集团市场分析交流群 | jianlong-market |
| 4 | Mysteel-铁矿石矿工群（正式） | mysteel-miner |
| 5 | Mysteel铁矿石资讯SVIP正式2群 | mysteel-svip |

## 产出文件

| 文件 | 位置 | 说明 |
|------|------|------|
| 聊天记录 | `D:\Wechat_File\Wechat_ChatHistory\` | 按月分群的 Markdown |
| 图片摘要 | `D:\Wechat_File\Wechat_Image\群名\_image_summary.json` | Kimi 生成的图片描述 |
| 过滤后图片 | `D:\Wechat_File\Wechat_Image\群名\_image_filtered.json` | 去除无用图 + 分类标签 |
| 深度提取数据 | `D:\Wechat_File\Wechat_Image\_image_data_extracted.json` | 结构化数值数据 |
| 分类图片目录 | `D:\Wechat_File\Wechat_Image_Categorized\` | 按类别整理的图片 |
| 月度报告 | `D:\Wechat_File\Wechat_Image\_monthly_report_YYYY_MM.md` | 统计汇总报告 |
| 价格数据报告 | `D:\Wechat_File\Wechat_Image\_price_data_YYYY_MM.md` | 结构化价格表 |

## 维护者

- 创建者：lk
- 创建日期：2026-04-27
- 当前状态：运行中
