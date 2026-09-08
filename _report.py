import json
import sys

sys.stdout = open('_report3.txt', 'w', encoding='utf-8')

with open('data/weekly_ranking.json', encoding='utf-8') as f:
    data = json.load(f)

otc_stocks = []
for th, info in data['thresholds'].items():
    for s in info['stocks']:
        if s.get('market') == '上櫃':
            otc_stocks.append(s)

print(f'OTC 上櫃股票共 {len(otc_stocks)} 档')
print()

if otc_stocks:
    def wow_key(x):
        v = x.get('wow_pct','0').replace('%','').replace('+','').replace('—','0')
        try:
            return float(v)
        except:
            return 0.0
    otc_stocks_sorted = sorted(otc_stocks, key=wow_key, reverse=True)[:20]
    print('=== OTC 上櫃大户周增幅 TOP20 ===')
    for s in otc_stocks_sorted:
        wow = s.get('wow_pct','—')
        streak = s.get('streak','—')
        signals = ','.join(s.get('signals',[]))
        print(f"  {s['code']} {s['name']}: 大户={s.get('big_holder_pct','—')}, 周增={wow}, 连增={streak}, 信号=[{signals}]")

# 所有股票中大户>80%且周增>0.5%的
print('\n=== 大户高度集中+周增显著 ===')
all_stocks = []
for th, info in data['thresholds'].items():
    for s in info['stocks']:
        all_stocks.append(s)

def bh_key(x):
    v = x.get('big_holder_pct','0').replace('%','')
    try:
        return float(v)
    except:
        return 0.0

high_bh = [s for s in all_stocks if bh_key(s) >= 80]
high_bh_sorted = sorted(high_bh, key=wow_key, reverse=True)[:15]
for s in high_bh_sorted:
    wow = s.get('wow_pct','—')
    streak = s.get('streak','—')
    signals = ','.join(s.get('signals',[]))
    print(f"  {s['code']} {s['name']}: 大户={s.get('big_holder_pct','—')}, 周增={wow}, 连增={streak}, 信号=[{signals}]")
