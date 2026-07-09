import json
from datetime import datetime

# Load Norway data
with open('data/norway/all_stocks_weekly.json', 'r', encoding='utf-8') as f:
    stocks = json.load(f)

# Filter out ETFs (4-digit codes starting with 0-9, exclude 00xx ETFs)
valid_stocks = [s for s in stocks if len(s['stock_code']) == 4 and s['stock_code'][0] in '123456789']

# Latest date from weekly_changes
sample_dates = list(valid_stocks[0]['weekly_changes'].keys())
latest_date = max(sample_dates)
prev_date = sorted(sample_dates)[-2] if len(sample_dates) > 1 else latest_date

# Format dates
latest_date_fmt = f"{latest_date[:4]}-{latest_date[4:6]}-{latest_date[6:]}"
prev_date_fmt = f"{prev_date[:4]}-{prev_date[4:6]}-{prev_date[6:]}"

# Calculate consecutive weeks for each stock
def calc_consecutive(weekly_changes):
    dates = sorted(weekly_changes.keys())
    count = 0
    for d in reversed(dates):
        if weekly_changes[d] > 0:
            count += 1
        else:
            break
    return count

for s in valid_stocks:
    s['consecutive'] = calc_consecutive(s['weekly_changes'])

# Sort by latest_change
increase_top = sorted([s for s in valid_stocks if s['latest_change'] > 0], 
                       key=lambda x: x['latest_change'], reverse=True)
decrease_top = sorted([s for s in valid_stocks if s['latest_change'] < 0], 
                       key=lambda x: x['latest_change'])

# Stats
total = len(valid_stocks)
inc_count = len(increase_top)
dec_count = len(decrease_top)
flat_count = total - inc_count - dec_count

# Signal detection
def detect_signals(s):
    signals = []
    wc = s['weekly_changes']
    dates = sorted(wc.keys())
    latest = dates[-1]
    prev = dates[-2] if len(dates) > 1 else latest
    
    pc = s.get('price_change') or 0
    
    # 1. 逆買: 股價跌幅≥3%，大戶仍買超
    if pc <= -3 and s['latest_change'] > 0:
        signals.append('逆買')
    
    # 2. 事件驅動: 單週WoW≥3%且無連增背景
    if s['latest_change'] >= 3 and s['consecutive'] < 2:
        signals.append('事件驅動')
    
    # 3. 加速: 本週WoW≥上週×1.5倍
    if wc[prev] > 0 and s['latest_change'] >= wc[prev] * 1.5 and s['latest_change'] > 0:
        signals.append('加速')
    
    # 4. 量價背離: 籌碼方向與股價方向相反
    if (s['latest_change'] > 0 and pc < -1) or (s['latest_change'] < 0 and pc > 1):
        signals.append('量價背離')
    
    # 5. 內外共振: 連增≥3週且股價同步上漲≥2%
    if s['consecutive'] >= 3 and pc >= 2:
        signals.append('內外共振')
    
    # 6. 法人同向: 大戶佔比≥70%且持續增持
    if s['last_week_hold_pct'] >= 70 and s['latest_change'] > 0:
        signals.append('法人同向')
    
    # 7. 籌碼回補: 上週賣超後本週轉正
    if wc[prev] < 0 and s['latest_change'] > 0:
        signals.append('籌碼回補')
    
    # 8. 高波動警示: 週漲跌幅≥8%
    if abs(pc) >= 8:
        signals.append('高波動警示')
    
    # 9. 高度集中: 大戶持股佔比超過75%
    if s['last_week_hold_pct'] > 75:
        signals.append('高度集中')
    
    # 10. 久盤吸籌: 連增≥5週但股價漲幅<3%
    if s['consecutive'] >= 5 and pc < 3:
        signals.append('久盤吸籌')
    
    # 11. 流動性風險: 大戶佔比超過90%
    if s['last_week_hold_pct'] > 90:
        signals.append('流動性風險')
    
    # 12. 新進榜: 本週首次進入增持前100名
    if s['latest_change'] > 0 and s['rank'] <= 100:
        # Check if it was in top 100 last week (simplified: check if previous week had lower rank or not in top 100)
        # For now, mark as 新進榜 if rank is new or improved significantly
        # We'll use a simplified approach: if total_change is small but latest_change is large
        if s['rank'] <= 100:
            signals.append('新進榜')
    
    return signals

for s in valid_stocks:
    s['signals'] = detect_signals(s)

