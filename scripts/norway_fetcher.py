#!/usr/bin/env python3
"""
norway.twsthr.info 籌碼數據抓取器

數據來源: 神秘金字塔 (norway.twsthr.info)
原始資料: 台灣集保所 + Google Finance

頁面說明:
- StockHoldersTopWeek.aspx?Show=1 — 類股排行(全部上市櫃)
- StockHoldersTopWeek.aspx?Show=2 — 台灣50排行
- StockHoldersTopWeek.aspx?CID=XX&Show=1 — 特定產業類別
- StockHolders.aspx?STOCK=XXXX — 個股籌碼詳情

表格結構 (19 cells per data row):
  thead row 0: 主表頭 (11 cells)
  thead row 1: 週日期 (9 cells: 6週日期 + empty + 走勢 + 總增減)
  tbody rows:  資料行 (19 cells)
    0-1:  empty
    2:    # (排名)
    3:    股票代號/名稱
    4:    類別
    5-10: 6週大股東持有張數增減 %
    11:   empty
    12:   門檻代碼 (50/31/30/10/40)
    13:   總增減 %
    14:   empty
    15:   上週持有 %
    16:   今日收盤價
    17:   今日漲跌
    18:   empty
"""

import requests
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

BASE_URL = "https://norway.twsthr.info"
OUTPUT_DIR = "data/norway"

# 門檻代碼對照
THRESHOLD_MAP = {
    50: 400,   # >400張
    31: 400,   # >400張
    30: 400,   # >400張
    10: 1000,  # >1000張
    40: 200,   # >200張
}


def fetch_html(url_path: str, params: Optional[Dict] = None) -> str:
    """抓取頁面 HTML — 帶 retry 與反爬蟲 headers"""
    import time

    url = f"{BASE_URL}/{url_path}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    for attempt in range(3):
        try:
            time.sleep(1.5 * attempt)
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code == 200:
                resp.encoding = "utf-8"
                return resp.text
            print(f"[WARN] {url} returned {resp.status_code}, retrying ({attempt + 1}/3)...")
        except Exception as e:
            print(f"[WARN] Request failed: {e}, retrying ({attempt + 1}/3)...")
            time.sleep(2)

    raise RuntimeError(f"Failed to fetch {url} after 3 attempts")


def _extract_week_dates(thead_rows: List) -> List[str]:
    """從 thead 第二行提取6個週日期"""
    if len(thead_rows) < 2:
        return []
    
    date_row = thead_rows[1]
    cells = date_row.find_all(["th", "td"])
    dates = []
    for i in range(min(6, len(cells))):
        text = cells[i].get_text(strip=True)
        if re.match(r'\d{4,8}', text):
            dates.append(text)
    return dates


def _complete_dates(short_dates: List[str], html: str) -> List[str]:
    """補全年份到簡短日期"""
    title_match = re.search(r'(\d{4})/(\d{2})/(\d{2})', html)
    base_year = title_match.group(1) if title_match else str(datetime.now().year)
    
    result = []
    for d in short_dates:
        if len(d) == 8:
            result.append(d)
        elif len(d) == 4:
            result.append(f"{base_year}{d}")
        else:
            result.append(d)
    return result


