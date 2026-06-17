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

# Sort by score ascending
results.sort(key=lambda x: (x['score'], x['count']))

lines = []
lines.append("=== 最低分股票 (潛在移除候選) ===\n")
for r in results[:20]:
    flag = "[移除]" if r['count'] <= 1 else "[觀察]"
    lines.append(f"{flag} {r['sid']} {r['name']:<8} | 評分:{r['score']} | 入榜:{r['count']} | 大戶%:{r['big_pct']:.1f}% | 漲跌:{r['change_pct']:+.2f}% | {r['trend']}\n")

# Removal recommendations
lines.append("\n=== 移除建議 ===\n")
lines.append("優先移除 (評分<=30 且大戶%=0):\n")
for r in results[:10]:
    if r['score'] <= 30 and r['big_pct'] == 0:
        lines.append(f"  - {r['sid']} {r['name']} (評分:{r['score']}, 漲跌:{r['change_pct']:+.2f}%)\n")

lines.append("\n族群過度集中 (同族群>5檔, 建議精簡):\n")
sector_map = {
    '電子零組件': ['1590','2352','2428','2439','2449','2481','3017','3217','3264','3356','3357','3376','3450','3498','3535','3537','3624','3680','5274','5291','5328','5425','5439','6104','6127','6147','6182','6187','6191','6207','6223','6257','6261','6271','6284','6462','6485','6727','8040','8046','8091','8096','8150','8210','8289','8358','8996'],
    '半導體': ['2330','2454','2303','5347','2344','3006','4967','6770','3016','6805','3443','4919','4961','4966','6510','6415','6257','3008','3045','3665','6494','6515','6669','8086'],
    '金融保險': ['2881','2882','2850','2880','2883','2885','2886','2887','2890','2892'],
    'PCB': ['2313','2355','2368','2383','3037','6213','6274','8046'],
    'AI伺服器/電子組裝': ['2317','2324','2356','2376','2382','3231','3661','6669','2404'],
    '被動元件': ['2327','2472','2478','2492','6173','8042','8043','1815','3026','2375','3090','6207'],
    '鋼鐵金屬': ['2030','2031','2032','2033','2034','2023','2025'],
}

for sector, codes in sector_map.items():
    sector_stocks = [r for r in results if r['sid'] in codes]
    if len(sector_stocks) > 5:
        lines.append(f"\n{sector}: {len(sector_stocks)}檔 -> 建議保留5-8檔\n")
        sector_stocks.sort(key=lambda x: x['score'])
        keep = sector_stocks[:8]
        remove = sector_stocks[8:]
        lines.append(f"  保留 (評分最高): {[s['sid'] for s in keep]}\n")
        if remove:
            lines.append(f"  移除 (評分較低): {[s['sid'] for s in remove]}\n")

with open('removal_recommendations.txt', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Saved to removal_recommendations.txt")
