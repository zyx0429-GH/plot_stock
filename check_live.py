import re
with open('docs/watchlist.html','r',encoding='utf-8') as f:
    html = f.read()

# Check threshold column exists
has_threshold_col = '門檻' in html
print('has threshold column:', has_threshold_col)

# Check big_holder values
rows = re.findall(r'<td class="highlight">([<d.]+)%</td>', html)
non_zero = [r for r in rows if float(r) > 0]
print(f'total big_holder rows: {len(rows)}, non-zero: {len(non_zero)}')

# Check dual certified
has_dual = '雙重認證' in html
print('has dual certified:', has_dual)