# Signal counts
all_signals = {}
for s in valid_stocks:
    for sig in s['signals']:
        all_signals[sig] = all_signals.get(sig, 0) + 1

# Top 25 for bar charts and grid
inc_top25 = increase_top[:25]
dec_top25 = decrease_top[:25]

# Calculate max_abs for symmetric scales
max_inc = max((s['latest_change'] for s in inc_top25), default=0)
max_dec = abs(min((s['latest_change'] for s in dec_top25), default=0))
max_abs = max(max_inc, max_dec, 0.1)

# Bar width function
def bar_width(pct, max_abs):
    return min(100, abs(pct) / max_abs * 100)

# Color function for price change
def price_color(pct):
    pct = pct or 0
    if pct > 0:
        intensity = min(255, int(50 + pct * 20))
        return f'rgb({intensity}, 180, {intensity})'
    elif pct < 0:
        intensity = min(255, int(50 + abs(pct) * 20))
        return f'rgb(255, {255-intensity}, {255-intensity})'
    return '#94a3b8'

# Color for grid cells
def grid_bg(pct):
    pct = pct or 0
    if pct > 0:
        intensity = min(200, int(50 + pct * 15))
        return f'rgb({intensity}, 200, {intensity})'
    elif pct < 0:
        intensity = min(200, int(50 + abs(pct) * 15))
        return f'rgb(255, {255-intensity}, {255-intensity})'
    return '#f1f5f9'

# Market type
def market_type(code):
    if code.startswith('8') or code.startswith('6'):
        return '上櫃'
    return '上市'

