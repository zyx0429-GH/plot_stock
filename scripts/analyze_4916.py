import json
import sys

# Redirect output to file to avoid Windows console encoding issues
output_path = 'data/4916_report.txt'
output = open(output_path, 'w', encoding='utf-8')

# fortune-fred data for 4916
with open('data/weekly_ranking.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

output.write('=== fortune-fred 4916 事欣科 (2026-05-27 抓取) ===\n')
for th in ['200', '400', '600', '800', '1000']:
    stocks = data['thresholds'].get(th, {}).get('stocks', [])
    for s in stocks:
        if s['code'] == '4916':
            output.write(f"\n門檻 >={th}張:\n")
            output.write(f"  排名: {s['rank']}\n")
            output.write(f"  排名變化: {s['rank_change']}\n")
            output.write(f"  價格: {s['price']}\n")
            output.write(f"  漲跌%: {s['change_pct']}\n")
            output.write(f"  大戶%: {s['big_holder_pct']}\n")
            output.write(f"  週增減%: {s['wow_pct']}\n")
            output.write(f"  連增週數: {s['streak']}\n")
            output.write(f"  訊號: {', '.join(s['signals'])}\n")
            break

output.write('\n\n=== norway.twsthr.info 4916 事欣科 (5/15~5/22 手動讀取) ===\n')
norway_data = [
    {"date": "2026/05/22", "price": 68.0, "change": 0.6, "change_pct": 0.89, "volume": 11855, "institutional": 419, "foreign": 327, "trust": 92, "dealer": 0, "big_holder_pct": 44.65, "big_holder_change": -0.03},
    {"date": "2026/05/21", "price": 67.4, "change": 2.4, "change_pct": 3.69, "volume": 30628, "institutional": 672, "foreign": 579, "trust": 93, "dealer": 0, "big_holder_pct": 44.68, "big_holder_change": -0.37},
    {"date": "2026/05/20", "price": 65.0, "change": 2.2, "change_pct": 3.50, "volume": 32293, "institutional": 537, "foreign": 483, "trust": 54, "dealer": 0, "big_holder_pct": 45.05, "big_holder_change": 0.28},
    {"date": "2026/05/19", "price": 62.8, "change": 0.4, "change_pct": 0.64, "volume": 15272, "institutional": 43, "foreign": 47, "trust": -4, "dealer": 0, "big_holder_pct": 44.77, "big_holder_change": 0.05},
    {"date": "2026/05/18", "price": 62.4, "change": 1.8, "change_pct": 2.97, "volume": 34897, "institutional": 302, "foreign": 228, "trust": 74, "dealer": 0, "big_holder_pct": 44.72, "big_holder_change": -0.68},
    {"date": "2026/05/17", "price": 60.6, "change": 1.1, "change_pct": 1.85, "volume": 14405, "institutional": 230, "foreign": 212, "trust": 18, "dealer": 0, "big_holder_pct": 45.40, "big_holder_change": 0.13},
    {"date": "2026/05/16", "price": 59.5, "change": 2.1, "change_pct": 3.66, "volume": 24804, "institutional": 384, "foreign": 370, "trust": 14, "dealer": 0, "big_holder_pct": 45.27, "big_holder_change": -0.06},
    {"date": "2026/05/15", "price": 57.4, "change": 0.8, "change_pct": 1.41, "volume": 10923, "institutional": 109, "foreign": 107, "trust": 2, "dealer": 0, "big_holder_pct": 45.33, "big_holder_change": -0.12},
]

print('\n日期        | 收盤價 | 漲跌  | 漲跌%  | 成交量  | 三大法人 | 外資   | 投信  | 自營商 | 大戶%   | 大戶增減')
print('-' * 110)
for d in norway_data:
    print(f"{d['date']} | {d['price']:>6.1f} | {d['change']:>+5.1f} | {d['change_pct']:>+5.2f}% | {d['volume']:>7,} | {d['institutional']:>+7,} | {d['foreign']:>+6,} | {d['trust']:>+5,} | {d['dealer']:>+6,} | {d['big_holder_pct']:>5.2f}% | {d['big_holder_change']:>+6.2f}%")

# Calculate some stats
print('\n=== 統計 ===')
print(f"期間漲幅: {norway_data[0]['price'] - norway_data[-1]['price']:.1f} ({((norway_data[0]['price'] / norway_data[-1]['price']) - 1) * 100:.2f}%)")
print(f"最高價: {max(d['price'] for d in norway_data):.1f} ({max(norway_data, key=lambda x: x['price'])['date']})")
print(f"最低價: {min(d['price'] for d in norway_data):.1f} ({min(norway_data, key=lambda x: x['price'])['date']})")
print(f"總成交量: {sum(d['volume'] for d in norway_data):,}")
print(f"外資累積買超: {sum(d['foreign'] for d in norway_data):+,}")
print(f"大戶%變化: {norway_data[0]['big_holder_pct'] - norway_data[-1]['big_holder_pct']:+.2f}%")

# Estimate cost (volume-weighted average)
total_value = sum(d['price'] * d['volume'] for d in norway_data)
total_volume = sum(d['volume'] for d in norway_data)
vwap = total_value / total_volume
print(f"\n期間均價 (VWAP): {vwap:.2f}")
print(f"成本區間估計: {min(d['price'] for d in norway_data):.1f} ~ {max(d['price'] for d in norway_data):.1f}")

# Save to file
report = {
    "stock": "4916 事欣科",
    "period": "2026-05-15 ~ 2026-05-22",
    "sources": ["fortune-fred.github.io/plot_stock", "norway.twsthr.info"],
    "fortune_fred": {
        "rank": 1,
        "big_holder_pct": "50.96%",
        "wow_change": "+11.91%",
        "streak": "連增3",
        "signals": ["加速", "新進榜", "內外共振", "高波動警示"]
    },
    "norway_daily": norway_data,
    "summary": {
        "period_return_pct": round(((norway_data[0]['price'] / norway_data[-1]['price']) - 1) * 100, 2),
        "total_volume": sum(d['volume'] for d in norway_data),
        "foreign_net": sum(d['foreign'] for d in norway_data),
        "vwap": round(vwap, 2),
        "big_holder_change": round(norway_data[0]['big_holder_pct'] - norway_data[-1]['big_holder_pct'], 2)
    }
}

with open('data/4916_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

output.write('\n報告已保存: data/4916_analysis.json\n')
output.write('文字報告已保存: data/4916_report.txt\n')
output.close()
print('Done. Reports saved to data/4916_analysis.json and data/4916_report.txt')
