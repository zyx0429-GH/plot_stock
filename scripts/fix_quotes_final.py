import sys

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\generate_html.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '00982A' in line and "lines.append" in line and 'location.href' in line:
        # Found problematic line - fix the quotes
        if "location.href='stock_" in line:
            line = line.replace("location.href='stock_", "location.href=\\'stock_")
            line = line.replace(".html'\" class", ".html\\'\" class")
            lines[i] = line
            sys.stdout.write("[FIX] Line %d\n" % (i+1))

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\generate_html.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

sys.stdout.write("Done!\n")
