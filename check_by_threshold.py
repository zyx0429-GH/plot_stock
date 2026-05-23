import json
with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\data\screened_data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Build threshold lookup
lookup = {}
for s in d.get('watchlist', []):
    sid = s.get('stock_id')
    th = s.get('big_holder_threshold')
    if sid and th:
        lookup[sid] = th
for s in d.get('screened', []):
    sid = s.get('stock_id')
    if sid and sid not in lookup:
        th = s.get('big_holder_threshold')
        if th:
            lookup[sid] = th

# Show stocks by threshold
for th in ['100', '200', '400', '1000']:
    stocks = [(sid, lookup[sid]) for sid, val in lookup.items() if str(val) == th]
    print(f'threshold={th}: {len(stocks)} stocks')
    for sid, _ in stocks[:5]:
        print(f'  {sid}')

# Show missing
all_bhr = {s.get('stock_id') for s in d.get('big_holder_rank', [])}
missing = [sid for sid in all_bhr if sid not in lookup]
print(f'\nMissing thresholds: {len(missing)}')
print(f'Sample: {missing[:10]}')
