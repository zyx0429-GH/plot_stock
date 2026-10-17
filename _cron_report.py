import json

with open('data/raw_data.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)
with open('data/screened_data.json', 'r', encoding='utf-8') as f:
    scr = json.load(f)

def fmt(d):
    sid = d.get('stock_id', '?')
    name = d.get('stock_name', '?')
    close = d.get('close', 0)
    chg = d.get('change_pct', 0) or 0
    fn = d.get('foreign_net', 0) or 0
    tn = d.get('trust_net', 0) or 0
    bh = d.get('big_holder_pct', 0)
    bhc = d.get('big_holder_change', 0)
    m = d.get('margin', {}) or {}
    mchg = m.get('margin_change', 0)
    return f"{sid} {name} 收{close} 漲跌{chg:+.2f}% 外資{fn:+,} 投信{tn:+,} 大戶{bh}%({bhc:+.2f}) 融資{mchg:+,}"

print("=== 00981A 雙重認證 (" + str(len(scr['dual_certified'])) + "檔) ===")
for s in scr['dual_certified']:
    print(fmt(s))

print()
print("=== 00982A 雙重認證 (" + str(len(scr['dual_certified_982a'])) + "檔) ===")
for s in scr['dual_certified_982a']:
    print(fmt(s))

print()
print("=== 三重認證 (" + str(len(scr['triple_certified'])) + "檔) ===")
for s in scr['triple_certified']:
    print(fmt(s))

print()
print("=== 異常掃描：外資淨賣超>500萬 或 |漲跌|>5%（全部監控檔） ===")
anomalies = []
for sid, d in raw.items():
    i = d.get('info', {})
    chg = i.get('change_pct', 0) or 0
    fn = i.get('foreign_net', 0) or 0
    if fn < -5000000 or abs(chg) > 5:
        anomalies.append((sid, i.get('stock_name','?'), i.get('close',0), chg, fn, i.get('trust_net',0)))
anomalies.sort(key=lambda x: x[4])
for a in anomalies:
    flag = []
    if a[4] < -5000000: flag.append('外資大賣')
    if abs(a[3]) > 5: flag.append('大漲跌')
    print(f"{a[0]} {a[1]} 收{a[2]} 漲跌{a[3]:+.2f}% 外資{a[4]:+,} 投信{a[5]:+,}  [{'+'.join(flag)}]")

print()
print("=== 外資買超前10 ===")
fb = []
for sid, d in raw.items():
    i = d.get('info', {})
    fn = i.get('foreign_net', 0) or 0
    fb.append((fn, sid, i.get('stock_name','?'), i.get('change_pct',0), i.get('close',0)))
fb.sort(reverse=True)
for fn, sid, name, chg, c in fb[:10]:
    print(f"{sid} {name} 收{c} 漲跌{chg:+.2f}% 外資{fn:+,}")

print()
print("=== 外資賣超前10 ===")
for fn, sid, name, chg, c in fb[-10:]:
    print(f"{sid} {name} 收{c} 漲跌{chg:+.2f}% 外資{fn:+,}")

print()
print("=== 融資大增前15 (margin_spike) ===")
for s in scr['margin_spike'][:15]:
    m = s.get('margin', {}) or {}
    print(f"{s.get('stock_id')} {s.get('stock_name')} 融資餘額{m.get('balance'):,} 單日{m.get('margin_change'):+,}({m.get('margin_change_pct'):+.1f}%) 收{s.get('close')} 漲跌{(s.get('change_pct') or 0):+.2f}%")

print()
print("update_time:", scr.get('update_time'))
