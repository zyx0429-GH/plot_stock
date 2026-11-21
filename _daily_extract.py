# -*- coding: utf-8 -*-
import json, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

d = json.load(open('data/screened_data.json', encoding='utf-8'))
update = d.get('update_time')
print(f"更新時間: {update}  總篩選: {d.get('total')}")

def fmt_stock(s):
    m = s.get('margin', {}) or {}
    tech = s.get('technical', {}) or {}
    foreign_net = s.get('foreign_net', 0) or 0
    trust_net = s.get('trust_net', 0) or 0
    bh = s.get('big_holder_pct', 0) or 0
    bh_chg = s.get('big_holder_change', 0) or 0
    line = (f"{s['stock_id']} {s.get('stock_name','')} 收{s.get('close')} "
            f"({s.get('change_pct',0):+.2f}%) "
            f"外資{foreign_net/10000:+,.0f}萬 投信{trust_net/10000:+,.0f}萬 "
            f"大戶{bh:.2f}%({bh_chg:+.2f}) "
            f"融資{m.get('margin_change',0):+,.0f}張({m.get('margin_change_pct',0):+.1f}%) "
            f"券{m.get('short_change',0):+,.0f} "
            f"分數{s.get('score')}")
    return line

def show(title, key, limit=30):
    lst = d.get(key, []) or []
    print(f"\n=== {title} ({len(lst)}檔) ===")
    for s in lst[:limit]:
        print(fmt_stock(s))

show('雙重認證 00981A', 'dual_certified')
show('雙重認證 00982A', 'dual_certified_982a')
show('三重認證', 'triple_certified')

# 外資動向：從全部 screened 檔案取前段
allst = d.get('screened', []) or []
def net(s, k): return s.get(k, 0) or 0

print("\n=== 外資淨買超 Top10 (全部篩選股) ===")
for s in sorted(allst, key=lambda x: -net(x,'foreign_net'))[:10]:
    print(fmt_stock(s))
print("\n=== 外資淨賣超 Top10 (全部篩選股) ===")
for s in sorted(allst, key=lambda x: net(x,'foreign_net'))[:10]:
    print(fmt_stock(s))

# 融資異動
print("\n=== 融資增加 Top8 ===")
for s in sorted(allst, key=lambda x: -(x.get('margin',{}) or {}).get('margin_change',0))[:8]:
    print(fmt_stock(s))
print("\n=== 融資減少 Top8 ===")
for s in sorted(allst, key=lambda x: (x.get('margin',{}) or {}).get('margin_change',0))[:8]:
    print(fmt_stock(s))

# 異常檢查：外資淨賣超>500萬 或 漲跌>5%（以雙重/三重認證 + watchlist 為範圍）
print("\n=== 異常警示（雙重/三重認證 + watchlist）===")
watch_ids = {s.get('stock_id') for s in (d.get('watchlist') or [])}
pool = {}
for key in ('dual_certified','dual_certified_982a','triple_certified'):
    for s in d.get(key, []) or []:
        pool[s['stock_id']] = s
warned = 0
for sid, s in pool.items():
    fn = s.get('foreign_net',0) or 0
    chg = s.get('change_pct',0) or 0
    flags = []
    if fn < -5_000_000: flags.append(f"外資淨賣超{fn/10000:,.0f}萬")
    if abs(chg) > 5: flags.append(f"漲跌{chg:+.2f}%")
    if flags:
        warned += 1
        print(f"[{' | '.join(flags)}] {fmt_stock(s)}")
if warned == 0:
    print("無異常（認證榜單內無外資淨賣超>500萬且無漲跌>5%個股）")
