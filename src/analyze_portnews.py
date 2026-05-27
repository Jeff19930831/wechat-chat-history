"""PortNews 综合分析：结构化提取 + 月度综述报告
- 读取 PortNews 每日 Markdown 报告
- 使用 DeepSeek-v4-pro 提取结构化数据
- 聚合生成月度分析报告
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from openai import OpenAI

# --- 常量 ---
PORTNEWS_BASE = Path("D:/SyncThing/PortNews")
CHAT_HISTORY_BASE = Path("D:/Wechat_File/Wechat_ChatHistory")
PRICE_DATA_BASE = Path("D:/Wechat_File/Wechat_Image")
OUTPUT_BASE = Path("D:/SyncThing/PortNews/analysis")

API_KEY_ENV = "DEEPSEEK_API_KEY"
API_BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-v4-pro"
API_DELAY = 2  # 秒

SYSTEM_PROMPT = "你是一个大宗商品市场分析专家，擅长从中文财经新闻中提取结构化信息。请严格按照要求输出 JSON 格式。"

DAILY_EXTRACT_PROMPT = """请分析以下 Port News 每日市场报告，提取结构化信息：

1. **涉及品种**：文中提到的大宗商品品种（铁矿石/钢材/焦煤/焦炭/铜/铝/原油/天然气/黄金/锂/镍/其他），标注每个品种的上下文
2. **价格信号**：文中提到的具体价格或价格方向
3. **宏观事件**：影响商品市场的重大事件（地缘政治/央行政策/贸易政策/经济数据）
4. **供应链信号**：供应端和需求端的具体变化
5. **市场情绪**：整体判断（看多/看空/中性/分歧）
6. **关键引用**：最重要的1-2句结论

严格以 JSON 格式输出，不要包含其他文字：
{
  "date": "YYYY-MM-DD",
  "edition": "AM 或 PM",
  "commodities": [
    {"name": "品种名", "context": "上下文说明", "direction": "上涨/下跌/持平/不确定"}
  ],
  "price_signals": [
    {"commodity": "品种", "price": "价格值", "unit": "单位", "direction": "上涨/下跌/持平", "benchmark": "对比基准"}
  ],
  "macro_events": [
    {"event": "事件描述", "impact": "对商品市场影响", "scope": "影响范围"}
  ],
  "supply_chain": {
    "supply": ["供应端变化1"],
    "demand": ["需求端变化1"]
  },
  "sentiment": {
    "overall": "看多/看空/中性/分歧",
    "reason": "判断依据"
  },
  "key_quotes": ["关键引用1"]
}

如果某字段在文中找不到，使用空数组或空字符串。以下是报告内容：

