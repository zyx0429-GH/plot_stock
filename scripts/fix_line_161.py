import sys

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\generate_html.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 161 (0-indexed: 160)
line = lines[160]
# The issue is: location.href='stock_...html' inside an f-string
# Replace the single quotes around href with escaped ones
if "location.href='stock_" in line:
    line = line.replace("location.href='stock_", "location.href=\\'stock_")
    line = line.replace(".html'\" class", ".html\\'\" class")
    lines[160] = line
    sys.stdout.write("[FIX] Line 161\n")

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\generate_html.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

sys.stdout.write("Done!\n")
