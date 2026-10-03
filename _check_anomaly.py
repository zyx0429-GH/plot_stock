# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('data/raw_data.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

holds = ['2327','6213','1815','2409','3006','2377','6239','4967','2313']
print(f"{'code':<6}{'name':<10}{'close':>8}{'chg%':>8}{'foreign(1000)':>14}{'foreign(10k TWD)':>16}{'trust(1000)':>12}{'margin_bal':>10}{'margin_chg':>10}{'short_chg':>10}")
anoms = []
for sid in holds:
    d = raw.get(sid)
    if not d:
        print(sid, 'NO DATA')
        continue
    i = d['info']
    fn = i['foreign_net']
    close = i['close']
    fw = fn * close / 10000  # 萬元
    m = d['margin'][-1] if d.get('margin') else {}
    print(f"{sid:<6}{i['stock_name']:<10}{close:>8}{i['change_pct']:>8.2f}{fn/1000:>14.0f}{fw:>16.0f}{i['trust_net']/1000:>12.0f}{str(m.get('margin_balance','')):>10}{str(m.get('margin_change','')):>10}{str(m.get('short_change','')):>10}")
    if fn < 0 and abs(fn) * close > 5000000:
        anoms.append((sid, i['stock_name'], 'foreign sell > 500萬元', round(fw)))
    if abs(i['change_pct']) > 5:
        anoms.append((sid, i['stock_name'], 'price move > 5%', i['change_pct']))

print()
print('ANOMALIES:', anoms if anoms else 'none')
