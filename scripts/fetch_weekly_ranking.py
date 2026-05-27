#!/usr/bin/env python3
"""
抓取 fortune-fred.github.io/plot_stock/weekly_ranking.html 的数据
并解析为结构化 JSON，供 zyx0429-GH/plot_stock 使用
"""

import requests
import re
import json
from html import unescape
from datetime import datetime
import os

URL = 'https://fortune-fred.github.io/plot_stock/weekly_ranking.html'
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs')


def fetch_page():
    resp = requests.get(URL, timeout=60)
    resp.raise_for_status()
    return resp.text


def extract_quoted_string(s, start_idx):
    """Extract a double-quoted string starting at start_idx, handling \" and \\u escapes"""
    if s[start_idx] != '"':
        return None
    i = start_idx + 1
    result = []
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            next_c = s[i + 1]
            if next_c == '"':
                result.append('"')
                i += 2
            elif next_c == '\\':
                result.append('\\')
                i += 2
            elif next_c == 'n':
                result.append('\n')
                i += 2
            elif next_c == 'u' and i + 5 < len(s):
                # Unicode escape \uXXXX
                hex_str = s[i+2:i+6]
                try:
                    result.append(chr(int(hex_str, 16)))
                except ValueError:
                    result.append('\\u' + hex_str)
                i += 6
            else:
                result.append(next_c)
                i += 2
        elif c == '"':
            return ''.join(result), i + 1
        else:
            result.append(c)
            i += 1
    return None


def extract_tbl(text):
    """Extract the TBL object - find all threshold entries"""
    result = {}
    for threshold in ['200', '400', '600', '800', '1000']:
        pattern = f"'{threshold}':"
        idx = text.find(pattern)
        if idx == -1:
            continue
        # Find g: after this threshold
        g_idx = text.find('g:', idx)
        if g_idx == -1:
            continue
        quote_idx = text.find('"', g_idx)
        if quote_idx == -1:
            continue
        html, end_pos = extract_quoted_string(text, quote_idx)
        if html:
            result[threshold] = html
    return result


def parse_html_table(html):
    """Parse HTML table rows into structured data"""
    rows = []
    full_trs = re.findall(r'<tr[^>]*data-tags="([^"]*)"[^>]*>(.*?)</tr>', html, re.DOTALL)
    for tags_str, tr_content in full_trs:
        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        cells = []
        for td_match in re.finditer(r'(<td[^>]*>)(.*?)(</td>)', tr_content, re.DOTALL):
            td_html = td_match.group(2)
            full_td = td_match.group(0)
            # Get text
            text = re.sub(r'<[^>]+>', '', td_html).strip()
            # Get data-v
            dv_match = re.search(r'data-v="([^"]*)"', full_td)
            data_v = dv_match.group(1) if dv_match else None
            cells.append({'text': text, 'data_v': data_v, 'html': td_html})
        rows.append({'tags': tags, 'cells': cells})
    return rows


def extract_stock_info(rows):
    """Extract stock info from parsed rows"""
    stocks = []
    for row in rows:
        cells = row['cells']
        tags = row['tags']
        if len(cells) < 5:
            continue

        stock_code = None
        stock_name = None
        for cell in cells[:3]:
            text = cell['text']
            # Stock code is typically a 4-5 digit number
            m = re.search(r'(\d{4,5})', text)
            if m:
                stock_code = m.group(1)
                # Try to extract name from <span class="nm"> in the original td HTML
                td_html = cell.get('html', '')
                nm_match = re.search(r'<span class="nm">(.*?)</span>', td_html, re.DOTALL)
                if nm_match:
                    stock_name = re.sub(r'<[^>]+>', '', nm_match.group(1)).strip()
                if not stock_name:
                    # Fallback: try to extract name from text after code
                    remaining = text[len(stock_code):].strip()
                    # Remove known suffixes
                    for suffix in ['上市', '上櫃']:
                        remaining = remaining.replace(suffix, '')
                    stock_name = remaining[:4].strip()
                break

        if not stock_code:
            continue

        # Separate signal tags from market/industry
        signal_tags = []
        market = ''
        industry = ''
        for t in tags:
            if t in ['上市', '上櫃']:
                market = t
            elif t.startswith('ind:'):
                industry = t.replace('ind:', '')
            elif t.startswith('連增'):
                signal_tags.append(t)
            else:
                signal_tags.append(t)

        # Extract numeric data from cells
        # Typical layout: rank, rank_change, stock_info, price, change%, big_holder%, wow%, streak
        cell_texts = [c['text'] for c in cells]
        rank = cell_texts[0] if len(cell_texts) > 0 else ''
        rank_change = cell_texts[1] if len(cell_texts) > 1 else ''
        price = cell_texts[3] if len(cell_texts) > 3 else ''
        change_pct = cell_texts[4] if len(cell_texts) > 4 else ''
        big_holder_pct = cell_texts[5] if len(cell_texts) > 5 else ''
        wow_pct = cell_texts[6] if len(cell_texts) > 6 else ''
        streak = cell_texts[7] if len(cell_texts) > 7 else ''

        stocks.append({
            'code': stock_code,
            'name': stock_name or '',
            'market': market,
            'industry': industry,
            'signals': signal_tags,
            'rank': rank,
            'rank_change': rank_change,
            'price': price,
            'change_pct': change_pct,
            'big_holder_pct': big_holder_pct,
            'wow_pct': wow_pct,
            'streak': streak,
        })
    return stocks


def parse_datasets(text):
    """Extract summary stats from DATASETS"""
    result = {}
    for threshold in ['200', '400', '600', '800', '1000']:
        pattern = f"'{threshold}':"
        idx = text.find(pattern)
        if idx == -1:
            continue
        block_start = text.find('{', idx)
        block_end = text.find('}', block_start)
        if block_start == -1 or block_end == -1:
            continue
        entry = text[block_start:block_end+1]
        stats = {}
        for key in ['nUp', 'nDown', 'nFlat', 'nAll', 'nCt', 'nAccel', 'nNewG', 'nStreak5']:
            km = re.search(rf'\b{key}\s*:\s*(\d+)', entry)
            if km:
                stats[key] = int(km.group(1))
        result[threshold] = stats
    return result


def main():
    print("Fetching weekly_ranking.html...")
    text = fetch_page()

    print("Extracting TBL data...")
    tbl = extract_tbl(text)
    print(f"Found thresholds: {list(tbl.keys())}")

    print("Extracting DATASETS stats...")
    datasets = parse_datasets(text)

    all_data = {}
    for threshold, html in tbl.items():
        print(f"Parsing threshold {threshold}...")
        rows = parse_html_table(html)
        stocks = extract_stock_info(rows)
        all_data[threshold] = {
            'stocks': stocks,
            'count': len(stocks),
            'stats': datasets.get(threshold, {})
        }
        print(f"  Found {len(stocks)} stocks")

    # Count signals
    signal_counts = {}
    for td in all_data.values():
        for stock in td['stocks']:
            for sig in stock['signals']:
                signal_counts[sig] = signal_counts.get(sig, 0) + 1

    result = {
        'source': 'fortune-fred.github.io/plot_stock/weekly_ranking.html',
        'fetched_at': datetime.now().isoformat(),
        'thresholds': all_data,
        'signal_counts': signal_counts
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    json_path = os.path.join(OUTPUT_DIR, 'weekly_ranking.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON to {json_path}")

    return result


if __name__ == '__main__':
    main()
