import json
import os
import sys

# 更新 screened_data.json
screened_path = os.path.join("data", "screened_data.json")
if os.path.exists(screened_path):
    with open(screened_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for key in ["screened", "foreign_buy", "trust_buy", "bull_stocks", "dual_certified", "watchlist"]:
        stocks = data.get(key, [])
        for s in stocks:
            tech = s.get("technical", {})
            close = s.get("close")
            ma20 = tech.get("ma20")
            ma60 = tech.get("ma60")

            if close is not None and ma20 is not None and ma20 != "-" and ma20 != 0:
                tech["bias20"] = round((close - ma20) / ma20 * 100, 2)
            else:
                tech["bias20"] = "-"

            if close is not None and ma60 is not None and ma60 != "-" and ma60 != 0:
                tech["bias60"] = round((close - ma60) / ma60 * 100, 2)
            else:
                tech["bias60"] = "-"

    with open(screened_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated {screened_path}")

# 更新 raw_data.json
raw_path = os.path.join("data", "raw_data.json")
if os.path.exists(raw_path):
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    for stock_id, stock_data in raw_data.items():
        tech = stock_data.get("technical", {})
        close = stock_data.get("close")
        ma20 = tech.get("ma20")
        ma60 = tech.get("ma60")

        if close is not None and ma20 is not None and ma20 != "-" and ma20 != 0:
            tech["bias20"] = round((close - ma20) / ma20 * 100, 2)
        else:
            tech["bias20"] = "-"

        if close is not None and ma60 is not None and ma60 != "-" and ma60 != 0:
            tech["bias60"] = round((close - ma60) / ma60 * 100, 2)
        else:
            tech["bias60"] = "-"

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    print(f"Updated {raw_path}")

print("Done updating BIAS data in JSON files.")
