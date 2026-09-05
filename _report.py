import json
import sys

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

data = json.load(open('data/screened_data.json', encoding='utf-8'))

dual981 = [s for s in data['screened'] if s.get('dual_certified')]
dual982 = [s for s in data['screened'] if s.get('dual_certified_982a')]
triple = [s for s in data['screened'] if s.get('triple_certified')]

print('=== 00981A Dual Certified ===')
for s in dual981:
    print(f"{s['stock_id']} {s['stock_name']} | 收{s['close']} | 漲{s['change_pct']}% | 外資{s['foreign_net']/10000:.0f}萬 | 融資{s['margin']['balance']}")

print('\n=== 00982A Dual Certified ===')
for s in dual982:
    print(f"{s['stock_id']} {s['stock_name']} | 收{s['close']} | 漲{s['change_pct']}% | 外資{s['foreign_net']/10000:.0f}萬 | 融資{s['margin']['balance']}")

print('\n=== Triple Certified ===')
for s in triple:
    print(f"{s['stock_id']} {s['stock_name']} | 收{s['close']} | 漲{s['change_pct']}% | 外資{s['foreign_net']/10000:.0f}萬")

print('\n=== Anomalies (外資淨賣超>500萬 或 漲跌>5%) ===')
anomalies = []
for s in data['screened']:
    foreign_net = s['foreign_net']
    change_pct = s['change_pct']
    if foreign_net < -5000000 or abs(change_pct) > 5:
        direction = "賣超" if foreign_net < 0 else "買超"
        anomalies.append(f"{s['stock_id']} {s['stock_name']} | 收{s['close']} | 漲{change_pct}% | 外資{direction}{abs(foreign_net)/10000:.0f}萬 | 融資餘額{s['margin']['balance']}")
        
if anomalies:
    for a in anomalies:
        print(a)
else:
    print('無異常')
