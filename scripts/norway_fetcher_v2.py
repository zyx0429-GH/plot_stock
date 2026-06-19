"""
Norway.twsthr.info fetcher - NEW VERSION
Parses server-rendered HTML directly (not AJAX)
"""
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import json
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NORWAY_URL = 'https://norway.twsthr.info/StockHoldersTopWeek.aspx?Show=1'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
}


def fetch_norway_html():
    """Fetch raw HTML from Norway website"""
    print(f"Fetching {NORWAY_URL}...")
    resp = requests.get(NORWAY_URL, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    # Force UTF-8 encoding
    resp.encoding = 'utf-8'
    print(f"Response status: {resp.status_code}, length: {len(resp.text)}")
    return resp.text


def parse_stock_code_name(td_text):
    """Extract stock code and name from cell like '2399映泰'"""
    # Pattern: 4-digit code followed by name
    match = re.match(r'^(\d{4})(.+)$', td_text)
    if match:
        return match.group(1), match.group(2)
    # Try 6-digit (上櫃)
    match = re.match(r'^(\d{6})(.+)$', td_text)
    if match:
        return match.group(1), match.group(2)
    return None, None


def parse_norway_data(html):
    """Parse Norway HTML to extract big holder data"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find the main data table
    table = soup.find('table', {'id': 'details'})
    if not table:
        print("ERROR: Could not find table with id='details'")
        # Try alternative selectors
        table = soup.find('table', {'role': 'grid'})
        if not table:
            raise ValueError("Could not find data table in HTML")
    
    tbody = table.find('tbody')
    if not tbody:
        tbody = table
    
    rows = tbody.find_all('tr')
    print(f"Found {len(rows)} data rows")
    
    data = []
    skipped = 0
    
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) < 15:
            skipped += 1
            continue
        
        try:
            # Cell indices based on observed HTML structure:
            # 0: empty
            # 1: color indicator
            # 2: rank #
            # 3: stock code/name link
            # 4: category
            # 5-10: weekly changes (20260515, 0522, 0529, 0605, 0612, 0618)
            # 11: empty
            # 12: trend image
            # 13: total change
            # 14: empty
            # 15: last week holding %
            # 16: today's close price
            # 17: today's change
            # 18: empty/grade
            
            stock_link = cells[3].get_text(strip=True)
            stock_code, stock_name = parse_stock_code_name(stock_link)
            
            if not stock_code:
                skipped += 1
                continue
            
            # Extract weekly changes
            weekly_changes = []
            for i in range(5, 11):
                if i < len(cells):
                    val = cells[i].get_text(strip=True)
                    try:
                        weekly_changes.append(float(val) if val else 0.0)
                    except ValueError:
                        weekly_changes.append(0.0)
                else:
                    weekly_changes.append(0.0)
            
            # Latest week change (last column in weekly range)
            latest_week_change = weekly_changes[-1] if weekly_changes else 0.0
            
            # Total change
            total_change_text = cells[13].get_text(strip=True) if len(cells) > 13 else '0'
            try:
                total_change = float(total_change_text)
            except ValueError:
                total_change = 0.0
            
            # Last week holding %
            holding_text = cells[15].get_text(strip=True) if len(cells) > 15 else '0'
            try:
                holding_pct = float(holding_text)
            except ValueError:
                holding_pct = 0.0
            
            # Today's close
            close_text = cells[16].get_text(strip=True) if len(cells) > 16 else '0'
            try:
                close_price = float(close_text)
            except ValueError:
                close_price = 0.0
            
            # Today's change
            change_text = cells[17].get_text(strip=True) if len(cells) > 17 else '0'
            try:
                daily_change = float(change_text)
            except ValueError:
                daily_change = 0.0
            
            data.append({
                'stock_id': stock_code,
                'name': stock_name,
                'category': cells[4].get_text(strip=True) if len(cells) > 4 else '',
                'latest_week_change': latest_week_change,
                'total_change': total_change,
                'holding_pct': holding_pct,
                'close_price': close_price,
                'daily_change': daily_change,
            })
            
        except Exception as e:
            skipped += 1
            continue
    
    print(f"Parsed {len(data)} stocks, skipped {skipped} rows")
    return data


def update_stock_json(data_list, json_path='docs/data/stock_data.json'):
    """Update stock_data.json with Norway big holder data"""
    if not os.path.exists(json_path):
        print(f"ERROR: {json_path} not found")
        return False
    
    with open(json_path, 'r', encoding='utf-8') as f:
        stock_data = json.load(f)
    
    # Build lookup from Norway data
    norway_lookup = {d['stock_id']: d for d in data_list}
    
    updated = 0
    not_found = []
    
    for stock in stock_data.get('stocks', []):
        sid = stock.get('stock_id', '')
        if sid in norway_lookup:
            nd = norway_lookup[sid]
            stock['大戶週增減'] = nd['latest_week_change']
            stock['大戶總增減'] = nd['total_change']
            stock['大戶上週持有'] = nd['holding_pct']
            updated += 1
        else:
            not_found.append(sid)
    
    stock_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stock_data['data_date'] = datetime.now().strftime('%Y-%m-%d')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(stock_data, f, ensure_ascii=False, indent=2)
    
    print(f"Updated {updated}/{len(stock_data.get('stocks', []))} stocks with Norway data")
    if not_found:
        print(f"Not found in Norway data: {not_found[:20]}")
    
    return True


def main():
    """Main entry point"""
    print("=" * 60)
    print("Norway.twsthr.info Big Holder Fetcher (v2)")
    print("=" * 60)
    
    try:
        html = fetch_norway_html()
        data = parse_norway_data(html)
        
        # Save raw data for inspection
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        raw_path = f'data/norway_raw_{timestamp}.json'
        os.makedirs('data', exist_ok=True)
        with open(raw_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved raw data to {raw_path}")
        
        # Update stock_data.json
        json_path = 'docs/data/stock_data.json'
        if os.path.exists(json_path):
            update_stock_json(data, json_path)
        else:
            print(f"Warning: {json_path} not found, skipping update")
        
        print("\nDone!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
