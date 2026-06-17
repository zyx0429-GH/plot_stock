import json
import os
from collections import Counter

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with open('data/screened_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

screened = data.get('screened', [])

# Count how many top lists each stock appears in
stock_counts = Counter()
for key in ['foreign_buy', 'trust_buy', 'bull_stocks', 'dual_certified', 
            'margin_spike', 'margin_top', 'short_ratio_top', 'margin_decrease', 'short_increase']:
    for s in data.get(key, []):
        stock_counts[s['stock_id']] += 1

# Sort by score (ascending) and count
results = []
for s in screened:
    sid = s['stock_id']
    score = s.get('score', 0)
    count = stock_counts.get(sid, 0)
    big_pct = s.get('big_holder_pct', 0) or 0
    change_pct = s.get('change_pct', 0) or 0
    trend = (s.get('technical', {}) or {}).get('trend', '')
    results.append({
        'sid': sid, 'name': s['stock_name'], 'score': score, 
        'count': count, 'big_pct': big_pct, 'change_pct': change_pct,
        'trend': trend
    })

# Sort by score ascending (weakest first)
results.sort(key=lambda x: (x['score'], x['count']))

print("=== Lowest Score Stocks (Potential Removal Candidates) ===")
for r in results[:20]:
    flag = "XX" if r['count'] <= 1 else "!!"
    print(f"{flag} {r['sid']} {r['name']:<8} | Score:{r['score']} | Lists:{r['count']} | Big%:{r['big_pct']:.1f}% | Chg:{r['change_pct']:+.2f}% | {r['trend']}")

# Sector counts
sector_map = {
    'Semiconductor': ['2330','2454','2303','5347','2344','3006','4967','6770','3016','6805','3443','4919','4961','4966','6510','6415','6257','3008','3045','3665','6494','6515','6669','8086'],
    'IC Design': ['2454','2357','2337','3006','3443','4919','4961','4966','4967','6510','6415','6257','3665','6669','8086'],
    'Foundry': ['2330','2303','5347','6770','6805'],
    'Packaging': ['2344','3016','6239','3008','3045','6515'],
    'Memory': ['2344','2408','3006','6770'],
    'AI Server/Assembly': ['2317','2324','2356','2376','2382','3231','3661','6669','2404'],
    'Passive Components': ['2327','2472','2478','2492','6173','8042','8043','1815','3026','2375','3090','6207'],
    'PCB': ['2313','2355','2368','2383','3037','6213','6274','8046'],
    'Panel/Opto': ['2409','3481'],
    'Electronics Parts': ['1590','2352','2428','2439','2449','2481','3017','3217','3264','3356','3357','3376','3450','3498','3535','3537','3624','3680','5274','5291','5328','5425','5439','6104','6127','6147','6182','6187','6191','6207','6223','6257','6261','6271','6284','6462','6485','6727','8040','8046','8091','8096','8150','8210','8289','8358','8996'],
    'Telecom': ['2345','5274','5328','6284','8096','8289'],
    'Financial': ['2881','2882','2850','2880','2883','2885','2886','2887','2890','2892'],
    'Food': ['1216','3005'],
    'Chemical': ['1301','1319','2002','1605'],
    'Steel': ['2030','2031','2032','2033','2034','2023','2025'],
    'Auto': ['2634'],
    'Biotech': ['6182'],
    'SiC': ['3707','8261'],
    'Aerospace': ['2634'],
    'Satellite': ['6821'],
    'ETF': ['00981A']
}

sector_counts = {}
for r in results:
    for sector, codes in sector_map.items():
        if r['sid'] in codes:
            if sector not in sector_counts:
                sector_counts[sector] = []
            sector_counts[sector].append(r)
            break

print("\n=== Sector Overload Check ===")
for sector, stocks in sorted(sector_counts.items(), key=lambda x: -len(x[1])):
    if len(stocks) > 5:
        print(f"\n{sector}: {len(stocks)} stocks")
        stocks_sorted = sorted(stocks, key=lambda x: x['score'])
        for s in stocks_sorted[:3]:
            print(f"  !! {s['sid']} {s['name']:<8} Score:{s['score']} Chg:{s['change_pct']:+.2f}%")