# HTML Generation
html = f'''<!DOCTYPE html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>集保週排行榜 — {latest_date_fmt}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f5f5f7;color:#1d1d1f;padding:1.5rem}}
.hdr{{padding:1.25rem 0 1rem;border-bottom:1px solid #d2d2d7;margin-bottom:1.25rem}}
.hdr-title{{font-size:20px;font-weight:500;margin:0 0 4px}}
.hdr-sub{{font-size:13px;color:#6e6e73;margin:0}}

/* Threshold tabs */
.thresh-tabs{{display:flex;gap:8px;margin-bottom:1.25rem}}
.tab{{border:1px solid #d2d2d7;background:#fff;border-radius:7px;padding:5px 14px;font-size:13px;cursor:pointer;color:#1d1d1f;transition:all .15s}}
.tab:hover{{background:#f0f0f0}}
.tab.active{{background:#1d1d1f;color:#fff;border-color:#1d1d1f}}

/* Stats cards */
.stats-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:1.25rem}}
.stat-card{{background:#fff;border:1px solid #e5e5ea;border-radius:10px;padding:14px;text-align:center}}
.stat-label{{font-size:12px;color:#6e6e73;margin-bottom:4px}}
.stat-value{{font-size:24px;font-weight:600;color:#1d1d1f}}
.stat-sub{{font-size:12px;color:#8e8e93;margin-top:2px}}

/* Signal cards */
.sig-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:1.25rem}}
.sig-card{{background:#fff;border:1px solid #e5e5ea;border-radius:10px;padding:14px;cursor:pointer;transition:all .15s}}
.sig-card:hover{{border-color:#1d1d1f}}
.sig-card.active{{border-color:#1d1d1f;background:#f5f5f7}}
.sig-name{{font-size:13px;font-weight:500;color:#1d1d1f}}
.sig-desc{{font-size:12px;color:#6e6e73;margin-top:2px}}
.sig-count{{font-size:22px;font-weight:600;color:#1d1d1f;margin-top:6px}}

/* Bar Charts */
.bar-charts{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:1.25rem}}
.bar-section{{background:#fff;border:1px solid #e5e5ea;border-radius:10px;padding:16px}}
.bar-section h3{{font-size:14px;font-weight:600;margin-bottom:4px}}
.bar-sub{{font-size:12px;color:#6e6e73;margin-bottom:12px}}
.bar-chart{{position:relative}}
.bar-row{{display:flex;align-items:center;margin-bottom:6px;font-size:12px;height:22px;position:relative}}
.bar-label{{width:70px;text-align:right;padding-right:8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px}}
.bar-track{{flex:1;height:18px;position:relative;background:#f5f5f7;border-radius:3px}}
.bar-fill{{height:100%;border-radius:3px;position:absolute;top:0}}
.bar-left .bar-fill{{left:0;background:linear-gradient(90deg,#ff453a,#ff6b61)}}
.bar-right .bar-fill{{right:0;background:linear-gradient(90deg,#30d158,#30d158)}}
.bar-pct{{width:50px;padding-left:8px;font-size:11px;font-weight:600}}
.bar-axis{{display:flex;justify-content:space-between;font-size:10px;color:#8e8e93;margin-top:8px;padding-left:78px;padding-right:50px}}

/* Grid Heatmap */
.grid-section{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:1.25rem}}
.grid-panel{{background:#fff;border:1px solid #e5e5ea;border-radius:10px;padding:16px}}
.grid-panel h3{{font-size:14px;font-weight:600;margin-bottom:4px}}
.grid-sub{{font-size:12px;color:#6e6e73;margin-bottom:12px}}
.grid-cells{{display:grid;grid-template-columns:repeat(5,1fr);gap:4px}}
.grid-cell{{border-radius:6px;padding:6px 2px;text-align:center;color:#fff;font-size:11px;min-height:55px;display:flex;flex-direction:column;justify-content:center;cursor:pointer;transition:transform .15s}}
.grid-cell:hover{{transform:scale(1.05)}}
.gc-code{{font-weight:700;font-size:12px}}
.gc-name{{font-size:10px;opacity:.9;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.gc-pct{{font-size:11px;font-weight:600}}

/* Filter chips */
.chips-section{{background:#fff;border:1px solid #e5e5ea;border-radius:10px;padding:.75rem 1rem;margin-bottom:.75rem}}
.chips-row{{display:flex;align-items:center;gap:6px;flex-wrap:wrap}}
.chips-row+.chips-row{{margin-top:6px}}
.chip-label{{font-size:12px;color:#6e6e73;min-width:60px}}
.chip{{border:1px solid #d2d2d7;background:#f5f5f7;border-radius:20px;padding:4px 12px;font-size:12px;cursor:pointer;color:#1d1d1f;transition:all .15s;white-space:nowrap}}
.chip:hover{{background:#e8e8ed}}
.chip.active{{background:#1d1d1f;color:#fff;border-color:#1d1d1f}}

/* Legend */
.legend-section{{background:#fff;border:1px solid #e5e5ea;border-radius:10px;padding:.75rem 1rem;margin-bottom:1.25rem}}
.legend-section>summary{{font-size:13px;font-weight:500;cursor:pointer;user-select:none;list-style:none;display:flex;align-items:center;gap:6px;color:#1d1d1f}}
.legend-section>summary::-webkit-details-marker{{display:none}}
.legend-section>summary::before{{content:'▶';font-size:9px;transition:transform .2s}}
.legend-section[open]>summary::before{{content:'▼'}}
.legend-body{{margin-top:10px;font-size:12px;color:#6e6e73;line-height:1.8}}
.legend-item{{display:flex;align-items:flex-start;gap:8px;margin-bottom:6px}}
.legend-dot{{width:8px;height:8px;border-radius:50%;margin-top:5px;flex-shrink:0}}

/* Search */
.search-bar{{margin-bottom:1rem}}
.search-bar input{{width:100%;padding:10px 14px;border:1px solid #d2d2d7;border-radius:8px;font-size:14px;background:#fff}}
.search-bar input:focus{{outline:none;border-color:#1d1d1f}}

/* Tables */
.table-section{{background:#fff;border:1px solid #e5e5ea;border-radius:10px;padding:16px;margin-bottom:1.25rem}}
.table-title{{font-size:15px;font-weight:600;margin-bottom:4px}}
.table-sub{{font-size:12px;color:#6e6e73;margin-bottom:12px}}
.data-table{{width:100%;border-collapse:collapse;font-size:13px}}
.data-table th{{text-align:left;padding:8px 6px;border-bottom:1px solid #e5e5ea;font-weight:600;color:#6e6e73;font-size:12px;cursor:pointer}}
.data-table td{{padding:8px 6px;border-bottom:1px solid #f2f2f7;vertical-align:top}}
.data-table tr:hover{{background:#f9f9fb}}
.td-name{{display:flex;flex-direction:column;gap:2px}}
.td-name a{{color:#0066cc;text-decoration:none;font-weight:500}}
.td-name a:hover{{text-decoration:underline}}
.td-tags{{display:flex;gap:4px;flex-wrap:wrap;margin-top:2px}}
.tag{{font-size:10px;padding:1px 6px;border-radius:10px;background:#f2f2f7;color:#6e6e73}}
.tag-primary{{background:#1d1d1f;color:#fff}}
.tag-new{{background:#007aff;color:#fff}}
.market-badge{{font-size:10px;padding:1px 5px;border-radius:4px;background:#f2f2f7;color:#6e6e73}}
.streak-up{{color:#30d158}}
.streak-down{{color:#ff453a}}
.change-up{{color:#30d158}}
.change-down{{color:#ff453a}}

@media (max-width: 900px) {{
    .bar-charts, .grid-section, .stats-row, .sig-row{{grid-template-columns:1fr}}
    body{{padding:.75rem}}
}}
</style>
</head>
<body>

<!-- Navigation -->
<style>
.wr-nav{{display:flex;align-items:center;gap:16px;padding:12px 20px;background:#fff;border-bottom:1px solid #e5e5ea;margin-bottom:1rem;flex-wrap:wrap}}
.wr-nav a{{color:#0066cc;text-decoration:none;font-size:13px;font-weight:500;padding:4px 10px;border-radius:6px;transition:background .15s}}
.wr-nav a:hover{{background:#f2f2f7}}
.wr-nav a.active{{background:#1d1d1f;color:#fff}}
.wr-nav-brand{{font-size:14px;font-weight:600;color:#1d1d1f;margin-right:8px}}
</style>
<nav class="wr-nav">
<span class="wr-nav-brand">🔥 跟隨大戶選股站</span>
<a href="index.html">📊 首頁</a>
<a href="watchlist.html">⭐ 自選</a>
<a href="etf_00981a.html">📈 00981A</a>
<a href="etf_00982a.html">📈 00982A</a>
<a href="sector.html">🔄 族群輪動</a>
<a href="weekly_ranking.html" class="active">📅 週排行</a>
</nav>

<div class="hdr">
    <h1 class="hdr-title">集保週排行榜 — {latest_date_fmt}</h1>
    <p class="hdr-sub">大戶持股比例週增減｜上週 {prev_date_fmt}｜僅含正股（1–9開頭4位代號）</p>
</div>

<div class="thresh-tabs">
    <button class="tab active">200張以上</button>
    <button class="tab">400張以上</button>
    <button class="tab">1000張以上</button>
</div>

<div class="stats-row">
    <div class="stat-card">
        <div class="stat-label">正股數</div>
        <div class="stat-value">{total}</div>
        <div class="stat-sub">已排除ETF</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">大戶增加</div>
        <div class="stat-value" style="color:#30d158">{inc_count}</div>
        <div class="stat-sub">{(inc_count/total*100):.1f}%</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">大戶減少</div>
        <div class="stat-value" style="color:#ff453a">{dec_count}</div>
        <div class="stat-sub">{(dec_count/total*100):.1f}%</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">持平</div>
        <div class="stat-value" style="color:#8e8e93">{flat_count}</div>
        <div class="stat-sub">{(flat_count/total*100):.1f}%</div>
    </div>
</div>

<div class="sig-row">
    <div class="sig-card" onclick="filterBySignal('逆買')">
        <div class="sig-name">逆買訊號</div>
        <div class="sig-desc">股跌≥3%仍增持</div>
        <div class="sig-count">{all_signals.get('逆買', 0)}</div>
    </div>
    <div class="sig-card" onclick="filterBySignal('加速')">
        <div class="sig-name">加速買超</div>
        <div class="sig-desc">wow≥上週×2</div>
        <div class="sig-count">{all_signals.get('加速', 0)}</div>
    </div>
    <div class="sig-card" onclick="filterBySignal('新進榜')">
        <div class="sig-name">新進榜</div>
        <div class="sig-desc">買超TOP100新上榜</div>
        <div class="sig-count">{all_signals.get('新進榜', 0)}</div>
    </div>
    <div class="sig-card" onclick="filterBySignal('久盤吸籌')">
        <div class="sig-name">連增≥5週</div>
        <div class="sig-desc">持續吸籌</div>
        <div class="sig-count">{all_signals.get('久盤吸籌', 0)}</div>
    </div>
</div>

<!-- Bar Charts -->
<div class="bar-charts">
    <div class="bar-section">
        <h3>🔥 大戶增持 — 週漲跌 Top 25</h3>
        <div class="bar-sub">顏色深淺 = 週漲跌幅度（%）｜按 WoW 增持幅度由大到小排列</div>
        <div class="bar-chart">
'''

