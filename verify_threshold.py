import re
with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\docs\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find data-threshold values
rows = re.findall(r'data-threshold="([^"]+)"', content)
unique = set(rows)
print('Data thresholds in rows:', unique)
print('Total rows:', len(rows))

# Check sample rows
for val in list(unique)[:5]:
    count = rows.count(val)
    print(f'  threshold="{val}": {count} rows')

# Check >=100 button
if 'id="th-100"' in content:
    print('[OK] th-100 button exists')
