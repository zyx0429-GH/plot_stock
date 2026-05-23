import json
with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\data\screened_data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print('Keys in screened_data.json:', list(d.keys()))
print('screened count:', len(d.get('screened', [])))
print('big_holder_rank count:', len(d.get('big_holder_rank', [])))
print('watchlist count:', len(d.get('watchlist', [])))

# Check big_holder_rank thresholds
if d.get('big_holder_rank'):
    for s in d['big_holder_rank'][:5]:
        th = s.get('big_holder_threshold', 'NOT_FOUND')
        print(f"  big_holder_rank {s.get('stock_id')}: threshold={th}")

# Check watchlist thresholds
if d.get('watchlist'):
    for s in d['watchlist'][:5]:
        th = s.get('big_holder_threshold', 'NOT_FOUND')
        print(f"  watchlist {s.get('stock_id')}: threshold={th}")
