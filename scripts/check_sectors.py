import json
from collections import Counter

with open('wantgoo_sectors.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for sid in ['2330', '2317', '2327', '2881', '1216', '3481']:
    print(f'{sid}: {data.get(sid, "N/A")}')

sectors = Counter(data.values())
print(f'\nUnique sectors: {len(sectors)}')
for s, c in sectors.most_common():
    print(f'  {s}: {c}')
