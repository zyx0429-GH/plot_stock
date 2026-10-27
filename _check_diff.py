import json, io, sys

# Compare old (git HEAD) vs new raw_data.json for stock 2330 foreign/margin arrays
old_txt = io.open(r'C:\Users\user\AppData\Local\Temp\old_raw.json', encoding='utf-8', errors='replace').read()

def grab(txt, sid):
    i = txt.find('"%s"' % sid)
    if i < 0:
        return None
    j = txt.find('"foreign"', i)
    return txt[j:j+800]

print('=== OLD 2330 foreign segment ===')
print(grab(old_txt, '2330'))

new = json.load(io.open('data/raw_data.json', encoding='utf-8'))
s = new['2330']
print('=== NEW 2330 ===')
print('foreign:', s.get('foreign'))
print('margin:', s.get('margin'))
print('trust:', s.get('trust'))
print('holding len:', len(s.get('holding', [])))
print('price dates? sample price keys:', list(s.get('price', {}).keys())[:5])