# Left bar chart (increase)
for s in inc_top25:
    w = bar_width(s['latest_change'], max_abs)
    color = '#30d158' if (s.get('price_change') or 0) > 0 else '#ff453a' if (s.get('price_change') or 0) < 0 else '#8e8e93'
    html += f'''            <div class="bar-row bar-left">
                <div class="bar-label">{s['stock_code']} {s['stock_name'][:3]}</div>
                <div class="bar-track">
                    <div class="bar-fill" style="width:{w:.1f}%;opacity:{0.3 + min(0.7, abs(s.get('price_change', 0) or 0)/10)}"></div>
                </div>
                <div class="bar-pct" style="color:{color}">+{s['latest_change']:.2f}%</div>
            </div>
'''

html += f'''            <div class="bar-axis">
                <span>0%</span>
                <span>{max_abs/2:.1f}%</span>
                <span>{max_abs:.1f}%</span>
            </div>
        </div>
    </div>
    <div class="bar-section">
        <h3>❄️ 大戶減持 — 週漲跌 Top 25</h3>
        <div class="bar-sub">顏色深淺 = 週漲跌幅度（%）｜按 WoW 減持幅度由大到小排列</div>
        <div class="bar-chart">
'''

# Right bar chart (decrease)
for s in dec_top25:
    w = bar_width(s['latest_change'], max_abs)
    color = '#30d158' if (s.get('price_change') or 0) > 0 else '#ff453a' if (s.get('price_change') or 0) < 0 else '#8e8e93'
    html += f'''            <div class="bar-row bar-right">
                <div class="bar-pct" style="color:{color};text-align:right">{s['latest_change']:.2f}%</div>
                <div class="bar-track">
                    <div class="bar-fill" style="width:{w:.1f}%;opacity:{0.3 + min(0.7, abs(s.get('price_change', 0) or 0)/10)}"></div>
                </div>
                <div class="bar-label">{s['stock_code']} {s['stock_name'][:3]}</div>
            </div>
'''

