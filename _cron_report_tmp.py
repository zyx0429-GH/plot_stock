#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r"C:\Users\user\.kimi_openclaw\workspace\plot_stock"
d = json.load(open(os.path.join(base, "data", "weekly_ranking.json"), encoding="utf-8"))

def f(x):
    try: return float(str(x).replace('%','').replace('+',''))
    except: return 0.0

def line(s):
    sigs = s.get("signals") or []
    sig = ",".join(sigs) if isinstance(sigs, list) else str(sigs)
    rc = s.get("rank_change") or ""
    return (f"{s['code']} {s['name']} [{s.get('market','')}/{s.get('industry','')}] "
            f"價={s.get('price')} 大戶持股={s.get('big_holder_pct')} 週增減={s.get('wow_pct')} "
            f"連增={s.get('streak')} 排名變動={rc} 訊號={sig}")

print("fetched_at:", d.get("fetched_at"))
print("\n########## 門檻 400張 (大戶>400張) ##########")
st = d["thresholds"]["400"]["stocks"]
up = sorted(st, key=lambda s: f(s.get("wow_pct")), reverse=True)
print("\n--- 週增減 TOP15 ---")
for s in up[:15]: print(line(s))
print("\n--- 週增減 最後15 (減持最多) ---")
for s in up[-15:]: print(line(s))

print("\n--- 上櫃 (OTC) 週增減 TOP15 ---")
otc = sorted([s for s in st if s.get("market")=="上櫃"], key=lambda s: f(s.get("wow_pct")), reverse=True)
for s in otc[:15]: print(line(s))
print("上櫃檔數(400門檻榜內):", len(otc))

print("\n########## 門檻 1000張 ##########")
st1 = d["thresholds"]["1000"]["stocks"]
up1 = sorted(st1, key=lambda s: f(s.get("wow_pct")), reverse=True)
print("\n--- 週增減 TOP10 ---")
for s in up1[:10]: print(line(s))
print("\n--- 週增減 最後10 ---")
for s in up1[-10:]: print(line(s))
otc1 = [s for s in st1 if s.get("market")=="上櫃"]
print("\n--- 上櫃 TOP10 ---")
for s in sorted(otc1, key=lambda s: f(s.get("wow_pct")), reverse=True)[:10]: print(line(s))

print("\n########## 門檻 200張 ##########")
st2 = d["thresholds"]["200"]["stocks"]
for s in sorted(st2, key=lambda s: f(s.get("wow_pct")), reverse=True)[:10]: print(line(s))

print("\n########## 訊號計數 ##########")
for k,v in d["signal_counts"].items(): print(f"  {k}: {v}")

print("\n########## 統計 ##########")
for th in ["200","400","1000"]:
    print(th, d["thresholds"][th]["stats"])
