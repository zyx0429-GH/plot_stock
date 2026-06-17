import json

with open('data/screened_data.json','r',encoding='utf-8') as f:
    data = json.load(f)

stocks = data.get('screened',[])
print(f'總股票數: {len(stocks)}')

missing = []
for s in stocks:
    tech = s.get('technical',{})
    ma20 = tech.get('ma20')
    ma60 = tech.get('ma60')
    if ma20 is None or ma60 is None:
        missing.append(f"{s.get('stock_id')} {s.get('stock_name')}: ma20={ma20} ma60={ma60}")

print(f'缺少 MA20/MA60 的股票數: {len(missing)}')
for m in missing[:20]:
    print(m)
