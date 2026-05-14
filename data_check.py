import json
with open('data/screened_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print('Keys:', list(data.keys()))
print('screened count:', len(data.get('screened', [])))
print('foreign_buy count:', len(data.get('foreign_buy', [])))
print('bull_stocks count:', len(data.get('bull_stocks', [])))
print('big_holder_rank count:', len(data.get('big_holder_rank', [])))
print('total:', data.get('total'))
for k in ['screened', 'foreign_buy', 'bull_stocks', 'big_holder_rank']:
    arr = data.get(k, [])
    if arr:
        first = arr[0]
        print(f'{k}[0]: stock_id={first.get("stock_id")}, name={first.get("stock_name")}')
