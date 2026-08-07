import json, sys

with open('data/screened_data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

stocks = d.get('screened', d.get('stocks', []))

# 雙重/三重認證
print("=== 雙重/三重認證榜單 ===")
for s in stocks:
    dc = s.get('dual_certified', '')
    tc = s.get('triple_certified', False)
    if dc or tc:
        print(f"{s['stock_id']} {s['stock_name']} | 收盤:{s.get('close')} 漲跌:{s.get('change_pct')}% | 外資:{s.get('foreign_net')} | 融資餘額:{s.get('margin_balance')} 融資增減:{s.get('margin_change')} | 大戶:{s.get('big_holder_pct')}% | 認證:{'三重' if tc else dc}")

# 外資淨賣超 > 500萬 (持倉股中)
print("\n=== 外資淨賣超 > 500萬 (ETF持倉股) ===")
etf_set = set()
for s in d['stocks']:
    if s['stock_id'] in ('00981A', '00982A'):
        continue
    # 判斷是否為持倉股 ( dual_certified 或 watchlist )
    if s.get('dual_certified') or s.get('watchlist', False):
        fn = s.get('foreign_net', 0)
        if isinstance(fn, (int, float)) and fn < -500:
            print(f"{s['stock_id']} {s['stock_name']} | 外資淨賣超: {fn} | 收盤:{s.get('close')} 漲跌:{s.get('change_pct')}%")

# 股價漲跌 > 5%
print("\n=== 股價漲跌 > 5% (ETF持倉股) ===")
for s in d['stocks']:
    if s['stock_id'] in ('00981A', '00982A'):
        continue
    if s.get('dual_certified') or s.get('watchlist', False):
        cp = s.get('change_pct', 0)
        if isinstance(cp, (int, float)) and abs(cp) > 5:
            direction = '漲' if cp > 0 else '跌'
            print(f"{s['stock_id']} {s['stock_name']} | {direction}:{cp}% | 收盤:{s.get('close')} | 外資:{s.get('foreign_net')} | 融資餘額:{s.get('margin_balance')}")

# 融資異動 (大幅增減)
print("\n=== 融資異動 (增減絕對值 > 200) ===")
for s in d['stocks']:
    if s['stock_id'] in ('00981A', '00982A'):
        continue
    if s.get('dual_certified') or s.get('watchlist', False):
        mc = s.get('margin_change', 0)
        if isinstance(mc, (int, float)) and abs(mc) > 200:
            direction = '增加' if mc > 0 else '減少'
            print(f"{s['stock_id']} {s['stock_name']} | 融資{direction}:{mc} | 收盤:{s.get('close')} 漲跌:{s.get('change_pct')}% | 外資:{s.get('foreign_net')}")

print("\n=== 00981A/00982A 本身 ===")
for s in d['stocks']:
    if s['stock_id'] in ('00981A', '00982A'):
        print(f"{s['stock_id']} {s['stock_name']} | 收盤:{s.get('close')} 漲跌:{s.get('change_pct')}% | 外資:{s.get('foreign_net')} | 融資餘額:{s.get('margin_balance')} 融資增減:{s.get('margin_change')}")
