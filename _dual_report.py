# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

raw = json.load(open('data/raw_data.json', encoding='utf-8'))
scr = json.load(open('data/screened_data.json', encoding='utf-8'))

def stock_info(code):
    s = raw.get(code)
    if not s:
        return None
    info = s.get('info', {})
    m = s.get('margin', [{}])
    m = m[0] if m else {}
    return {
        'name': info.get('stock_name'),
        'close': info.get('close'),
        'chg_pct': round(info.get('change_pct', 0) or 0, 2),
        'foreign_net_shares': info.get('foreign_net'),
        'foreign_net_value_wan': round((info.get('foreign_net') or 0) * (info.get('close') or 0) / 10000),
        'trust_net_shares': info.get('trust_net'),
        'margin_change': m.get('margin_change'),
        'margin_balance': m.get('margin_balance'),
        'short_change': m.get('short_change'),
        'volume': info.get('volume'),
    }

def fmt(code, i):
    fn = i['foreign_net_shares'] or 0
    fd = '買' if fn > 0 else '賣' if fn < 0 else '平'
    fav = abs(i['foreign_net_value_wan'])
    return (f"{code} {i['name']} | 收盤 {i['close']} ({i['chg_pct']}%) | "
            f"外資淨{fd} {fav} 萬 | 投信 {i['trust_net_shares']} | "
            f"融資 {i['margin_balance']} 張 (變動 {i['margin_change']}) | 券變 {i['short_change']}")

def get_code(it):
    return it.get('code') if isinstance(it, dict) else it

print('====== 00981A 雙認證 ({}) ======'.format(len(scr['dual_certified'])))
anomalies = []
for it in scr['dual_certified']:
    code = get_code(it)
    i = stock_info(code)
    if i:
        print(fmt(code, i))
        if i['foreign_net_value_wan'] < -500 or abs(i['chg_pct']) > 5:
            anomalies.append(('00981A', code, i))
print()
print('====== 00982A 雙認證 ({}) ======'.format(len(scr['dual_certified_982a'])))
for it in scr['dual_certified_982a']:
    code = get_code(it)
    i = stock_info(code)
    if i:
        print(fmt(code, i))
        if i['foreign_net_value_wan'] < -500 or abs(i['chg_pct']) > 5:
            anomalies.append(('00982A', code, i))
print()
print('====== 三重認證 ({}) ======'.format(len(scr['triple_certified'])))
for it in scr['triple_certified']:
    code = get_code(it)
    i = stock_info(code)
    if i:
        print(fmt(code, i))
        if i['foreign_net_value_wan'] < -500 or abs(i['chg_pct']) > 5:
            anomalies.append(('三重', code, i))

print()
print('====== 異常警示 (外資賣超>500萬 或 漲跌>5%) ======')
if not anomalies:
    print('無異常')
for tag, code, i in anomalies:
    reasons = []
    if i['foreign_net_value_wan'] < -500:
        reasons.append(f"外資淨賣超 {abs(i['foreign_net_value_wan'])} 萬")
    if abs(i['chg_pct']) > 5:
        reasons.append(f"股價 {'漲' if i['chg_pct']>0 else '跌'} {abs(i['chg_pct'])}%")
    print(f"[{tag}] {code} {i['name']}: {'; '.join(reasons)}")