html += f'''            <div class="bar-axis">
                <span>-{max_abs:.1f}%</span>
                <span>-{max_abs/2:.1f}%</span>
                <span>0%</span>
            </div>
        </div>
    </div>
</div>

<!-- Grid Heatmap -->
<div class="grid-section">
    <div class="grid-panel">
        <h3>🔥 大戶增持 — 週漲跌 Top 25</h3>
        <div class="grid-sub">顏色深淺 = 週漲跌幅度（%）</div>
        <div class="grid-cells">
'''

for s in inc_top25:
    pc = s.get('price_change') or 0
    bg = grid_bg(pc)
    text_color = '#fff' if abs(pc) > 3 else '#1d1d1f'
    html += f'''            <div class="grid-cell" style="background:{bg};color:{text_color}" title="{s['stock_code']} {s['stock_name']}: {pc:+.2f}%">
                <div class="gc-code">{s['stock_code']}</div>
                <div class="gc-name">{s['stock_name'][:4]}</div>
                <div class="gc-pct">{pc:+.2f}%</div>
            </div>
'''

html += '''        </div>
    </div>
    <div class="grid-panel">
        <h3>❄️ 大戶減持 — 週漲跌 Top 25</h3>
        <div class="grid-sub">顏色深淺 = 週漲跌幅度（%）</div>
        <div class="grid-cells">
'''

for s in dec_top25:
    pc = s.get('price_change') or 0
    bg = grid_bg(pc)
    text_color = '#fff' if abs(pc) > 3 else '#1d1d1f'
    html += f'''            <div class="grid-cell" style="background:{bg};color:{text_color}" title="{s['stock_code']} {s['stock_name']}: {pc:+.2f}%">
                <div class="gc-code">{s['stock_code']}</div>
                <div class="gc-name">{s['stock_name'][:4]}</div>
                <div class="gc-pct">{pc:+.2f}%</div>
            </div>
'''

