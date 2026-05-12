"""整理 Port News T3 下载文件到 D:\SyncThing，按月份分文件夹
- PDF研报/刊物 → 按文件名中日期归入月份文件夹
- Text (Port News Selected) → 按文件名日期前缀归入月份文件夹
- WeChat缓存PDF → 统一放入 wechat_cached/
"""
import os
import re
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = "D:/SyncThing/PortNews"
PDF_DIR = "D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/pdf_real"
TEXT_DIR = "D:/Wechat_File/Wechat_ChatHistory/port-news-t3/feishu/text"
CACHE_DIR = "D:/Wechat_File/Wechat_ChatHistory/port-news-t3/pdf"


def extract_month_from_pdf(name):
    """从PDF文件名提取月份 (YYYY-MM)"""
    # Pattern 1: YYMMDD like 260305, 260323
    m = re.search(r'(\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])', name)
    if m:
        return f"20{m.group(1)}-{m.group(2)}"

    # Pattern 1b: M.D-D or M.D date range like 1.3-4, 4.25-26 (F Times, W..L files)
    m = re.search(r'(\d{1,2})\.(\d{1,2})-\d{1,2}', name)
    if m:
        month = int(m.group(1))
        if 1 <= month <= 12:
            return f"2026-{month:02d}"

    # Pattern 2: M.D like 1.16, 4.3, 12.31
    m = re.search(r'(\d{1,2})\.(\d{1,2})(?:\s|\.pdf|$)', name)
    if m:
        month = int(m.group(1))
        day = int(m.group(2))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"2026-{month:02d}"

    # Pattern 3: "March 2026", "Apr" etc
    month_map = {
        'jan': '01', 'january': '01',
        'feb': '02', 'february': '02',
        'mar': '03', 'march': '03',
        'apr': '04', 'april': '04',
        'may': '05',
        'jun': '06', 'june': '06',
        'jul': '07', 'july': '07',
        'aug': '08', 'august': '08',
        'sep': '09', 'september': '09',
        'oct': '10', 'october': '10',
        'nov': '11', 'november': '11',
        'dec': '12', 'december': '12',
    }
    for name_lower, mm in month_map.items():
        if name_lower in name.lower():
            return f"2026-{mm}"

    return None


def main():
    os.makedirs(BASE, exist_ok=True)

    # === Move PDFs ===
    print(f"=== 整理 PDF 研报/刊物 ({PDF_DIR}) ===")
    pdf_files = os.listdir(PDF_DIR)
    pdf_ok = 0
    pdf_no_date = []

    for f in pdf_files:
        if not f.endswith('.pdf'):
            continue
        src = os.path.join(PDF_DIR, f)
        if not os.path.isfile(src):
            continue

        month = extract_month_from_pdf(f)
        if month:
            dest_dir = os.path.join(BASE, month, "研报")
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, f)
            if not os.path.exists(dest):
                shutil.move(src, dest)
            pdf_ok += 1
        else:
            pdf_no_date.append(f)

    print(f"  已整理: {pdf_ok}")
    print(f"  无法提取月份: {len(pdf_no_date)}")
    for f in pdf_no_date:
        dest_dir = os.path.join(BASE, "未知月份", "研报")
        os.makedirs(dest_dir, exist_ok=True)
        src = os.path.join(PDF_DIR, f)
        dest = os.path.join(dest_dir, f)
        if not os.path.exists(dest):
            shutil.move(src, dest)
        print(f"    → 未知月份: {f}")

    # === Move Text ===
    print(f"\n=== 整理 Port News Selected ({TEXT_DIR}) ===")
    text_files = os.listdir(TEXT_DIR)
    text_ok = 0

    for f in text_files:
        if not f.endswith('.md'):
            continue
        src = os.path.join(TEXT_DIR, f)

        m = re.match(r'(\d{4}-\d{2})-\d{2}_', f)
        if m:
            month = m.group(1)
            dest_dir = os.path.join(BASE, month, "PortNews")
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, f)
            if not os.path.exists(dest):
                shutil.move(src, dest)
            text_ok += 1
        else:
            dest_dir = os.path.join(BASE, "未知月份", "PortNews")
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, f)
            if not os.path.exists(dest):
                shutil.move(src, dest)
            print(f"    → 未知月份: {f}")

    print(f"  已整理: {text_ok}")

    # === Move WeChat cached PDFs ===
    print(f"\n=== 整理 WeChat 缓存 PDF ({CACHE_DIR}) ===")
    if os.path.exists(CACHE_DIR):
        cache_files = os.listdir(CACHE_DIR)
        dest_dir = os.path.join(BASE, "wechat_cached")
        os.makedirs(dest_dir, exist_ok=True)
        cache_ok = 0
        for f in cache_files:
            src = os.path.join(CACHE_DIR, f)
            if not os.path.isfile(src):
                continue
            dest = os.path.join(dest_dir, f)
            if not os.path.exists(dest):
                shutil.move(src, dest)
            cache_ok += 1
        print(f"  已整理: {cache_ok}")

    # === Summary ===
    print(f"\n{'='*60}")
    print(f"整理完成!")
    print(f"  PDF研报: {pdf_ok}")
    print(f"  PortNews文字: {text_ok}")
    print(f"  目标目录: {BASE}")

    for root, dirs, files in os.walk(BASE):
        level = root.replace(BASE, '').count(os.sep)
        indent = ' ' * 2 * level
        count = len(files)
        size = sum(os.path.getsize(os.path.join(root, f)) for f in files if os.path.isfile(os.path.join(root, f)))
        print(f'{indent}{os.path.basename(root)}/ ({count} files, {size/1024/1024:.1f}MB)')


if __name__ == "__main__":
    main()
