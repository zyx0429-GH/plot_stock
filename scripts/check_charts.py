with open('generate_html.py','r',encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if 'priceChart' in line or 'foreignChart' in line:
        safe = line.strip()[:80].encode('ascii','replace').decode('ascii')
        print(f'{i}: {safe}')
