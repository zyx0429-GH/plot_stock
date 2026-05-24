import requests
from bs4 import BeautifulSoup
import json
import os

def parse_top_week():
    url = "https://norway.twsthr.info/StockHoldersTopWeek.aspx"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    print(f"[INFO] Fetching {url}...")
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    
    # Server claims utf-8, and encoding_test confirms utf-8 is correct
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Find main data table by id="details"
    main_table = soup.find("table", id="details")
    if not main_table:
        print("[ERR] Table with id='details' not found")
        # Fallback: find table with most cells in first row
        tables = soup.find_all("table")
        best_cells = 0
        for t in tables:
            first_row = t.find("tr")
            if first_row:
                n_cells = len(first_row.find_all(["td", "th"]))
                if n_cells > best_cells:
                    best_cells = n_cells
                    main_table = t
        if not main_table:
            print("[ERR] No suitable table found")
            return []
    
    tbody = main_table.find("tbody")
    if not tbody:
        tbody = main_table
    
    rows = tbody.find_all("tr")
    
    # Get dates from thead second row
    thead = main_table.find("thead")
    dates = ["20260410", "20260417", "20260424", "20260430", "20260508", "20260515"]
    if thead:
        date_rows = thead.find_all("tr")
        if len(date_rows) >= 2:
            date_cells = date_rows[1].find_all(["td", "th"])
            if len(date_cells) >= 6:
                dates = [c.get_text(strip=True) for c in date_cells[3:9]]
    
    stocks = []
    for r in rows:
        cells = r.find_all("td")
        if len(cells) < 16:
            continue
        
        rank_text = cells[2].get_text(strip=True)
        if not rank_text.isdigit():
            continue
        
        stock_text = cells[3].get_text(strip=True)
        if len(stock_text) < 4:
            continue
        
        stock_code = stock_text[:4]
        stock_name = stock_text[4:]
        
        try:
            weekly_changes = {
                dates[0]: float(cells[5].get_text(strip=True)),
                dates[1]: float(cells[6].get_text(strip=True)),
                dates[2]: float(cells[7].get_text(strip=True)),
                dates[3]: float(cells[8].get_text(strip=True)),
                dates[4]: float(cells[9].get_text(strip=True)),
                dates[5]: float(cells[10].get_text(strip=True)),
            }
        except (ValueError, IndexError):
            continue
        
        try:
            threshold_code = int(cells[12].get_text(strip=True)) if cells[12].get_text(strip=True) else 0
        except ValueError:
            threshold_code = 0
        
        try:
            total_change = float(cells[13].get_text(strip=True))
        except ValueError:
            total_change = 0.0
        
        try:
            last_week_hold = float(cells[15].get_text(strip=True))
        except ValueError:
            last_week_hold = 0.0
        
        try:
            close_price = float(cells[16].get_text(strip=True))
        except (ValueError, IndexError):
            close_price = 0.0
        
        try:
            price_change = float(cells[17].get_text(strip=True))
        except (ValueError, IndexError):
            price_change = 0.0
        
        stocks.append({
            "rank": int(rank_text),
            "stock_code": stock_code,
            "stock_name": stock_name,
            "category": cells[4].get_text(strip=True),
            "threshold_code": threshold_code,
            "weekly_changes": weekly_changes,
            "latest_change": weekly_changes.get(dates[5], 0),
            "total_change": total_change,
            "last_week_hold_pct": last_week_hold,
            "close_price": close_price,
            "price_change": price_change,
        })
    
    return stocks

if __name__ == "__main__":
    stocks = parse_top_week()
    
    os.makedirs("../data/norway", exist_ok=True)
    out_path = "../data/norway/top200_weekly_20260522.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)
    
    # Write summary to file instead of console (avoid Windows cp950 encoding issues)
    with open("../data/norway/fetch_log.txt", "w", encoding="utf-8") as log:
        log.write(f"Parsed {len(stocks)} stocks\n")
        log.write(f"Saved to {out_path}\n\n")
        log.write("=== Top 20 ===\n")
        for s in stocks[:20]:
            log.write(f"  {s['rank']:>3} | {s['stock_code']} {s['stock_name']:<8} | {s['category']:<10} | 週增={s['latest_change']:>+6.2f}% | 總增={s['total_change']:>+6.2f}% | 持有={s['last_week_hold_pct']:>5.2f}% | 收盤={s['close_price']}\n")
    
    # Use ASCII-only print to avoid Windows console encoding issues
    print(f"[OK] Parsed {len(stocks)} stocks")
    print(f"[OK] Saved to {out_path}")
    print("[OK] Summary written to data/norway/fetch_log.txt")
