#!/usr/bin/env python3
"""快速测试 MNDTAS API 和 _merge_mndtas"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
from scripts.data_fetcher import TWStockDataFetcher

fetcher = TWStockDataFetcher()

# 先測試 MNDTAS API 對單一股票的回應
print("=== Test MNDTAS API for 2330 ===")
try:
    data = fetcher._twse_get("exchangeReport/MNDTAS", {"response": "json", "stockNo": "2330"})
    print("keys:", list(data.keys()))
    if data.get("fields"):
        print("fields:", data["fields"])
    if data.get("data"):
        print("rows:", len(data["data"]))
        latest = data["data"][-1]
        print("latest row:", latest)
except Exception as e:
    print("ERROR:", e)
    import traceback
    traceback.print_exc()

# 測試 _merge_mndtas
print("\n=== Test _merge_mndtas ===")
results = {"2330": {"info": {"stock_name": "台積電"}}}
try:
    fetcher._merge_mndtas(results)
    print("2330 shareholder:", results["2330"].get("shareholder"))
except Exception as e:
    print("ERROR:", e)
    import traceback
    traceback.print_exc()
