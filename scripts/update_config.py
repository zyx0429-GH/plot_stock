import json
import os

# Read current config.py
with open('scripts/config.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the load_big_holder_top25 function
old_func = '''def load_big_holder_top25():
    """從 chip_monitoring weekly JSON 載入最新大戶 TOP25"""
    import glob
    import json
    
    weekly_dirs = [
        os.path.join(os.path.dirname(__file__), "..", "data", "chip_monitoring", "weekly"),
        os.path.join(os.path.dirname(__file__), "..", "..", "memory", "chip-monitoring", "weekly"),
        os.path.join(os.path.dirname(__file__), "..", "..", "memory", "chip_monitoring", "weekly"),
    ]
    
    all_files = []
    for d in weekly_dirs:
        if os.path.isdir(d):
            all_files.extend(sorted(glob.glob(os.path.join(d, "*-full.json")), reverse=True))
            all_files.extend(sorted(glob.glob(os.path.join(d, "[0-9]*-[0-9]*-[0-9]*.json")), reverse=True))
    
    if not all_files:
        return []
    
    # 去重並排序
    seen = set()
    unique_files = []
    for f in all_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)
    
    latest_file = unique_files[0]
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    
    stocks = data.get("all_stocks", data.get("top100_increase", []) + data.get("top100_decrease", []))
    if not stocks:
        return []
    
    # 按 bh_pct 排序取前25
    sorted_stocks = sorted(stocks, key=lambda x: x.get("bh_pct", 0), reverse=True)
    return [str(s.get("ticker", "")).lstrip("0") or "0" for s in sorted_stocks[:25]]

BIG_HOLDER_TOP25 = load_big_holder_top25()'''

new_func = '''def load_big_holder_top25():
    """從 weekly_ranking.json 載入最新大戶 TOP25"""
    import json
    import os
    
    weekly_path = os.path.join(os.path.dirname(__file__), "..", "data", "weekly_ranking.json")
    if not os.path.exists(weekly_path):
        return []
    
    try:
        with open(weekly_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    
    # 從 thresholds 提取所有股票
    all_stocks = []
    for th_data in data.get("thresholds", {}).values():
        for s in th_data.get("stocks", []):
            all_stocks.append(s)
    
    if not all_stocks:
        return []
    
    # 去重
    seen = set()
    unique = []
    for s in all_stocks:
        code = str(s.get("code", "")).lstrip("0") or "0"
        if code not in seen:
            seen.add(code)
            pct_str = str(s.get("big_holder_pct", "0%")).replace("%", "")
            try:
                pct = float(pct_str)
            except:
                pct = 0.0
            unique.append({"code": code, "pct": pct})
    
    # 按大戶%排序取前25
    sorted_stocks = sorted(unique, key=lambda x: x["pct"], reverse=True)
    return [s["code"] for s in sorted_stocks[:25]]

BIG_HOLDER_TOP25 = load_big_holder_top25()
print(f"[INFO] Big holder TOP25 loaded: {len(BIG_HOLDER_TOP25)} stocks")

# 將 TOP25 自動合併到 WATCHLIST
WATCHLIST = list(dict.fromkeys(WATCHLIST + BIG_HOLDER_TOP25))
print(f"[INFO] Watchlist after TOP25 merge: {len(WATCHLIST)} stocks")'''

if old_func in content:
    content = content.replace(old_func, new_func)
    with open('scripts/config.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: replaced load_big_holder_top25')
else:
    print('ERROR: old_func not found')
    if 'def load_big_holder_top25' in content:
        print('Found function definition but not exact match')
