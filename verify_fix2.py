import re
with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\docs\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find big holder table section
idx = content.find('id="bigHolderTable"')
print('bigHolderTable found at:', idx)

# Check for >=100 or ≥100
if '>=100' in content or '\u2265100' in content:
    print('[OK] 100 button text found')
else:
    print('[WARN] 100 button text not found, checking th-100...')
    if 'th-100' in content:
        # Find the actual text near th-100
        idx = content.find('th-100')
        print('th-100 context:', content[idx:idx+80])

# Find data-threshold pattern - more lenient
rows = re.findall(r'data-threshold="([^"]+)"', content)
print('All data-threshold values:', set(rows))
print('Total data-threshold count:', len(rows))

# Find a sample row
idx = content.find('data-threshold=')
if idx >= 0:
    print('Sample row:', content[idx:idx+200])