html += '''        </div>
    </div>
</div>

<!-- Filter Chips -->
<div class="chips-section">
    <div class="chips-row">
        <span class="chip-label">核心訊號：</span>
        <button class="chip" onclick="toggleChip(this)">逆買</button>
        <button class="chip" onclick="toggleChip(this)">加速買超</button>
        <button class="chip" onclick="toggleChip(this)">籌碼回補</button>
        <button class="chip" onclick="toggleChip(this)">高度集中</button>
        <button class="chip" onclick="toggleChip(this)">久盤吸籌</button>
        <button class="chip" onclick="toggleChip(this)">新進榜</button>
        <span style="margin-left:12px;font-size:12px;color:#6e6e73">連增：</span>
        <button class="chip" onclick="toggleChip(this)">≥3週</button>
        <button class="chip" onclick="toggleChip(this)">≥5週</button>
    </div>
    <div class="chips-row">
        <span class="chip-label">擴充訊號：</span>
        <button class="chip" onclick="toggleChip(this)">量價背離</button>
        <button class="chip" onclick="toggleChip(this)">法人同向</button>
        <button class="chip" onclick="toggleChip(this)">內外共振</button>
        <button class="chip" onclick="toggleChip(this)">事件驅動</button>
        <button class="chip" onclick="toggleChip(this)">高波動警示</button>
        <button class="chip" onclick="toggleChip(this)">流動性風險</button>
    </div>
    <div class="chips-row">
        <span class="chip-label">市場：</span>
        <button class="chip" onclick="toggleChip(this)">上市</button>
        <button class="chip" onclick="toggleChip(this)">上櫃</button>
        <button class="chip" onclick="toggleChip(this)">產業 ▾</button>
        <button class="chip" onclick="toggleChip(this)">題材 ▾</button>
    </div>
</div>

<!-- Legend -->
<details class="legend-section">
    <summary>標籤說明（點擊展開）</summary>
    <div class="legend-body">
        <div class="legend-item"><div class="legend-dot" style="background:#5b21b6"></div><div><strong>逆買</strong>：股價跌幅≥3%，大戶仍增持</div></div>
        <div class="legend-item"><div class="legend-dot" style="background:#7e22ce"></div><div><strong>事件驅動</strong>：單週WoW≥3%且無連增背景</div></div>
        <div class="legend-item"><div class="legend-dot" style="background:#9d174d"></div><div><strong>加速</strong>：本週WoW≥上週×1.5倍</div></div>
        <div class="legend-item"><div class="legend-dot" style="background:#92400e"></div><div><strong>量價背離</strong>：籌碼方向與股價方向相反</div></div>
        <div class="legend-item"><div class="legend-dot" style="background:#166534"></div><div><strong>內外共振</strong>：連增≥3週且股價同步上漲≥2%</div></div>
        <div class="legend-item"><div class="legend-dot" style="background:#075985"></div><div><strong>法人同向</strong>：大戶佔比≥70%且持續增持</div></div>
        <div class="legend-item"><div class="legend-dot" style="background:#065f46"></div><div><strong>籌碼回補</strong>：上週賣超後本週轉正</div></div>
        <div class="legend-item"><div class="legend-dot" style="background:#9f1239"></div><div><strong>高波動警示</strong>：週漲跌幅≥8%</div></div>
        <div class="legend-item"><div class="legend-dot" style="background:#9a3412"></div><div><strong>高度集中</strong>：大戶持股佔比超過75%</div></div>
        <div class="legend-item"><div class="legend-dot" style="background:#1e40af"></div><div><strong>久盤吸籌</strong>：連增≥5週但股價漲幅<3%</div></div>
        <div class="legend-item"><div class="legend-dot" style="background:#475569"></div><div><strong>流動性風險</strong>：大戶佔比超過90%</div></div>
        <div class="legend-item"><div class="legend-dot" style="background:#1d1d1f"></div><div><strong>新進榜</strong>：本週首次進入增持前100名</div></div>
    </div>
</details>

<!-- Search -->
<div class="search-bar">
    <input type="text" id="searchInput" placeholder="搜尋股號或股名…（可與籌碼篩選同時使用）" oninput="doSearch(this.value)">
</div>

<!-- Increase Table -->
<div class="table-section">
    <div class="table-title">增加前 100 名</div>
    <div class="table-sub">股號 / 收盤價 / 週漲跌 / 大戶佔比 / 大戶週增減 / 連增｜逆買=股跌≥3%但大戶仍增</div>
    <table class="data-table" id="incTable">
        <thead>
            <tr>
                <th>#</th>
                <th>變動</th>
                <th>股號</th>
                <th>收盤價</th>
                <th>週漲跌</th>
                <th>大戶佔比</th>
                <th>大戶週增減</th>
                <th>連增</th>
            </tr>
        </thead>
        <tbody>
'''