---"""


# --- API 客户端 ---
def get_client():
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        print(f"错误：未找到环境变量 {API_KEY_ENV}")
        sys.exit(1)
    return OpenAI(api_key=api_key, base_url=API_BASE_URL)


def extract_json_from_output(output: str) -> dict | list | None:
    if not output:
        return None
    # 去除 markdown code block 包裹
    cleaned = re.sub(r"```(?:json)?\s*", "", output)
    cleaned = re.sub(r"```\s*$", "", cleaned).strip()
    start = cleaned.find("{")
    if start < 0:
        start = cleaned.find("[")
    if start < 0:
        return None
    # 找匹配的闭合括号
    open_char = cleaned[start]
    close_char = "}" if open_char == "{" else "]"
    depth = 0
    for i in range(start, len(cleaned)):
        if cleaned[i] == open_char:
            depth += 1
        elif cleaned[i] == close_char:
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(cleaned[start:i + 1])
                except json.JSONDecodeError:
                    # 尝试修复尾部截断
                    for j in range(i, max(start, i - 50), -1):
                        if cleaned[j] == close_char:
                            try:
                                return json.loads(cleaned[start:j + 1])
                            except json.JSONDecodeError:
                                continue
                    return None
    return None


def call_glm(client, prompt: str, max_retries: int = 3, max_tokens: int = 2048) -> str:
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            if "429" in err or "rate" in err.lower():
                wait = 60 * (attempt + 1)
                print(f"  限流，等待 {wait}s...")
                time.sleep(wait)
            elif attempt < max_retries - 1:
                print(f"  API 错误 (attempt {attempt+1}): {err[:100]}")
                time.sleep(10)
            else:
                raise


# --- 文件发现 ---
def discover_portnews_files(month: str) -> list[Path]:
    pattern = PORTNEWS_BASE / month / "PortNews"
    if not pattern.exists():
        print(f"目录不存在: {pattern}")
        return []
    files = sorted(pattern.glob("*.md"))
    print(f"发现 {len(files)} 个 PortNews 文件 ({month})")
    return files


def discover_chat_commentary(month: str) -> list[dict]:
    month_us = month.replace("-", "_")
    chat_file = CHAT_HISTORY_BASE / "port-news-t3" / f"{month_us}.md"
    if not chat_file.exists():
        print(f"聊天记录不存在: {chat_file}")
        return []

    with open(chat_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    messages = []
    for line in lines:
        # 格式: - [2026-04-01 07:54] THE PORT: content
        # 或:   [2026-04-01 07:54:00] THE PORT: content
        m = re.match(r"-?\s*\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?)\]\s*(.+?):\s*(.+)", line)
        if m:
            messages.append({
                "time": m.group(1),
                "sender": m.group(2),
                "content": m.group(3),
            })

    the_port = [m for m in messages if "THE PORT" in m["sender"]]
    print(f"聊天记录: {len(messages)} 条消息, {len(the_port)} 条 THE PORT 评论")
    return the_port


# --- 内容去重 ---
def deduplicate_content(text: str) -> str:
    paragraphs = re.split(r"\n\s*\n", text)
    seen = set()
    unique = []
    for p in paragraphs:
        p_stripped = p.strip().replace("\u200b", "")
        if not p_stripped:
            continue
        h = hashlib.md5(p_stripped.encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            unique.append(p_stripped)
    return "\n\n".join(unique)


# --- 每日提取 ---
def extract_daily(client, filepath: Path, cache_dir: Path) -> dict:
    cache_file = cache_dir / f"{filepath.stem}.json"

    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            cached = json.load(f)
        if cached.get("status") == "success":
            cached["_from_cache"] = True
            return cached

    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    content = deduplicate_content(raw)
    prompt = DAILY_EXTRACT_PROMPT + "\n" + content

    result = {
        "source_file": filepath.name,
        "extracted_at": datetime.now().isoformat(),
        "status": "pending",
        "data": None,
    }

    try:
        output = call_glm(client, prompt)
        data = extract_json_from_output(output)
        if data is not None:
            result["data"] = data
            result["status"] = "success"
        else:
            result["status"] = "parse_error"
            result["raw"] = output[:500]
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:200]

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


# --- 评论主题提取 ---
COMMENTARY_PROMPT = """以下是 Port News 主理人 THE PORT 在 {month}月 发表的市场评论。请分析：

1. 月度主题（3-5个核心主题，标注频率和趋势）
2. 市场情绪轨迹（按周划分）
3. 关键转折点
4. 各品种月度观点

以 JSON 格式输出：
{{
  "monthly_themes": [{{"theme": "...", "frequency": "高频/中频/低频", "trend": "趋势描述"}}],
  "sentiment_trajectory": {{"week1": "...", "week2": "...", "week3": "...", "week4": "..."}},
  "turning_points": [{{"date_range": "...", "event": "...", "shift": "..."}}],
  "commodity_views": [{{"commodity": "...", "view": "看多/看空/中性", "reason": "..."}}]
}}

评论内容：
---"""


def extract_commentary_themes(client, messages: list[dict], month: str) -> dict:
    if not messages:
        return {"status": "no_data", "data": None}

    # 分段提取，每段最多30条，避免输出截断
    chunk_size = 30
    all_data = []
    for i in range(0, len(messages), chunk_size):
        chunk = messages[i:i + chunk_size]
        text = "\n".join(f"[{m['time']}] {m['content']}" for m in chunk)
        label = f"第{i//chunk_size+1}段" if len(messages) > chunk_size else ""
        prompt = COMMENTARY_PROMPT.format(month=month) + f"\n({label})\n" + text

        try:
            output = call_glm(client, prompt, max_tokens=2048)
            if not output or not output.strip():
                print(f"  评论段{i//chunk_size+1} 空响应，重试...")
                time.sleep(10)
                output = call_glm(client, prompt, max_tokens=2048)
            data = extract_json_from_output(output)
            if data is not None:
                all_data.append(data)
            else:
                print(f"  评论段{i//chunk_size+1} JSON解析失败")
            time.sleep(API_DELAY)
        except Exception as e:
            print(f"  评论段{i//chunk_size+1}错误: {str(e)[:100]}")

    if not all_data:
        return {"status": "parse_error", "data": None}

    # 合并分段结果
    merged = {
        "monthly_themes": [],
        "sentiment_trajectory": {},
        "turning_points": [],
        "commodity_views": [],
    }
    seen_themes = set()
    for d in all_data:
        for t in d.get("monthly_themes", []):
            key = t.get("theme", "")
            if key not in seen_themes:
                seen_themes.add(key)
                merged["monthly_themes"].append(t)
        merged["turning_points"].extend(d.get("turning_points", []))
        for v in d.get("commodity_views", []):
            merged["commodity_views"].append(v)
        if d.get("sentiment_trajectory"):
            merged["sentiment_trajectory"].update(d["sentiment_trajectory"])

    return {"status": "success", "data": merged}


# --- 价格数据加载 ---
def load_price_data(month: str) -> dict:
    month_us = month.replace("-", "_")
    price_file = PRICE_DATA_BASE / f"_price_data_{month_us}.md"
    if not price_file.exists():
        return {"status": "no_data", "records": 0}

    with open(price_file, "r", encoding="utf-8") as f:
        text = f.read()

    records = len(re.findall(r"\|.*\|.*\|.*\|", text))
    return {"status": "loaded", "records": records, "file": str(price_file)}


# --- 聚合与报告 ---
REPORT_PROMPT = """你是一个大宗商品研究分析师。基于以下结构化数据，撰写一份月度综合分析报告。

