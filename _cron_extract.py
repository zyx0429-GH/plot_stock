# -*- coding: utf-8 -*-
import json

with open('data/screened_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

stocks = data.get('screened', [])
print(f"update_time: {data.get('update_time','')}")
print(f"total: {data.get('total','')}")
print()

def fmt_stock(s):
    code = s.get('stock_id', '')
    name = s.get('stock_name', '')
    close = s.get('close', 0) or 0
    chg = s.get('change_pct', 0) or 0
    fi = s.get('foreign_net', 0) or 0
    tr = s.get('trust_net', 0) or 0
    bp = s.get('big_holder_pct', 0) or 0
    bc = s.get('big_holder_change', 0) or 0
    m = s.get('margin', {})
    mbal_chg = m.get('balance_change', 0) or 0 if isinstance(m, dict) else 0
    fi_days = s.get('foreign_consecutive_days', 0) or 0
    tr_days = s.get('trust_consecutive_days', 0) or 0
    flag = ''
    if fi < -5000000:
        flag += ' [ALERT:外資賣超>500萬]'
    if abs(chg) > 5:
        flag += ' [ALERT:漲跌>5%]'
    return f"  {code} {name} | 收{close} {chg:+.2f}% | 外資淨{fi:+,.0f}({fi_days}日) | 投信淨{tr:+,.0f}({tr_days}日) | 大戶{bp:.2f}%({bc:+.3f}) | 融資變{mbal_chg:+,.0f}{flag}"

# === Dual certified ===
print('=== 00981A 雙重認證 ===')
dual981 = data.get('dual_certified', [])
for s in dual981:
    print(fmt_stock(s))

print()
print('=== 00982A 雙重認證 ===')
dual982 = data.get('dual_certified_982a', [])
for s in dual982:
    print(fmt_stock(s))

print()
print('=== 三重認證 ===')
triple = data.get('triple_certified', [])
for s in triple:
    print(fmt_stock(s))

# === Anomaly scan ===
print()
print('=== 異常掃描（全部持股）===')
anomalies = []
for s in stocks:
    fi = s.get('foreign_net', 0) or 0
    chg = s.get('change_pct', 0) or 0
    reasons = []
    if fi < -5000000:
        reasons.append(f'外資賣超{fi:+,.0f}股')
    if abs(chg) > 5:
        reasons.append(f'漲跌{chg:+.2f}%')
    if reasons:
        anomalies.append((s, reasons))

if anomalies:
    for s, reasons in anomalies:
        code = s.get('stock_id', '')
        name = s.get('stock_name', '')
        close = s.get('close', 0) or 0
        fi = s.get('foreign_net', 0) or 0
        chg = s.get('change_pct', 0) or 0
        bp = s.get('big_holder_pct', 0) or 0
        print(f"  {code} {name} | 收{close} {chg:+.2f}% | 外資淨{fi:+,.0f} | 大戶{bp:.2f}% | {'; '.join(reasons)}")
else:
    print('  無異常')

# === Foreign sell top10 ===
print()
print('=== 外資淨賣超 TOP10 ===')
sorted_sell = sorted(stocks, key=lambda x: x.get('foreign_net', 0) or 0)[:10]
for s in sorted_sell:
    fi = s.get('foreign_net', 0) or 0
    if fi >= 0:
        continue
    chg = s.get('change_pct', 0) or 0
    code = s.get('stock_id', '')
    name = s.get('stock_name', '')
    close = s.get('close', 0) or 0
    print(f"  {code} {name} | 收{close} {chg:+.2f}% | 外資賣超{fi:+,.0f}股")

# === Foreign buy top10 ===
print()
print('=== 外資淨買超 TOP10 ===')
sorted_buy = sorted(stocks, key=lambda x: x.get('foreign_net', 0) or 0, reverse=True)[:10]
for s in sorted_buy:
    fi = s.get('foreign_net', 0) or 0
    if fi <= 0:
        continue
    chg = s.get('change_pct', 0) or 0
    code = s.get('stock_id', '')
    name = s.get('stock_name', '')
    close = s.get('close', 0) or 0
    print(f"  {code} {name} | 收{close} {chg:+.2f}% | 外資買超{fi:+,.0f}股")

# === Margin spike ===
print()
print('=== 融資異動 TOP10（融資餘額增加）===')
sorted_margin = sorted(stocks, key=lambda x: (x.get('margin', {}) or {}).get('balance_change', 0) or 0, reverse=True)[:10]
for s in sorted_margin:
    m = s.get('margin', {}) or {}
    mc = m.get('balance_change', 0) or 0
    if mc <= 0:
        continue
    chg = s.get('change_pct', 0) or 0
    code = s.get('stock_id', '')
    name = s.get('stock_name', '')
    close = s.get('close', 0) or 0
    mbal = m.get('balance', 0) or 0
    print(f"  {code} {name} | 收{close} {chg:+.2f}% | 融資增{mc:+,.0f}張 (餘{mbal:,.0f})")

# === Market overview ===
print()
print('=== 大盤概況 ===')
up = sum(1 for s in stocks if (s.get('change_pct', 0) or 0) > 0)
down = sum(1 for s in stocks if (s.get('change_pct', 0) or 0) < 0)
flat = len(stocks) - up - down
fi_buy = sum(1 for s in stocks if (s.get('foreign_net', 0) or 0) > 0)
fi_sell = sum(1 for s in stocks if (s.get('foreign_net', 0) or 0) < 0)
up5 = sum(1 for s in stocks if (s.get('change_pct', 0) or 0) > 5)
down5 = sum(1 for s in stocks if (s.get('change_pct', 0) or 0) < -5)
print(f"  上漲{up} / 下跌{down} / 平盤{flat} (共{len(stocks)}檔)")
print(f"  外資買超{fi_buy}檔 / 賣超{fi_sell}檔")
print(f"  漲停附近(>5%): {up5}檔 / 跌停附近(<-5%): {down5}檔")
total_fi = sum(s.get('foreign_net', 0) or 0 for s in stocks)
print(f"  外資合計淨流向: {total_fi:+,.0f}股")
