# -*- coding: utf-8 -*-
"""Daily report extraction v2."""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r"C:\Users\user\.kimi_openclaw\workspace\plot_stock\data"

with open(base + r"\screened_data.json", encoding='utf-8') as f:
    screened = json.load(f)

print("update_time:", screened.get('update_time'))
print("total:", screened.get('total'))

# sample one stock entry structure
lst = screened.get('screened', [])
print("n screened:", len(lst))
if lst:
    print("sample keys:", sorted(lst[0].keys()))

# summary lists
for k in ['dual_certified','dual_certified_982a','triple_certified','foreign_buy','trust_buy','margin_spike','bull_stocks']:
    v = screened.get(k)
    print(f"\n== {k} ({type(v).__name__}, len={len(v) if hasattr(v,'__len__') else '?'}) ==")
    if isinstance(v, list) and v:
        print(json.dumps(v[0], ensure_ascii=False)[:600])
