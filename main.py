#!/usr/bin/env python3
"""
智董籌碼選股站 - 主入口
執行順序: 抓取資料 → 大戶籌碼 → 選股篩選 → 生成網頁
"""

import sys
import os

# 將 scripts 加入路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from scripts.data_fetcher import fetch_all
from scripts.stock_screener import run_screening
from scripts.generate_html import generate
from scripts.cross_analysis import main as run_cross_analysis

def run_norway_fetch():
    """執行 Norway 大戶籌碼抓取"""
    print("\n[INFO] Step 1.2: 抓取 Norway 大戶籌碼數據...")
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/norway_fetcher_v2.py"],
            capture_output=True, text=True, timeout=120
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"[WARN] Norway fetcher stderr: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"[WARN] Norway fetcher failed: {e}")
        return False

def main():
    print("=" * 60)
    print("[INFO] 智董籌碼選股站 - 每日更新開始")
    print("=" * 60)

    # Step 1: 抓取台股盤後資料
    print("\n[INFO] Step 1/4: 抓取台股資料...")
    fetch_all()

    # Step 1.2: 抓取 Norway 大戶籌碼
    norway_ok = run_norway_fetch()
    if not norway_ok:
        print("[WARN] Norway 大戶籌碼抓取失敗，使用上次數據")

    # Step 1.5: 交叉比對
    print("\n[INFO] Step 1.5: 執行籌碼數據交叉比對...")
    run_cross_analysis()

    # Step 2: 選股篩選
    print("\n[INFO] Step 2/3: 執行選股邏輯...")
    run_screening()

    # Step 3: 生成網頁
    print("\n[INFO] Step 3/3: 生成靜態網頁...")
    generate()

    print("\n" + "=" * 60)
    print("[OK] 全部完成！請打開 docs/index.html 預覽")
    print("=" * 60)

if __name__ == "__main__":
    main()
