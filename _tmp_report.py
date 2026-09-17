import json

with open('data/screened_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

screened = data.get('screened', [])

def fmt(n):
    return '{:,}'.format(int(n))

def check_anomaly(s):
    change_pct = s.get('change_pct', 0)
    foreign_net = s.get('foreign_net', 0)
    anomalies = []
    if abs(change_pct) > 5:
        anomalies.append('股價波動 {:.2f}%'.format(change_pct))
    if foreign_net < -500000:
        anomalies.append('外資大賣超 ' + fmt(foreign_net))
    elif foreign_net > 500000:
        anomalies.append('外資大買超 ' + fmt(foreign_net))
    return anomalies

# Dual certified 981A
dual_981a = [s for s in screened if s.get('dual_certified')]
print('=== 00981A 雙重認證 (外資連買 + 大戶集中) ===')
print('共 {} 檔\n'.format(len(dual_981a)))
for s in dual_981a:
    code = s['stock_id']; name = s['stock_name']; close = s['close']; change_pct = s['change_pct']
    foreign_net = s['foreign_net']; margin = s['margin']; big_holder_pct = s['big_holder_pct']; big_holder_change = s['big_holder_change']
    anomalies = check_anomaly(s)
    status = ' [異常] ' + ' | '.join(anomalies) if anomalies else ''
    print('{} {}: 收盤={:.1f} 漲跌={:+.2f}% | 外資={} | 融資={}({}) | 大戶={:.1f}%({:+.2f}%){}'.format(
        code, name, close, change_pct, fmt(foreign_net), fmt(margin['balance']), fmt(margin['margin_change']), big_holder_pct, big_holder_change, status))

# Dual certified 982A
dual_982a = [s for s in screened if s.get('dual_certified_982a')]
print('\n=== 00982A 雙重認證 (投信連買 + 大戶集中) ===')
print('共 {} 檔\n'.format(len(dual_982a)))
for s in dual_982a:
    code = s['stock_id']; name = s['stock_name']; close = s['close']; change_pct = s['change_pct']
    foreign_net = s['foreign_net']; trust_net = s['trust_net']; margin = s['margin']
    big_holder_pct = s['big_holder_pct']; big_holder_change = s['big_holder_change']
    anomalies = check_anomaly(s)
    status = ' [異常] ' + ' | '.join(anomalies) if anomalies else ''
    print('{} {}: 收盤={:.1f} 漲跌={:+.2f}% | 外資={} 投信={} | 融資={}({}) | 大戶={:.1f}%({:+.2f}%){}'.format(
        code, name, close, change_pct, fmt(foreign_net), fmt(trust_net), fmt(margin['balance']), fmt(margin['margin_change']), big_holder_pct, big_holder_change, status))

# Triple certified
triple = [s for s in screened if s.get('triple_certified')]
print('\n=== 三重認證 (外資+投信+大戶) ===')
print('共 {} 檔\n'.format(len(triple)))
for s in triple:
    code = s['stock_id']; name = s['stock_name']; close = s['close']; change_pct = s['change_pct']
    foreign_net = s['foreign_net']; trust_net = s['trust_net']; margin = s['margin']
    big_holder_pct = s['big_holder_pct']; big_holder_change = s['big_holder_change']
    anomalies = check_anomaly(s)
    status = ' [異常] ' + ' | '.join(anomalies) if anomalies else ''
    print('{} {}: 收盤={:.1f} 漲跌={:+.2f}% | 外資={:+} 投信={:+} | 融資={}({:+}) | 大戶={:.1f}%({:+.2f}%){}'.format(
        code, name, close, change_pct, fmt(foreign_net), fmt(trust_net), fmt(margin['balance']), fmt(margin['margin_change']), big_holder_pct, big_holder_change, status))
