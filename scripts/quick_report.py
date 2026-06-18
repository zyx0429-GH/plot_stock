# -*- coding: utf-8 -*-
import json

with open('data/screened_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"總股票數: {len(data['screened'])}")
print(f"雙重認證數: {len(data['dual_certified'])}")
print()

# 雙重認證榜單
print("=== 雙重認證榜單 ===")
for s in data['dual_certified'][:10]:
    sign = "+" if s['change_pct'] >= 0 else ""
    print(f"{s['stock_id']} {s['stock_name']} 收{s['close']} {sign}{s['change_pct']}% 外資{s['foreign_net']:+,.0f} 大戶{s['big_holder_pct']}% 週增{s['big_holder_change']:+.2f}% 評分{s['score']}")

print()

# 外資買超前10
print("=== 外資買超 TOP 10 ===")
foreign_buy = [s for s in data['screened'] if s['foreign_net'] > 0]
foreign_buy.sort(key=lambda x: x['foreign_net'], reverse=True)
for s in foreign_buy[:10]:
    sign = "+" if s['change_pct'] >= 0 else ""
    print(f"{s['stock_id']} {s['stock_name']} 收{s['close']} {sign}{s['change_pct']}% 外資+{s['foreign_net']:,}")

print()

# 外資賣超前10
print("=== 外資賣超 TOP 10 ===")
foreign_sell = [s for s in data['screened'] if s['foreign_net'] < 0]
foreign_sell.sort(key=lambda x: x['foreign_net'])
for s in foreign_sell[:10]:
    sign = "+" if s['change_pct'] >= 0 else ""
    print(f"{s['stock_id']} {s['stock_name']} 收{s['close']} {sign}{s['change_pct']}% 外資{s['foreign_net']:,}")

print()

# 融資異動
print("=== 融資異動 (>20%) ===")
margin_spike = []
for s in data['screened']:
    m = s.get('margin')
    if m is None:
        continue
    if abs(m.get('margin_change_pct', 0)) > 20 or abs(m.get('short_change_pct', 0)) > 20:
        margin_spike.append(s)
margin_spike.sort(key=lambda x: abs(x.get('margin', {}).get('margin_change_pct', 0) or 0), reverse=True)
for s in margin_spike[:10]:
    m = s.get('margin', {})
    print(f"{s['stock_id']} {s['stock_name']} 融資{m.get('margin_change_pct', 0):+.1f}% 融券{m.get('short_change_pct', 0):+.1f}% 券資比{m.get('ratio', 0):.2%}")

print()

# 智董持倉
print("=== 智董持倉股 ===")
holdings = ['2327', '3006', '6213', '1815', '2409', '6239', '4967', '2377', '2313']
for s in data['screened']:
    if s['stock_id'] in holdings:
        sign = "+" if s['change_pct'] >= 0 else ""
        print(f"{s['stock_id']} {s['stock_name']} 收{s['close']} {sign}{s['change_pct']}% 外資{s['foreign_net']:+,} 大戶{s['big_holder_pct']}% 趨勢{s['technical']['trend']}")
