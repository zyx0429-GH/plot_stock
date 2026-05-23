import json
with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\data\screened_data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)
screened = d.get('screened', [])
print('total screened:', len(screened))
# Check big_holder_threshold distribution
thresholds = {}
for s in screened[:20]:
    th = s.get('big_holder_threshold', 'NOT_FOUND')
    thresholds[th] = thresholds.get(th, 0) + 1
    print(f"  {s.get('stock_id')}: threshold={th}, pct={s.get('big_holder_pct')}")
print('threshold distribution:', thresholds)
