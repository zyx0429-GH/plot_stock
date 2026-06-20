import sys

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\generate_html.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Patch 1: Add import for ETF_00982A_HOLDINGS
old1 = 'from config import SCREEN_CONFIG, DATA_DIR, DOCS_DIR, WATCHLIST, ETF_00981A_HOLDINGS'
new1 = 'from config import SCREEN_CONFIG, DATA_DIR, DOCS_DIR, WATCHLIST, ETF_00981A_HOLDINGS, ETF_00982A_HOLDINGS'

if old1 in content:
    content = content.replace(old1, new1)
    print("[OK] Added ETF_00982A_HOLDINGS import")
else:
    print("[WARN] Import patch not applied")

# Patch 2: Add 00982A to nav
old2 = '("etf_00981a", "📈 00981A", "etf_00981a.html"),'
new2 = '("etf_00981a", "📈 00981A", "etf_00981a.html"),\n            ("etf_00982a", "📈 00982A", "etf_00982a.html"),'

if old2 in content:
    content = content.replace(old2, new2)
    print("[OK] Added 00982A to nav")
else:
    print("[WARN] Nav patch not applied")

# Patch 3: Add generate_etf_00982a method after generate_etf_00981a
old3 = '    def generate_etf_00981a(self):\n        return self._generate_table_page("00981A 持股明細｜智董籌碼選股站", "📈 00981A 成分股", "etf_00981a", ETF_00981A_HOLDINGS)\n\n    def generate_passive_component'
new3 = '    def generate_etf_00981a(self):\n        return self._generate_table_page("00981A 持股明細｜智董籌碼選股站", "📈 00981A 成分股", "etf_00981a", ETF_00981A_HOLDINGS)\n\n    def generate_etf_00982a(self):\n        return self._generate_table_page("00982A 持股明細｜智董籌碼選股站", "📈 00982A 成分股 (群益台灣精選強棒)", "etf_00982a", ETF_00982A_HOLDINGS)\n\n    def generate_passive_component'

if old3 in content:
    content = content.replace(old3, new3)
    print("[OK] Added generate_etf_00982a method")
else:
    print("[WARN] generate_etf_00982a patch not applied")

# Patch 4: Add to generate_all
old4 = 'self.generate_etf_00981a()\n        self.generate_big_holder_top25()'
new4 = 'self.generate_etf_00981a()\n        self.generate_etf_00982a()\n        self.generate_big_holder_top25()'

if old4 in content:
    content = content.replace(old4, new4)
    print("[OK] Added generate_etf_00982a to generate_all")
else:
    print("[WARN] generate_all patch not applied")

old4b = 'all_stocks = list(set(WATCHLIST + ETF_00981A_HOLDINGS))'
new4b = 'all_stocks = list(set(WATCHLIST + ETF_00981A_HOLDINGS + ETF_00982A_HOLDINGS))'

if old4b in content:
    content = content.replace(old4b, new4b)
    print("[OK] Added ETF_00982A_HOLDINGS to all_stocks")
else:
    print("[WARN] all_stocks patch not applied")

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\generate_html.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
