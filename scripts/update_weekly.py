#!/usr/bin/env python3
"""
组合脚本：抓取 fortune-fred weekly_ranking 数据 + 生成 HTML
用于 GitHub Actions 每周自动更新
"""
import sys
import os

# 确保 plot_stock 目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_weekly_ranking import main as fetch_main
from generate_weekly_html import main as generate_main

def main():
    print("=" * 50)
    print("Weekly Ranking Update Pipeline")
    print("=" * 50)
    
    # Step 1: Fetch data
    print("\n[1/2] Fetching data from fortune-fred...")
    fetch_main()
    
    # Step 2: Generate HTML
    print("\n[2/2] Generating weekly_ranking.html...")
    generate_main()
    
    print("\nDone! Check docs/weekly_ranking.html")

if __name__ == '__main__':
    main()
