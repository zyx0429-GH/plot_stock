# -*- coding: utf-8 -*-
"""Daily report extraction for dual-certified lists + anomaly check."""
import json, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

d = json.load(open('data/screened_data.json', encoding='utf-8'))
screened = d['screened']

def fmt_wan(x):
    if x is None: return 'n/a'
    return f"{x/10000:+.1f}萬"

print("=" * 60)
print("00981A 雙重認證榜單")
print("=" * 60)
lst = [s for s in screened if s.get('dual_certified')]
lst.sort(key=lambda s: s.get('score', 0), reverse=True)
for s in lst:
    m = s.get('margin') or {}
    print(f"{s['stock_id']} {s['stock_name']} 收{s['close']} ({s['change_pct']:+.2f}%) "
          f"外資{fmt_wan(s.get('foreign_net'))} 投信{fmt_wan(s.get('trust_net'))} "
          f"大戶{s.get('big_holder_pct')}%({s.get('big_holder_change'):+.2f}) "
          f"融資{m.get('margin_change_pct')}% 券{m.get('short_change_pct')}% score{s.get('score')}")

print()
print("=" * 60)
print("00982A 雙重認證榜單")
print("=" * 60)
lst2 = [s for s in screened if s.get('dual_certified_982a')]
lst2.sort(key=lambda s: s.get('score', 0), reverse=True)
for s in lst2:
    m = s.get('margin') or {}
    print(f"{s['stock_id']} {s['stock_name']} 收{s['close']} ({s['change_pct']:+.2f}%) "
          f"外資{fmt_wan(s.get('foreign_net'))} 投信{fmt_wan(s.get('trust_net'))} "
          f"大戶{s.get('big_holder_pct')}%({s.get('big_holder_change'):+.2f}) "
          f"融資{m.get('margin_change_pct')}% 券{m.get('short_change_pct')}% score{s.get('score')}")

print()
print("=" * 60)
print("三重認證")
print("=" * 60)
for s in sorted([s for s in screened if s.get('triple_certified')], key=lambda s: s.get('score', 0), reverse=True):
    print(f"{s['stock_id']} {s['stock_name']} 收{s['close']} ({s['change_pct']:+.2f}%) 外資{fmt_wan(s.get('foreign_net'))} score{s.get('score')}")

print()
print("=" * 60)
print("異常檢查（雙認證清單內）")
print("=" * 60)
ANOM_SELL = -5_000_000   # 外資淨賣超 > 500萬股
ANOM_PCT = 5.0
for tag, group in (("00981A", lst), ("00982A", lst2)):
    for s in group:
        flags = []
        fn = s.get('foreign_net') or 0
        if fn < ANOM_SELL:
            flags.append(f"外資淨賣超{fmt_wan(fn)}股")
        if abs(s['change_pct']) > ANOM_PCT:
            flags.append(f"漲跌{s['change_pct']:+.2f}%")
        if flags:
            m = s.get('margin') or {}
            print(f"[{tag}] {s['stock_id']} {s['stock_name']}: {'; '.join(flags)} | 外資連買{s.get('foreign_consecutive_days')}天 投信連買{s.get('trust_consecutive_days')}天 融資{m.get('margin_change_pct')}%")

print()
print("=" * 60)
print("外資淨賣超前10（全部篩選股）")
print("=" * 60)
allsell = sorted(screened, key=lambda s: s.get('foreign_net') or 0)[:10]
for s in allsell:
    print(f"{s['stock_id']} {s['stock_name']} 外資{fmt_wan(s.get('foreign_net'))} ({s['change_pct']:+.2f}%)")

print()
print("=" * 60)
print("融資異動 top10（增幅%）")
print("=" * 60)
bymargin = sorted([s for s in screened if (s.get('margin') or {}).get('margin_change_pct') is not None],
                  key=lambda s: s['margin']['margin_change_pct'], reverse=True)[:10]
for s in bymargin:
    m = s['margin']
    print(f"{s['stock_id']} {s['stock_name']} 融資{m['margin_change_pct']:+.2f}% ({m.get('margin_change')}張) ({s['change_pct']:+.2f}%)")

# date check
raw = json.load(open('data/raw_data.json', encoding='utf-8'))
keys = list(raw.keys())[:3]
sample = raw[keys[0]]
print()
print("資料日期樣本:", keys[0])
for k in ('date', 'trade_date', 'last_update'):
    if k in sample: print(k, '=', sample[k])
