import sys

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\stock_screener.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix check_dual_certified signature
old = '    def check_dual_certified(self, stock_id, info, tech, big_pct, big_change, foreign_consecutive, trust_consecutive):'
new = '    def check_dual_certified(self, stock_id, big_change, foreign_consecutive, trust_consecutive):'

if old in content:
    content = content.replace(old, new)
    sys.stdout.write('[OK] Fixed dual_certified signature\n')
else:
    sys.stdout.write('[WARN] Could not find old signature\n')

# Add 982a and triple methods after dual_certified
old2 = '        return is_in_00981a and big_holder_increasing and buying\n\n    def check_big_holder'
new2 = '''        return is_in_00981a and big_holder_increasing and buying

    def check_dual_certified_982a(self, stock_id, big_change, foreign_consecutive, trust_consecutive):
        """
        雙重認證篩選 (00982A):
        條件1: 在 00982A 成分股清單中
        條件2: 400大戶近期增倉 (big_holder_change > 0)
        條件3: 外資連買 or 投信連買
        """
        from config import ETF_00982A_HOLDINGS
        is_in_00982a = stock_id in ETF_00982A_HOLDINGS
        big_holder_increasing = big_change > 0 if big_change else False
        buying = foreign_consecutive or trust_consecutive
        return is_in_00982a and big_holder_increasing and buying

    def check_triple_certified(self, stock_id, big_change, foreign_consecutive, trust_consecutive):
        """
        三重認證篩選 (00981A 或 00982A + 大戶增倉 + 法人買超):
        條件1: 在 00981A 或 00982A 成分股清單中（任一即可）
        條件2: 400大戶近期增倉 (big_holder_change > 0)
        條件3: 外資連買 or 投信連買
        """
        from config import ETF_00981A_HOLDINGS, ETF_00982A_HOLDINGS
        is_in_etf = stock_id in ETF_00981A_HOLDINGS or stock_id in ETF_00982A_HOLDINGS
        big_holder_increasing = big_change > 0 if big_change else False
        buying = foreign_consecutive or trust_consecutive
        return is_in_etf and big_holder_increasing and buying

    def check_big_holder'''

if old2 in content:
    content = content.replace(old2, new2)
    sys.stdout.write('[OK] Added 982a and triple methods\n')
else:
    sys.stdout.write('[WARN] Could not find insertion point\n')

# Fix stock dict call
old3 = '                "dual_certified": self.check_dual_certified(stock_id, info, tech, big_pct, big_change, foreign_consecutive, trust_consecutive),'
new3 = '                "dual_certified": self.check_dual_certified(stock_id, big_change, foreign_consecutive, trust_consecutive),\n                "dual_certified_982a": self.check_dual_certified_982a(stock_id, big_change, foreign_consecutive, trust_consecutive),\n                "triple_certified": self.check_triple_certified(stock_id, big_change, foreign_consecutive, trust_consecutive),'

if old3 in content:
    content = content.replace(old3, new3)
    sys.stdout.write('[OK] Fixed stock dict call\n')
else:
    sys.stdout.write('[WARN] Could not find stock dict call\n')

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\stock_screener.py', 'w', encoding='utf-8') as f:
    f.write(content)

sys.stdout.write('Done!\n')
