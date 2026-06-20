import sys

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\stock_screener.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Patch 1: Add MACD score in _get_technical_analysis
old1 = '''            macd_data = {
                "dif": round(dif_series.iloc[-1], 4) if not pd.isna(dif_series.iloc[-1]) else "-",
                "dea": round(dea_series.iloc[-1], 4) if not pd.isna(dea_series.iloc[-1]) else "-",
                "hist": round(hist_series.iloc[-1], 4) if not pd.isna(hist_series.iloc[-1]) else "-",
            }'''

new1 = '''            dif_val = dif_series.iloc[-1]
            dea_val = dea_series.iloc[-1]
            hist_val = hist_series.iloc[-1]
            macd_data = {
                "dif": round(dif_val, 4) if not pd.isna(dif_val) else "-",
                "dea": round(dea_val, 4) if not pd.isna(dea_val) else "-",
                "hist": round(hist_val, 4) if not pd.isna(hist_val) else "-",
            }
            # MACD score (0-10)
            if not (pd.isna(dif_val) or pd.isna(dea_val) or pd.isna(hist_val)):
                try:
                    dif_f = float(dif_val)
                    dea_f = float(dea_val)
                    hist_f = float(hist_val)
                    if dif_f > dea_f and hist_f > 0:
                        macd_data["score"] = 10
                    elif dif_f < dea_f and hist_f < 0:
                        macd_data["score"] = 0
                    else:
                        macd_data["score"] = 5
                except (ValueError, TypeError):
                    macd_data["score"] = "-"
            else:
                macd_data["score"] = "-"'''

if old1 in content:
    content = content.replace(old1, new1)
    print("[OK] Added MACD score")
else:
    print("[WARN] MACD score patch not applied")

# Patch 2: Add dual_certified_982a and triple_certified methods
old2 = '''    def check_dual_certified(self, stock_id, big_change, foreign_consecutive, trust_consecutive):
        """
        雙重認證篩選 (00981A):
        條件1: 在 00981A 成分股清單中
        條件2: 400大戶近期增倉 (big_holder_change > 0)
        條件3: 外資連買 or 投信連買
        """
        from config import ETF_00981A_HOLDINGS
        is_in_00981a = stock_id in ETF_00981A_HOLDINGS
        big_holder_increasing = big_change > 0 if big_change else False
        buying = foreign_consecutive or trust_consecutive
        return is_in_00981a and big_holder_increasing and buying

    def check_big_holder'''

new2 = '''    def check_dual_certified(self, stock_id, big_change, foreign_consecutive, trust_consecutive):
        """
        雙重認證篩選 (00981A):
        條件1: 在 00981A 成分股清單中
        條件2: 400大戶近期增倉 (big_holder_change > 0)
        條件3: 外資連買 or 投信連買
        """
        from config import ETF_00981A_HOLDINGS
        is_in_00981a = stock_id in ETF_00981A_HOLDINGS
        big_holder_increasing = big_change > 0 if big_change else False
        buying = foreign_consecutive or trust_consecutive
        return is_in_00981a and big_holder_increasing and buying

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
    print("[OK] Added dual_certified_982a and triple_certified")
else:
    print("[WARN] Dual/triple certified patch not applied")

# Patch 3: Add to stock dict
old3 = '"dual_certified": self.check_dual_certified(stock_id, big_change, foreign_consecutive, trust_consecutive),'
new3 = '"dual_certified": self.check_dual_certified(stock_id, big_change, foreign_consecutive, trust_consecutive),\n                "dual_certified_982a": self.check_dual_certified_982a(stock_id, big_change, foreign_consecutive, trust_consecutive),\n                "triple_certified": self.check_triple_certified(stock_id, big_change, foreign_consecutive, trust_consecutive),'

if old3 in content:
    content = content.replace(old3, new3)
    print("[OK] Added to stock dict")
else:
    print("[WARN] Stock dict patch not applied")

# Patch 4: Add filtering
old4 = 'dual_certified = [s for s in screened if s.get("dual_certified", False)]\n\n        #'
new4 = 'dual_certified = [s for s in screened if s.get("dual_certified", False)]\n        dual_certified_982a = [s for s in screened if s.get("dual_certified_982a", False)]\n        triple_certified = [s for s in screened if s.get("triple_certified", False)]\n\n        #'

if old4 in content:
    content = content.replace(old4, new4)
    print("[OK] Added filtering")
else:
    print("[WARN] Filtering patch not applied")

# Patch 5: Add to output
old5 = '"dual_certified": dual_certified,\n            # ==='
new5 = '"dual_certified": dual_certified,\n            "dual_certified_982a": dual_certified_982a,\n            "triple_certified": triple_certified,\n            # ==='

if old5 in content:
    content = content.replace(old5, new5)
    print("[OK] Added to output")
else:
    print("[WARN] Output patch not applied")

# Patch 6: Add print statements
old6 = 'print(f"  - Dual certified: {len(results[\'dual_certified\'])}\")\n        print(f"  - Margin spike:'
new6 = 'print(f"  - Dual certified (00981A): {len(results[\'dual_certified\'])}\")\n        print(f"  - Dual certified (00982A): {len(results[\'dual_certified_982a\'])}\")\n        print(f"  - Triple certified: {len(results[\'triple_certified\'])}\")\n        print(f"  - Margin spike:'

if old6 in content:
    content = content.replace(old6, new6)
    print("[OK] Added print statements")
else:
    print("[WARN] Print statements patch not applied")

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\stock_screener.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
