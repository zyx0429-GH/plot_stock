#!/usr/bin/env python3
"""
数据完整性检查脚本
在 run_daily.bat / run_weekly.bat 中运行，确保数据链未断裂

检查项:
1. norway/all_stocks_weekly.json 不为空
2. raw_data.json 中关键股票有 shareholder 数据
3. screened_data.json 中 big_holder_pct 不全为 0
4. weekly_ranking.json 三个门槛数据不相同
"""

import json
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def fail(msg):
    print(f"[FAIL] {msg}")
    return False

def ok(msg):
    print(f"[OK] {msg}")
    return True

def check_norway_data():
    """检查 Norway 大戶数据是否为空"""
    path = os.path.join(DATA_DIR, 'norway', 'all_stocks_weekly.json')
    if not os.path.exists(path):
        return fail(f"Norway data missing: {path}")
    
    size = os.path.getsize(path)
    if size < 100:
        return fail(f"Norway data too small ({size} bytes), likely empty")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data or len(data) == 0:
        return fail("Norway data is empty list []. Run norway_fetcher.py first!")
    
    return ok(f"Norway data: {len(data)} records, {size} bytes")

def check_raw_data():
    """检查 raw_data.json 中 shareholder 数据是否为空"""
    path = os.path.join(DATA_DIR, 'raw_data.json')
    if not os.path.exists(path):
        return fail(f"raw_data.json missing")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 抽查关键股票
    sample_ids = ['2330', '2303', '2881', '2317', '2454']
    found = 0
    missing = []
    for sid in sample_ids:
        sdata = data.get(sid, {})
        sh = sdata.get('shareholder', [])
        if sh and len(sh) > 0 and sh[0].get('concentration', 0) > 0:
            found += 1
        else:
            missing.append(sid)
    
    if found == 0:
        return fail(f"raw_data.json: ALL sample stocks have empty shareholder data! "
                    f"Run data_fetcher.py with _merge_mndtas() enabled.")
    elif len(missing) > 0:
        print(f"[WARN] {len(missing)} sample stocks missing shareholder data: {missing}")
    
    return ok(f"raw_data.json: {found}/{len(sample_ids)} sample stocks have shareholder data")

def check_screened_data():
    """检查 screened_data.json 中 big_holder_pct 是否全为 0"""
    path = os.path.join(DATA_DIR, 'screened_data.json')
    if not os.path.exists(path):
        return fail(f"screened_data.json missing")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    screened = data.get('screened', [])
    if not screened:
        return fail("screened_data.json: screened list is empty")
    
    zero_count = sum(1 for s in screened if s.get('big_holder_pct') in (0, None, 0.0))
    total = len(screened)
    
    if zero_count == total:
        return fail(f"screened_data.json: ALL {total} stocks have big_holder_pct=0! "
                    f"Data chain broken. Check norway_fetcher + data_fetcher.")
    
    if zero_count > total * 0.5:
        print(f"[WARN] {zero_count}/{total} stocks have big_holder_pct=0 (over 50%)")
    
    return ok(f"screened_data.json: {total - zero_count}/{total} stocks have non-zero big_holder_pct")

def check_weekly_ranking():
    """检查 weekly_ranking.json 三个门槛数据是否相同"""
    path = os.path.join(DATA_DIR, 'weekly_ranking.json')
    if not os.path.exists(path):
        return fail(f"weekly_ranking.json missing")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    thresholds = data.get('thresholds', {})
    
    # 检查每个门槛是否有数据
    for t in ['200', '400', '1000']:
        stocks = thresholds.get(t, {}).get('stocks', [])
        if not stocks:
            return fail(f"weekly_ranking.json: threshold {t} has no stocks!")
    
    # 检查三个门槛 Top 5 是否相同（如果相同说明数据有问题）
    top5_200 = [s['code'] for s in thresholds['200']['stocks'][:5]]
    top5_400 = [s['code'] for s in thresholds['400']['stocks'][:5]]
    top5_1000 = [s['code'] for s in thresholds['1000']['stocks'][:5]]
    
    if top5_200 == top5_400 == top5_1000:
        return fail("weekly_ranking.json: All 3 thresholds have IDENTICAL Top 5! "
                    f"Run norway_to_weekly_json.py to regenerate from Norway data.")
    
    return ok(f"weekly_ranking.json: 3 thresholds have different Top 5 ({len(top5_200)} vs {len(top5_400)} vs {len(top5_1000)})")

def check_dual_certified():
    """检查双重/三重认证是否为空（辅助检查）"""
    path = os.path.join(DATA_DIR, 'screened_data.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    dual = len(data.get('dual_certified', []))
    dual982 = len(data.get('dual_certified_982a', []))
    triple = len(data.get('triple_certified', []))
    
    if dual == 0 and dual982 == 0 and triple == 0:
        return fail(f"screened_data.json: ALL dual/triple certified lists are empty! "
                    f"This is normal on some market days, but check if data chain is broken.")
    
    return ok(f"Dual/981A={dual}, Dual/982A={dual982}, Triple={triple}")

def main():
    print("=" * 50)
    print("Plot Stock Data Integrity Check")
    print("=" * 50)
    
    checks = [
        ("Norway big holder data", check_norway_data),
        ("Raw data shareholder", check_raw_data),
        ("Screened big_holder_pct", check_screened_data),
        ("Weekly ranking thresholds", check_weekly_ranking),
        ("Dual/Triple certified", check_dual_certified),
    ]
    
    results = []
    for name, func in checks:
        print(f"\n--- Checking: {name} ---")
        try:
            results.append(func())
        except Exception as e:
            print(f"[ERROR] {name} check crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"[PASS] All {total} checks passed!")
        return 0
    else:
        print(f"[FAIL] {total - passed}/{total} checks failed!")
        print("Data chain may be broken. Please check:")
        print("  1. run_weekly.bat -> norway_fetcher.py (Saturday data)")
        print("  2. run_daily.bat  -> data_fetcher.py")
        print("  3. run_weekly.bat -> norway_to_weekly_json.py (weekly ranking)")
        return 1

if __name__ == '__main__':
    sys.exit(main())
