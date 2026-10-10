import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
d = json.load(open('data/screened_data.json', encoding='utf-8'))
raw = json.load(open('data/raw_data.json', encoding='utf-8'))

print('=== 外資/投信資料重複檢查 (前 8 檔比對) ===')
n_dup = 0
for sid, r in list(raw.items())[:400]:
    f = (r.get('foreign') or [{}])[-1]
    t = (r.get('trust') or [{}])[-1]
    if f and t and f.get('buy') == t.get('buy') and f.get('sell') == t.get('sell') and 'buy' in f:
        n_dup += 1
print(f'foreign==trust 相同筆數: {n_dup} / {len(raw)}')
for sid in ['2330', '8358', '3711', '2308']:
    r = raw.get(sid)
    if not r: continue
    f = (r.get('foreign') or [{}])[-1]
    t = (r.get('trust') or [{}])[-1]
    print(sid, 'foreign:', f, '| trust:', t)
print()
print('=== 融資異動 Top (margin_spike 前 15) ===')
for s in d.get('margin_spike', [])[:15]:
    mg = s.get('margin') or {}
    print(f"{s['stock_id']} {s.get('stock_name')} 收{s.get('close')} ({s.get('change_pct'):+.2f}%) 融資餘{mg.get('balance')} 增{mg.get('margin_change'):+}張 ({mg.get('margin_change_pct'):+.1f}%) 券餘{mg.get('short_balance')}")
print()
print('=== 全市場概況 ===')
print('screened:', len(d['screened']), '| 外資買:', len(d['foreign_buy']), '| 投信買:', len(d['trust_buy']), '| 多方:', len(d['bull_stocks']))
print('margin_spike:', len(d.get('margin_spike', [])), '| margin_top:', len(d.get('margin_top', [])), '| margin_decrease:', len(d.get('margin_decrease', [])))
print('short_increase:', len(d.get('short_increase', [])))
print()
print('=== 外資買超 Top 10 (張) ===')
fs = sorted(d['screened'], key=lambda x: -(x.get('foreign_net') or 0))[:10]
for s in fs:
    print(f"{s['stock_id']} {s.get('stock_name')} 外資{(s.get('foreign_net') or 0)/1000:+,.0f}張 ({s.get('change_pct'):+.2f}%)")
print()
print('=== 外資賣超 Top 10 (張) ===')
fs = sorted(d['screened'], key=lambda x: (x.get('foreign_net') or 0))[:10]
for s in fs:
    print(f"{s['stock_id']} {s.get('stock_name')} 外資{(s.get('foreign_net') or 0)/1000:+,.0f}張 ({s.get('change_pct'):+.2f}%)")
