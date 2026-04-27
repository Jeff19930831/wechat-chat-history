# WeChat Chat History — 微信聊天记录整理

## 项目概述

基于 [wechat-cli](../wechat-cli/) 工具，对微信聊天记录进行批量导出、整理、分析和归档。

## 功能表

| 功能 | 状态 | 说明 |
|------|------|------|
| 群聊聊天记录批量导出 | 开发完成 | 按月分段导出，支持增量更新 |
| 按时间段归档 | 开发完成 | 按群名/年_月.md 组织 |
| Markdown 格式化 | 内置 | wechat-cli 原生支持 |
| 关键词搜索与统计 | 开发完成 | Top 50 关键词 + 月度趋势 |
| 群成员活跃度分析 | 开发完成 | 发言量、词数、时段分布 |

## 技术栈

- Python 3.12
- wechat-cli（SQLCipher 解密 + 消息导出）
- PyYAML（配置管理）
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
│   └── groups.yaml          # 目标群聊配置
├── src/
│   ├── export_chats.py      # 批量导出脚本
│   ├── keyword_stats.py     # 关键词统计分析
│   └── member_activity.py   # 成员活跃度分析
├── data/                     # 导出数据（运行时生成）
└── README.md / PROGRESS.md
```

## 使用方式

### 1. 批量导出聊天记录

```bash
cd src
PYTHONIOENCODING=utf-8 python export_chats.py
```

输出结构：`D:\Wechat_File\Wechat_ChatHistory\群别名\YYYY_MM.md`

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

## 维护者

- 创建者：lk
- 创建日期：2026-04-27
- 当前状态：运行中
