import json
import os

path = "data/raw_data.json"
if not os.path.exists(path):
    print("raw_data.json not found")
    exit()
with open(path, "r", encoding="utf-8") as f:
    d = json.load(f)
for sid in ["2317", "2327", "2449", "3661"]:
    info = d.get(sid, {}).get("info", {})
    close = info.get("close", "N/A")
    open_ = info.get("open", "N/A")
    name = info.get("stock_name", "N/A")
    change = info.get("change_pct", "N/A")
    print(f"{sid}: close={close}, open={open_}, name={name}, change_pct={change}")