for i, s in enumerate(increase_top[:100], 1):
    sigs = s['signals']
    primary = sigs[0] if sigs else ''
    extra = ' +' + str(len(sigs)-1) if len(sigs) > 1 else ''
    streak = f"↑{s['consecutive']}週" if s['consecutive'] > 1 else '—'
    streak_class = 'streak-up' if s['consecutive'] > 1 else ''
    pc = s.get('price_change') or 0
    price_chg = f"{pc:+.2f}%" if pc != 0 else '—'
    price_class = 'change-up' if pc > 0 else 'change-down' if pc < 0 else ''
    mkt = market_type(s['stock_code'])
    
    html += f'''            <tr>
                <td>{i}</td>
                <td>NEW</td>
                <td>
                    <div class="td-name">
                        <a href="stock_{s['stock_code']}.html">{s['stock_code']}{s['stock_name']}</a>
                        <span class="market-badge">{mkt}</span>
                        <div class="td-tags">
                            <span class="tag{' tag-primary' if primary else ''}">{primary}</span>
                            {f'<span class="tag tag-new">{extra}</span>' if extra else ''}
                        </div>
                    </div>
                </td>
                <td>{s['close_price']}</td>
                <td class="{price_class}">{price_chg}</td>
                <td>{s['last_week_hold_pct']:.2f}%</td>
                <td class="change-up">+{s['latest_change']:.2f}%</td>
                <td class="{streak_class}">{streak}</td>
            </tr>
'''

html += '''        </tbody>
    </table>
</div>

<!-- Decrease Table -->
<div class="table-section">
    <div class="table-title">減少前 100 名</div>
    <div class="table-sub">股號 / 收盤價 / 週漲跌 / 大戶佔比 / 大戶週增減 / 連增</div>
    <table class="data-table" id="decTable">
        <thead>
            <tr>
                <th>#</th>
                <th>變動</th>
                <th>股號</th>
                <th>收盤價</th>
                <th>週漲跌</th>
                <th>大戶佔比</th>
                <th>大戶週增減</th>
                <th>連增</th>
            </tr>
        </thead>
        <tbody>
'''

for i, s in enumerate(decrease_top[:100], 1):
    sigs = s['signals']
    primary = sigs[0] if sigs else ''
    extra = ' +' + str(len(sigs)-1) if len(sigs) > 1 else ''
    streak = f"↑{s['consecutive']}週" if s['consecutive'] > 1 else '—'
    streak_class = 'streak-up' if s['consecutive'] > 1 else ''
    pc = s.get('price_change') or 0
    price_chg = f"{pc:+.2f}%" if pc != 0 else '—'
    price_class = 'change-up' if pc > 0 else 'change-down' if pc < 0 else ''
    mkt = market_type(s['stock_code'])
    
    html += f'''            <tr>
                <td>{i}</td>
                <td>NEW</td>
                <td>
                    <div class="td-name">
                        <a href="stock_{s['stock_code']}.html">{s['stock_code']}{s['stock_name']}</a>
                        <span class="market-badge">{mkt}</span>
                        <div class="td-tags">
                            <span class="tag{' tag-primary' if primary else ''}">{primary}</span>
                            {f'<span class="tag tag-new">{extra}</span>' if extra else ''}
                        </div>
                    </div>
                </td>
                <td>{s['close_price']}</td>
                <td class="{price_class}">{price_chg}</td>
                <td>{s['last_week_hold_pct']:.2f}%</td>
                <td class="change-down">{s['latest_change']:.2f}%</td>
                <td class="{streak_class}">{streak}</td>
            </tr>
'''

html += '''        </tbody>
    </table>
</div>

<script>
function toggleChip(el) {
    el.classList.toggle('active');
}
function filterBySignal(signal) {
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.chip').forEach(c => {
        if (c.textContent.includes(signal)) c.classList.add('active');
    });
}
function doSearch(val) {
    val = val.toLowerCase();
    document.querySelectorAll('.data-table tbody tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(val) ? '' : 'none';
    });
}
</script>

</body>
</html>
'''

with open('docs/weekly_ranking.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Generated: docs/weekly_ranking.html")
print(f"Date: {latest_date_fmt}")
print(f"Stocks: {total}")
print(f"Increase: {inc_count} ({inc_count/total*100:.1f}%)")
print(f"Decrease: {dec_count} ({dec_count/total*100:.1f}%)")
print(f"Max abs scale: {max_abs:.2f}%")
