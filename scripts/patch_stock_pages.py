import os
import re

DOCS_DIR = r"C:\Users\user\.kimi_openclaw\workspace\plot_stock\docs"
SCRIPT_TAG = '<script src="js/extra_features.js" defer></script>'

files = [f for f in os.listdir(DOCS_DIR) if f.startswith('stock_') and f.endswith('.html')]
fixed = 0
for fname in files:
    path = os.path.join(DOCS_DIR, fname)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if SCRIPT_TAG in content:
        continue
    # Insert before </head>
    if '</head>' in content:
        content = content.replace('</head>', f'{SCRIPT_TAG}\n</head>')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        fixed += 1
        print(f"Fixed: {fname}")
    else:
        print(f"Skip (no </head>): {fname}")

print(f"\nTotal fixed: {fixed}/{len(files)}")
