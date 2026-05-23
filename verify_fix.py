import re
with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\docs\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check for >=100 button
if '>=100' in content:
    print('[OK] >=100 button found')
else:
    print('[FAIL] >=100 button NOT found')

# Check JS has th-100
if 'th-100' in content and 'th-1000' in content:
    print('[OK] JS threshold filter includes 100 and 1000')
else:
    print('[FAIL] JS threshold filter missing values')

# Count threshold buttons
buttons = re.findall(r'id="th-\d+"', content)
print('Threshold buttons:', buttons)

# Verify data-threshold values in table rows
rows = re.findall(r'data-threshold="(\d+)"', content)
unique_thresholds = set(rows)
print('Data thresholds in rows:', unique_thresholds)
print('Total rows:', len(rows))
