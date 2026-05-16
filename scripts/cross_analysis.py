#!/usr/bin/env python3
"""
交叉比對脚本: fortune-fred 大戶週報 vs Norway.twsthr.info 集保數據

功能:
1. 讀取兩個數據源
2. 找出差異 (同一股票兩邊數據不一致或只有一邊有)
3. 計算相關性
4. 生成交叉比對報告
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime

# 路徑
CHIP_DIR = "data/chip-monitoring/weekly"
NORWAY_DIR = "data/norway"
OUTPUT_DIR = "data/cross_analysis"


def load_latest_chip_data() -> Dict[str, Dict]:
    """載入最新的 fortune-fred 大戶週報數據"""
    # 找最新的 JSON 檔
    import glob
    files = sorted(glob.glob(f"{CHIP_DIR}/*.json"), reverse=True)
    if not files:
        return {}
    
    latest = files[0]
    print(f"[INFO] Loading chip data: {latest}")
    with open(latest, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 轉為 dict (stock_code -> record)
    records = data.get("stocks", data if isinstance(data, list) else [])
    lookup = {}
    for r in records:
        code = r.get("code", r.get("stock_code", ""))
        if code:
            lookup[code] = r
    return lookup


def load_norway_data() -> Dict[str, Dict]:
    """載入 Norway 數據"""
    norway_file = f"{NORWAY_DIR}/taiwan50_weekly.json"
    if not os.path.exists(norway_file):
        norway_file = f"{NORWAY_DIR}/all_stocks_weekly.json"
    
    if not os.path.exists(norway_file):
        return {}
    
    print(f"[INFO] Loading Norway data: {norway_file}")
    with open(norway_file, "r", encoding="utf-8") as f:
        records = json.load(f)
    
    lookup = {}
    for r in records:
        code = r.get("stock_code", "")
        if code:
            lookup[code] = r
    return lookup


def cross_analyze(chip_lookup: Dict, norway_lookup: Dict) -> Dict:
    """交叉比對分析"""
    
    # 1. 共同股票
    common_codes = set(chip_lookup.keys()) & set(norway_lookup.keys())
    
    # 2. 只在 fortune-fred 有的
    only_chip = set(chip_lookup.keys()) - set(norway_lookup.keys())
    
    # 3. 只在 Norway 有的
    only_norway = set(norway_lookup.keys()) - set(chip_lookup.keys())
    
    print(f"[INFO] Common: {len(common_codes)}, Only chip: {len(only_chip)}, Only Norway: {len(only_norway)}")
    
    # 4. 比對共同股票的週增減
    comparisons = []
    diffs = []
    
    for code in sorted(common_codes):
        chip = chip_lookup[code]
        nor = norway_lookup[code]
        
        chip_change = chip.get("weekly_change_pct", chip.get("big_holder_change_pct", 0))
        nor_change = nor.get("latest_change", nor.get("total_change", 0))
        
        diff = chip_change - nor_change
        diffs.append(abs(diff))
        
        comparisons.append({
            "stock_code": code,
            "stock_name": chip.get("name", nor.get("stock_name", "")),
            "chip_change": chip_change,
            "norway_change": nor_change,
            "diff": diff,
            "abs_diff": abs(diff),
            "chip_pct": chip.get("big_holder_pct", 0),
            "norway_pct": nor.get("last_week_hold_pct", 0),
            "direction_match": (chip_change > 0) == (nor_change > 0),  # 方向是否一致
        })
    
    # 排序: 差異最大的在前
    comparisons.sort(key=lambda x: x["abs_diff"], reverse=True)
    
    # 5. 統計
    if diffs:
        avg_diff = sum(diffs) / len(diffs)
        max_diff = max(diffs)
        direction_match_rate = sum(1 for c in comparisons if c["direction_match"]) / len(comparisons) * 100
    else:
        avg_diff = max_diff = direction_match_rate = 0
    
    return {
        "summary": {
            "common_stocks": len(common_codes),
            "only_chip": len(only_chip),
            "only_norway": len(only_norway),
            "avg_abs_diff": round(avg_diff, 3),
            "max_abs_diff": round(max_diff, 3),
            "direction_match_rate": round(direction_match_rate, 1),
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        },
        "comparisons": comparisons,
        "only_chip": sorted(list(only_chip)),
        "only_norway": sorted(list(only_norway)),
    }


def save_report(report: Dict):
    """保存交叉比對報告"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # JSON
    filepath = os.path.join(OUTPUT_DIR, "cross_analysis.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[OK] Cross analysis saved: {filepath}")
    
    # Markdown 報告
    md_path = os.path.join(OUTPUT_DIR, "cross_analysis_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 籌碼數據交叉比對報告\n\n")
        f.write(f"**分析日期**: {report['summary']['analysis_date']}\n\n")
        
        f.write("## 摘要\n\n")
        s = report["summary"]
        f.write(f"- 共同股票: **{s['common_stocks']}** 檔\n")
        f.write(f"- 僅 fortune-fred 有: **{s['only_chip']}** 檔\n")
        f.write(f"- 僅 Norway 有: **{s['only_norway']}** 檔\n")
        f.write(f"- 平均絕對差異: **{s['avg_abs_diff']}%**\n")
        f.write(f"- 最大差異: **{s['max_abs_diff']}%**\n")
        f.write(f"- 方向一致率: **{s['direction_match_rate']}%**\n\n")
        
        f.write("## 差異最大的股票 (Top 20)\n\n")
        f.write("| 排名 | 代碼 | 名稱 | fortune-fred | Norway | 差異 | 方向 |\n")
        f.write("|------|------|------|-------------|--------|------|------|\n")
        for i, c in enumerate(report["comparisons"][:20], 1):
            direction = "✅" if c["direction_match"] else "❌"
            f.write(f"| {i} | {c['stock_code']} | {c['stock_name']} | {c['chip_change']:+.2f}% | {c['norway_change']:+.2f}% | {c['diff']:+.2f}% | {direction} |\n")
        
        f.write("\n## 方向不一致的股票\n\n")
        mismatches = [c for c in report["comparisons"] if not c["direction_match"]]
        if mismatches:
            f.write("| 代碼 | 名稱 | fortune-fred | Norway |\n")
            f.write("|------|------|-------------|--------|\n")
            for c in mismatches:
                f.write(f"| {c['stock_code']} | {c['stock_name']} | {c['chip_change']:+.2f}% | {c['norway_change']:+.2f}% |\n")
        else:
            f.write("所有股票方向一致 ✅\n")
    
    print(f"[OK] Markdown report saved: {md_path}")


def main():
    print("=" * 50)
    print("籌碼數據交叉比對")
    print("=" * 50)
    
    chip = load_latest_chip_data()
    norway = load_norway_data()
    
    if not chip or not norway:
        print("[WARN] Missing data sources, skipping cross analysis")
        return
    
    report = cross_analyze(chip, norway)
    save_report(report)
    
    print(f"\n[INFO] Summary:")
    s = report["summary"]
    print(f"  Common: {s['common_stocks']}, Direction match: {s['direction_match_rate']}%")
    print(f"  Avg diff: {s['avg_abs_diff']}%, Max diff: {s['max_abs_diff']}%")


if __name__ == "__main__":
    main()
