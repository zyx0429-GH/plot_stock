import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('data/screened_data.json', encoding='utf-8') as f:
    d = json.load(f)

print('UPDATE_TIME:', d.get('update_time'))
print('TOTAL:', d.get('total'))
print()

def fmt_stock(s):
    close = s.get('close', 0)
    chg = s.get('change_pct', 0)
    fn = s.get('foreign_net', 0)
    fdays = s.get('foreign_consecutive_days', 0)
    fdir = s.get('foreign_consecutive_buy')
    tn = s.get('trust_net', 0)
    tdays = s.get('trust_consecutive_days', 0)
    bh = s.get('big_holder_pct', 0)
    bhc = s.get('big_holder_change', 0)
    m = s.get('margin') or {}
    return (f"  {s['stock_id']} {s.get('stock_name','')}: "
            f"收{close} ({chg:+.2f}%) | "
            f"外資{'買' if fdir else '賣'}{abs(fn):,.0f}張/連{fdays}日 | "
            f"投信{tn:+,.0f}張/連{tdays}日 | "
            f"大戶{bh:.2f}%({bhc:+.2f}%) | "
            f"融資餘額{m.get('margin_balance', 0):,.0f}")

print('=' * 60)
print('DUAL CERTIFIED 00981A:', len(d['dual_certified']))
for s in d['dual_certified']:
    print(fmt_stock(s))

print()
print('DUAL CERTIFIED 00982A:', len(d['dual_certified_982a']))
for s in d['dual_certified_982a']:
    print(fmt_stock(s))

print()
print('TRIPLE CERTIFIED:', len(d['triple_certified']))
for s in d['triple_certified']:
    print(fmt_stock(s))

# Check for anomalies in dual/triple lists
print()
print('=' * 60)
print('ANOMALY CHECK (dual/triple certified):')
print('Criteria: foreign net SELL > 5M shares (5000張) OR |change_pct| > 5%')
anomalies = []
for group_name, group in [('981A', d['dual_certified']),
                          ('982A', d['dual_certified_982a']),
                          ('Triple', d['triple_certified'])]:
    for s in group:
        fn = s.get('foreign_net', 0)
        fdir = s.get('foreign_consecutive_buy')
        chg = abs(s.get('change_pct', 0))
        # foreign_net positive=buy; if fdir=False it's been selling days
        foreign_sell_today = (fn < -5000000)  # >500萬股淨賣超
        price_move = chg > 5
        if foreign_sell_today or price_move:
            reasons = []
            if foreign_sell_today:
                reasons.append(f"外資淨賣超{abs(fn)/1e6:.0f}百萬股")
            if price_move:
                reasons.append(f"漲跌{chg:.2f}%")
            anomalies.append((group_name, s['stock_id'], s.get('stock_name',''), s.get('close'), s.get('change_pct'), fn, reasons))

if anomalies:
    for g, sid, name, close, chg, fn, reasons in anomalies:
        print(f"  [{g}] {sid} {name} 收{close} ({chg:+.2f}%) 外資net={fn:,.0f} -> {'; '.join(reasons)}")
else:
    print('  No anomalies in dual/triple certified lists.')

# Also scan whole screened list for big foreign sells among holdings-ish names
print()
print('=' * 60)
print('TOP FOREIGN NET SELLS (all screened, today):')
all_sorted = sorted(d['screened'], key=lambda x: x.get('foreign_net', 0))
for s in all_sorted[:15]:
    print(f"  {s['stock_id']} {s.get('stock_name','')}: 外資net={s.get('foreign_net',0):+,.0f} 收{s.get('close')} ({s.get('change_pct',0):+.2f}%)")

print()
print('TOP GAINERS (all screened, today):')
gainers = sorted(d['screened'], key=lambda x: x.get('change_pct', 0), reverse=True)
for s in gainers[:15]:
    print(f"  {s['stock_id']} {s.get('stock_name','')}: {s.get('change_pct',0):+.2f}% 收{s.get('close')} 外資{s.get('foreign_net',0):+,.0f}")

print()
print('TOP LOSERS (all screened, today):')
for s in gainers[-10:]:
    print(f"  {s['stock_id']} {s.get('stock_name','')}: {s.get('change_pct',0):+.2f}% 收{s.get('close')} 外資{s.get('foreign_net',0):+,.0f}")
