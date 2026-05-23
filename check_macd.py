import sys
with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\docs\stock_2301.html', 'r', encoding='utf-8') as f:
    content = f.read()
idx = content.find('DIF(12,26)')
if idx >= 0:
    snippet = content[idx-100:idx+400]
    with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\test_macd4.txt', 'w', encoding='utf-8') as f2:
        f2.write(snippet)
    print('found')
else:
    print('not found')