def parse_top_week(html: str) -> List[Dict]:
    """解析類股排行表格"""
    soup = BeautifulSoup(html, "html.parser")
    
    # 找有 thead + tbody 的 table，且 tbody rows 有 >=15 cells
    tables = soup.find_all("table")
    data_table = None
    for t in tables:
        rows = t.find_all("tr")
        max_cells = max((len(r.find_all(["td", "th"])) for r in rows), default=0)
        if max_cells >= 15:
            data_table = t
            break
    
    if data_table is None:
        raise ValueError("No data table found with >=15 cells")
    
    # 提取週日期
    thead = data_table.find("thead")
    thead_rows = thead.find_all("tr") if thead else []
    week_dates = _extract_week_dates(thead_rows)
    complete_dates = _complete_dates(week_dates, html)
    
    # 解析 tbody
    tbody = data_table.find("tbody")
    if tbody is None:
        raise ValueError("No tbody found")
    
    rows = tbody.find_all("tr")
    records = []
    
    for tr in rows:
        cells = tr.find_all(["td", "th"])
        if len(cells) < 16:
            continue
        
        texts = [c.get_text(strip=True) for c in cells]
        
        # 股票代號/名稱 (cell 3)
        raw_name = texts[3] if len(texts) > 3 else ""
        stock_info = _parse_stock_name(raw_name)
        if not stock_info["code"]:
            continue
        
        # 6週增減 (cells 5-10)
        weekly_changes = {}
        for i in range(6):
            idx = 5 + i
            if idx < len(texts):
                try:
                    val = float(texts[idx])
                except:
                    val = None
                date_key = complete_dates[i] if i < len(complete_dates) else f"week_{i}"
                weekly_changes[date_key] = val
        
        record = {
            "rank": _safe_int(texts[2]),
            "stock_code": stock_info["code"],
            "stock_name": stock_info["name"],
            "is_taiwan50": stock_info["star"],
            "category": texts[4] if len(texts) > 4 else "",
            "threshold_code": _safe_int(texts[12]),
            "threshold_shares": THRESHOLD_MAP.get(_safe_int(texts[12]), 0),
            "weekly_changes": weekly_changes,
            "latest_change": list(weekly_changes.values())[-1] if weekly_changes else None,
            "total_change": _safe_float(texts[13]),
            "last_week_hold_pct": _safe_float(texts[15]),
            "close_price": _safe_float(texts[16]),
            "price_change": _safe_float(texts[17]),
        }
        records.append(record)
    
    return records


def _parse_stock_name(raw: str) -> Dict[str, str]:
    """解析 '2327國巨*' → {'code':'2327','name':'國巨','star':True}"""
    m = re.match(r'(\d{4})(.+?)(\*)?$', raw.strip())
    if m:
        return {
            "code": m.group(1),
            "name": m.group(2),
            "star": bool(m.group(3)),
        }
    return {"code": raw, "name": raw, "star": False}


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(str(val).replace(",", ""))
    except:
        return None


def _safe_int(val) -> int:
    try:
        return int(str(val).replace(",", ""))
    except:
        return 0


def save_data(records: List[Dict], filename: str):
    """保存 JSON 數據"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved {len(records)} records → {filepath}")


def fetch_taiwan50():
    """抓取台灣50排行"""
    print("[INFO] Fetching Taiwan 50 ranking...")
    html = fetch_html("StockHoldersTopWeek.aspx", {"Show": 2})
    records = parse_top_week(html)
    save_data(records, "taiwan50_weekly.json")
    return records


def fetch_all_categories():
    """抓取所有類別 (上市 + 上櫃)"""
    # Norway 类别: 1-40 (上市), 90-140 (上櫃), 199 (其他)
    all_cids = list(range(1, 41)) + list(range(90, 141)) + [199]
    all_records = []
    
    for cid in all_cids:
        try:
            html = fetch_html("StockHoldersTopWeek.aspx", {"Show": 1, "CID": cid})
            records = parse_top_week(html)
            if not records:
                continue
            cat_name = records[0].get("category", f"cat_{cid}")
            save_data(records, f"category_{cid}_{cat_name}.json")
            all_records.extend(records)
            print(f"[OK] CID={cid} ({cat_name}): {len(records)} stocks")
        except Exception as e:
            print(f"[WARN] CID={cid}: {e}")
    
    # 去重
    seen = set()
    unique = []
    for r in all_records:
        code = r.get("stock_code")
        if code and code not in seen:
            seen.add(code)
            unique.append(r)
    
    save_data(unique, "all_stocks_weekly.json")
    print(f"[INFO] Total unique stocks: {len(unique)}")
    
    # 統計
    otc_count = sum(1 for r in unique if str(r.get('stock_code', '')).startswith('8'))
    print(f"[INFO] OTC (8xxx) stocks: {otc_count}")
    
    return unique


if __name__ == "__main__":
    print("=" * 50)
    print("Norway.twsthr.info 籌碼數據抓取器")
    print("=" * 50)
    
    # 抓取所有類別（包含上市+上櫃）
    records = fetch_all_categories()
    print(f"\n[INFO] Total unique stocks: {len(records)}")
    
    # 統計上櫃股票數量
    otc_count = sum(1 for r in records if str(r.get('stock_code', '')).startswith('8'))
    print(f"[INFO] OTC (8xxx) stocks: {otc_count}")
