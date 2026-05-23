import json
with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\data\screened_data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

screened = d.get('screened', [])
big_holder_rank = d.get('big_holder_rank', [])
watchlist = d.get('watchlist', [])

# Build threshold lookup from watchlist
wl_lookup = {}
for s in watchlist:
    sid = s.get('stock_id')
    th = s.get('big_holder_threshold')
    if sid and th:
        wl_lookup[sid] = th

# Check which big_holder_rank items are missing thresholds
missing = []
for s in big_holder_rank:
    sid = s.get('stock_id')
    th_from_screened = s.get('big_holder_threshold')
    th_from_wl = wl_lookup.get(sid)
    if not th_from_screened and not th_from_wl:
        missing.append(sid)

print(f'big_holder_rank total: {len(big_holder_rank)}')
print(f'watchlist total: {len(watchlist)}')
print(f'Missing thresholds: {len(missing)}')
print(f'Sample missing: {missing[:10]}')

# Also check screened directly
sc_missing = []
for s in screened:
    sid = s.get('stock_id')
    if not s.get('big_holder_threshold'):
        sc_missing.append(sid)
print(f'screened missing thresholds: {len(sc_missing)}')
print(f'Sample: {sc_missing[:10]}')
