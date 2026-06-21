#!/usr/bin/env python3
"""
將 norway 大戶籌碼數據轉換為 weekly_ranking.json 格式
供 generate_weekly_html.py 使用

數據來源: data/norway/all_stocks_weekly.json
"""

import json
import os
from datetime import datetime

NORWAY_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'norway', 'all_stocks_weekly.json')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'weekly_ranking.json')

# 門檻映射: threshold_code -> 門檻張數
THRESHOLD_MAP = {
    40: 200,
    30: 400,
    31: 400,
    50: 400,
    10: 1000,
}

def compute_streak(weekly_changes):
    """計算連續增持週數 (從最新週往回數)"""
    dates = sorted(weekly_changes.keys(), reverse=True)
    streak = 0
    for d in dates:
        v = weekly_changes[d]
        if v > 0:
            streak += 1
        else:
            break
    return streak

def compute_signals(r, streak, prev_week_change):
    """計算訊號標籤"""
    signals = []
    bh_pct = r.get('last_week_hold_pct', 0) or 0
    wow = r.get('latest_change', 0) or 0
    price_change = r.get('price_change', 0) or 0
    
    # 高波動警示: 週漲跌幅 >= 8%
    if abs(price_change) >= 8:
        signals.append('高波動警示')
    
    # 高度集中: 大戶佔比 >= 75%
    if bh_pct >= 75:
        signals.append('高度集中')
    
    # 流動性風險: 大戶佔比 >= 90%
    if bh_pct >= 90:
        signals.append('流動性風險')
    
    # 法人同向: 大戶佔比 >= 70% 且持續增持
    if bh_pct >= 70 and wow > 0:
        signals.append('法人同向')
    
    # 連增週數
    if streak >= 7:
        signals.append('連增7')
    elif streak >= 5:
        signals.append('連增5')
    elif streak >= 3:
        signals.append('連增3')
    
    # 加速: 本週 WoW >= 上週 * 1.5
    if prev_week_change is not None and prev_week_change > 0 and wow >= prev_week_change * 1.5:
        signals.append('加速')
    
    # 逆買: 股價跌幅 >= 3%, 大戶仍買超
    if price_change <= -3 and wow > 0:
        signals.append('逆買')
    
    # 事件驅動: 單週 WoW >= 3% 且無連增背景 (streak < 3)
    if wow >= 3 and streak < 3:
        signals.append('事件驅動')
    
    # 量價背離: 籌碼方向與股價方向相反
    if (wow > 0 and price_change < 0) or (wow < 0 and price_change > 0):
        signals.append('量價背離')
    
    # 內外共振: 連增 >= 3 週且股價同步上漲 >= 2%
    if streak >= 3 and price_change >= 2:
        signals.append('內外共振')
    
    # 久盤吸籌: 連增 >= 5 週但股價漲幅 < 3%
    if streak >= 5 and price_change < 3:
        signals.append('久盤吸籌')
    
    # 籌碼回補: 上週賣超後本週轉正
    if prev_week_change is not None and prev_week_change < 0 and wow > 0:
        signals.append('籌碼回補')
    
    return signals

def convert():
    with open(NORWAY_PATH, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    # 按門檻分組
    threshold_groups = {'200': [], '400': [], '1000': []}
    for r in records:
        tc = r.get('threshold_code')
        threshold = THRESHOLD_MAP.get(tc)
        if not threshold:
            continue
        key = str(threshold)
        
        weekly_changes = r.get('weekly_changes', {})
        dates = sorted(weekly_changes.keys(), reverse=True)
        streak = compute_streak(weekly_changes)
        
        # 上週變化 (用於加速、籌碼回補判斷)
        prev_week_change = None
        if len(dates) >= 2:
            prev_week_change = weekly_changes.get(dates[1])
        
        signals = compute_signals(r, streak, prev_week_change)
        
        # 判斷是否為新進榜 (需要前週數據, 簡化: 若上週變化為0或前週無數據且本週有顯著變化)
        # 這裡簡化: 若上週變化為0或極小, 且本週變化顯著, 標記為新進榜
        if prev_week_change is not None and abs(prev_week_change) < 0.05 and wow > 0.5:
            signals.append('新進榜')
        
        wow = r.get('latest_change', 0) or 0
        price_change = r.get('price_change', 0) or 0
        
        threshold_groups[key].append({
            'code': str(r.get('stock_code', '')),
            'name': r.get('stock_name', ''),
            'market': '上市' if int(r.get('stock_code', 0)) < 6000 else '上櫃',
            'industry': r.get('category', ''),
            'price': r.get('close_price', 0),
            'change_pct': f'{price_change:+.2f}%',
            'big_holder_pct': f'{r.get("last_week_hold_pct", 0):.2f}%',
            'wow_pct': f'{wow:+.2f}%',
            'streak': f'↑{streak}週' if streak > 0 else '',
            'rank_change': 'NEW' if '新進榜' in signals else '',
            'signals': signals,
        })
    
    # 對每個門檻排序 (按 wow% 由高到低)
    for key in threshold_groups:
        threshold_groups[key].sort(key=lambda x: float(x['wow_pct'].replace('%', '').replace('+', '')), reverse=True)
        # 添加排名
        for i, s in enumerate(threshold_groups[key], 1):
            s['rank'] = i
    
    # 計算統計數據
    all_data = {}
    signal_counts = {}
    for key in ['200', '400', '1000']:
        stocks = threshold_groups[key]
        n_up = sum(1 for s in stocks if float(s['wow_pct'].replace('%', '').replace('+', '')) > 0)
        n_down = sum(1 for s in stocks if float(s['wow_pct'].replace('%', '').replace('+', '')) < 0)
        n_flat = len(stocks) - n_up - n_down
        n_accel = sum(1 for s in stocks if '加速' in s['signals'])
        n_new = sum(1 for s in stocks if '新進榜' in s['signals'])
        n_streak5 = sum(1 for s in stocks if '連增5' in s['signals'] or '連增7' in s['signals'])
        
        all_data[key] = {
            'stocks': stocks[:100],  # 只取前100
            'count': len(stocks),
            'stats': {
                'nUp': n_up,
                'nDown': n_down,
                'nFlat': n_flat,
                'nAll': len(stocks),
                'nCt': 0,  # 未計算
                'nAccel': n_accel,
                'nNewG': n_new,
                'nStreak5': n_streak5,
            }
        }
        
        for s in stocks:
            for sig in s['signals']:
                signal_counts[sig] = signal_counts.get(sig, 0) + 1
    
    result = {
        'source': 'norway.twsthr.info/StockHoldersTopWeek.aspx',
        'fetched_at': datetime.now().isoformat(),
        'thresholds': all_data,
        'signal_counts': signal_counts,
    }
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Converted {len(records)} norway records to weekly_ranking.json")
    for key in ['200', '400', '1000']:
        print(f"  Threshold {key}: {len(all_data[key]['stocks'])} stocks")
    print(f"  Signals: {dict(sorted(signal_counts.items(), key=lambda x: -x[1])[:10])}")

if __name__ == '__main__':
    convert()
