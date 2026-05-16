import json
import os

for fname in ["data/screened_data.json", "data/raw_data.json"]:
    path = fname
    if not os.path.exists(path):
        print(f"{path} not found")
        continue
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    print(f"\n=== {path} ===")
    if "screened" in d:
        # screened_data.json
        for sid in ["2317", "2327", "2449", "3661"]:
            found = None
            for s in d.get("screened", []):
                if s.get("stock_id") == sid:
                    found = s
                    break
            if found:
                close = found.get("close", "N/A")
                open_ = found.get("open", "N/A")
                name = found.get("stock_name", "N/A")
                change = found.get("change_pct", "N/A")
                print(f"{sid}: close={close}, open={open_}, name={name}, change_pct={change}")
            else:
                print(f"{sid}: NOT in screened_data")
    else:
        # raw_data.json
        for sid in ["2317", "2327", "2449", "3661"]:
            info = d.get(sid, {}).get("info", {})
            close = info.get("close", "N/A")
            open_ = info.get("open", "N/A")
            name = info.get("stock_name", "N/A")
            change = info.get("change_pct", "N/A")
            print(f"{sid}: close={close}, open={open_}, name={name}, change_pct={change}")