请以 Markdown 格式输出，包含以下章节：
## 月度市场概览
（200-300字概要，覆盖本月最重要的3个主题）

## 宏观与地缘政治
（本月重大事件及其对商品市场的影响）

## 品种分析
（按黑色系/有色金属/能源/贵金属/其他分类，每个品种的月度表现和关键变化）

## 供应链动态
（供应端和需求端的关键变化）

## 市场情绪与预期
（情绪演变路径 + 当前市场分歧）

## 下月展望
（基于本月趋势的延伸判断）

以下是结构化数据：
---"""


def generate_monthly_report(client, structured: dict, commentary: dict, price_info: dict, month: str) -> str:
    data_summary = json.dumps({
        "month": month,
        "daily_entries_count": len(structured.get("daily_entries", [])),
        "commentary_themes": (commentary.get("data") or {}).get("monthly_themes", [])[:5],
        "commodity_views": (commentary.get("data") or {}).get("commodity_views", []),
        "sentiment_trajectory": (commentary.get("data") or {}).get("sentiment_trajectory", {}),
        "price_data": price_info,
        "top_commodities": structured.get("commodity_index", {}),
    }, ensure_ascii=False, indent=2)

    daily_summaries = []
    for entry in structured.get("daily_entries", []):
        d = entry.get("data", {})
        if d:
            daily_summaries.append({
                "date": d.get("date"),
                "commodities": [c.get("name") for c in d.get("commodities", [])],
                "sentiment": d.get("sentiment", {}).get("overall"),
                "macro_events": [e.get("event") for e in d.get("macro_events", [])],
            })

    prompt = REPORT_PROMPT + "\n" + json.dumps({
        "summary": data_summary,
        "daily_summaries": daily_summaries,
    }, ensure_ascii=False, indent=2)

    try:
        return call_glm(client, prompt, max_retries=2, max_tokens=4096)
    except Exception as e:
        return f"# 报告生成失败\n\n错误: {e}"


def build_commodity_index(daily_results: list[dict]) -> dict:
    index = {}
    for r in daily_results:
        data = r.get("data")
        if not data:
            continue
        for c in data.get("commodities", []):
            name = c.get("name", "未知")
            if name not in index:
                index[name] = {"mentions": 0, "directions": []}
            index[name]["mentions"] += 1
            if c.get("direction"):
                index[name]["directions"].append(c["direction"])
    return index


# --- 主流程 ---
def main():
    parser = argparse.ArgumentParser(description="PortNews 综合分析")
    parser.add_argument("--month", help="月份 YYYY-MM（全月模式）")
    parser.add_argument("--date", help="日期 YYYY-MM-DD（仅提取当天文件）")
    parser.add_argument("--limit", type=int, default=0, help="限制处理文件数（0=全部）")
    parser.add_argument("--skip-report", action="store_true", help="跳过报告生成")
    parser.add_argument("--daily", action="store_true", help="每日模式：只提取，跳过报告和评论")
    args = parser.parse_args()

    if not args.month and not args.date:
        parser.error("需要 --month 或 --date 参数")

    if args.date:
        month = args.date[:7]
        date_prefix = args.date
    else:
        month = args.month
        date_prefix = None

    output_dir = OUTPUT_BASE / month
    cache_dir = output_dir / "_daily"
    cache_dir.mkdir(parents=True, exist_ok=True)

    mode = "每日增量" if (date_prefix or args.daily) else "全月分析"
    print(f"=== PortNews {mode}: {date_prefix or month} ===\n")

    # 1. 发现文件
    files = discover_portnews_files(month)
    if not files:
        print("未找到 PortNews 文件，退出")
        return

    if date_prefix:
        files = [f for f in files if date_prefix in f.name]
        if not files:
            print(f"未找到 {date_prefix} 的 PortNews 文件，退出")
            return
        print(f"当天文件: {len(files)} 个")

    if args.limit > 0:
        files = files[:args.limit]
        print(f"限制处理: {len(files)} 个文件")

    is_daily = args.daily or date_prefix is not None

    # 2. 评论和价格（每日模式跳过）
    if is_daily:
        commentary = []
        price_info = {"status": "skipped", "records": 0}
    else:
        commentary = discover_chat_commentary(month)
        price_info = load_price_data(month)
        print(f"价格数据: {price_info['status']} ({price_info.get('records', 0)} 条)\n")

    # 3. 每日提取
    client = get_client()
    daily_results = []
    cached_count = 0

    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {f.name}...", end=" ", flush=True)
        result = extract_daily(client, f, cache_dir)
        daily_results.append(result)

        if result.get("_from_cache"):
            cached_count += 1
            print("缓存 OK", end="")
        elif result["status"] == "success":
            commodities = [c.get("name", "?") for c in (result.get("data", {}).get("commodities", [])[:3])]
            sentiment = result.get("data", {}).get("sentiment", {}).get("overall", "?")
            print(f"OK | {', '.join(commodities)} | {sentiment}", end="")
        else:
            print(f"FAIL | {result['status']}", end="")

        print()
        if i < len(files) and result["status"] == "success":
            time.sleep(API_DELAY)

    success = sum(1 for r in daily_results if r["status"] == "success")
    print(f"\n提取完成: {success}/{len(daily_results)} 成功 ({cached_count} 缓存)")

    # 每日模式：只保存结构化数据，到此结束
    if is_daily:
        # 增量合并到已有 _structured.json
        structured_file = output_dir / "_structured.json"
        if structured_file.exists():
            with open(structured_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
            existing_entries = {e["source_file"] for e in existing.get("daily_entries", []) if isinstance(e, dict)}
            new_results = [r for r in daily_results if r["source_file"] not in existing_entries]
            existing["daily_entries"].extend(new_results)
            existing["commodity_index"] = build_commodity_index(existing["daily_entries"])
            existing["meta"]["daily_files_processed"] = len(existing["daily_entries"])
            existing["meta"]["daily_success"] = sum(
                1 for e in existing["daily_entries"] if isinstance(e, dict) and e.get("status") == "success"
            )
            existing["meta"]["last_daily_update"] = datetime.now().isoformat()
            structured = existing
        else:
            structured = {
                "meta": {
                    "month": month,
                    "generated_at": datetime.now().isoformat(),
                    "last_daily_update": datetime.now().isoformat(),
                    "daily_files_processed": len(daily_results),
                    "daily_success": success,
                },
                "daily_entries": daily_results,
                "commodity_index": build_commodity_index(daily_results),
            }

        with open(structured_file, "w", encoding="utf-8") as f:
            json.dump(structured, f, ensure_ascii=False, indent=2)
        print(f"结构化数据已更新: {structured_file}")
        print("\n=== 每日增量完成 ===")
        return

    # === 以下为全月分析模式 ===

    # 4. 聚合
    commodity_index = build_commodity_index(daily_results)
    structured = {
        "meta": {
            "month": month,
            "generated_at": datetime.now().isoformat(),
            "daily_files_processed": len(daily_results),
            "daily_success": success,
            "commentary_messages": len(commentary),
            "price_records": price_info.get("records", 0),
        },
        "daily_entries": daily_results,
        "commodity_index": commodity_index,
    }

    structured_file = output_dir / "_structured.json"
    with open(structured_file, "w", encoding="utf-8") as f:
        json.dump(structured, f, ensure_ascii=False, indent=2)
    print(f"结构化数据已保存: {structured_file}")

    # 5. 评论主题
    print("\n提取评论主题...")
    commentary_result = extract_commentary_themes(client, commentary, month)
    if commentary_result["status"] == "success":
        themes = [t.get("theme", "") for t in commentary_result["data"].get("monthly_themes", [])[:3]]
        print(f"评论主题: {', '.join(themes)}")
    else:
        print(f"评论提取: {commentary_result['status']}")

    # 6. 月度报告
    if not args.skip_report:
        print("\n生成月度报告...")
        report = generate_monthly_report(client, structured, commentary_result, price_info, month)

        report_file = output_dir / "_monthly_summary.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"# Port News 月度综合分析 — {month}\n\n")
            f.write(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"> 数据源: {success} 份日报 + {len(commentary)} 条评论 + {price_info.get('records', 0)} 条价格数据\n\n")
            f.write(report)
        print(f"月度报告已保存: {report_file}")
    else:
        print("跳过报告生成")

    print("\n=== 全月分析完成 ===")


if __name__ == "__main__":
    main()
