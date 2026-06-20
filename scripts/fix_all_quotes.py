import sys

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\generate_html.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed = 0
for i, line in enumerate(lines):
    if "location.href='stock_" in line:
        lines[i] = line.replace("location.href='stock_", "location.href=\\'stock_").replace(".html'\" class", ".html\\'\" class")
        fixed += 1
        sys.stdout.write("[FIX] Line %d\n" % (i+1))

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\generate_html.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

sys.stdout.write("Fixed %d lines\n" % fixed)
