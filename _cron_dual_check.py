import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

d = json.load(open('data/screened_data.json', encoding='utf-8'))
print('top type:', type(d).__name__)
if isinstance(d, dict):
    print('top keys:', list(d.keys())[:30])
