import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
d = json.load(open('data/screened_data.json', encoding='utf-8'))
raw = json.load(open('data/raw_data.json', encoding='utf-8'))

def w(sid):
    return next((x for x in d['screened'] if x['stock_id'] == sid), None)

def fmt(s):
    fz = (s.get('foreign_net') or 0) / 1000
    tz = (s.get('trust_net') or 0) / 1000
    chg = s.get('change_pct')
    chgs = f"{chg:+.2f}%" if isinstance(chg, (int, float)) else str(chg)
    return (f"{s['stock_id']} {s.get('stock_name')} 收{s.get('close')} ({chgs}) "
            f"外資{fz:+,.0f}張 投信{tz:+,.0f}張 "
            f"外連買{s.get('foreign_consecutive_days')}日 投連買{s.get('trust_consecutive_days')}日")

print('=== 00981A 雙認證榜單 (7檔) ===')
for s in d['dual_certified']:
    print(fmt(s))
print()
print('=== 00982A 雙認證榜單 (21檔) ===')
for s in d['dual_certified_982a']:
    print(fmt(s))
print()
print('=== 三重認證 (28檔) ===')
print(' '.join(f"{s['stock_id']}({s.get('change_pct'):+.1f}%)" if isinstance(s.get('change_pct'), (int,float)) else s['stock_id'] for s in d['triple_certified']))
print()
m = w('8358')
print('=== 金居 8358 (唯一持倉股) ===')
if m:
    print(json.dumps(m, ensure_ascii=False, indent=1)[:2000])
else:
    print('不在 screened 名單')
print()
r = raw.get('8358')
if r:
    print('--- raw 8358 keys:', list(r.keys()))
    print(json.dumps(r, ensure_ascii=False, indent=1)[:2000])
