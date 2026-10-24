import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('data/screened_data.json', encoding='utf-8') as f:
    d = json.load(f)

print('TYPE:', type(d).__name__)
if isinstance(d, dict):
    print('KEYS:', list(d.keys())[:15])
    # peek structure
    for k in list(d.keys())[:3]:
        v = d[k]
        print(f'--- {k}: {type(v).__name__}')
        if isinstance(v, dict):
            print('  subkeys:', list(v.keys())[:30])
        elif isinstance(v, list) and v:
            print('  list[0]:', type(v[0]).__name__, (list(v[0].keys())[:30] if isinstance(v[0], dict) else v[0]))
elif isinstance(d, list):
    print('LEN:', len(d))
    if d:
        print('item0 keys:', list(d[0].keys()) if isinstance(d[0], dict) else d[0])
