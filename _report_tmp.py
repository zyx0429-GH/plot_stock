import json

with open('data/weekly_ranking.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== 大戶週增減 Top 20 (threshold 400) ===')
for s in data['400'][:20]:
    pct = s.get('big_holder_pct', 'N/A')
    wow = s.get('wow_change', 'N/A')
    cw = s.get('consecutive_weeks', 'N/A')
    print(f"{s['code']} {s['name']}: {pct}% big_holder, WoW {wow}% ({cw} consecutive)")

print()
print('=== OTC 上櫃股票重點 ===')
otc = [s for s in data['400'] if s['code'].startswith('8')]
print(f'OTC in 400 threshold: {len(otc)} stocks')
for s in otc[:15]:
    pct = s.get('big_holder_pct', 'N/A')
    wow = s.get('wow_change', 'N/A')
    print(f"{s['code']} {s['name']}: {pct}% big_holder, WoW {wow}%")

print()
print('=== Signals summary ===')
all_signals = {}
for t in ['200', '400', '1000']:
    for s in data[t]:
        for sig in s.get('signals', []):
            all_signals[sig] = all_signals.get(sig, 0) + 1
for sig, cnt in sorted(all_signals.items(), key=lambda x: -x[1])[:10]:
    print(f"  {sig}: {cnt}")
