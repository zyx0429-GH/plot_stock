#!/usr/bin/env python3
"""
生成 docs/weekly_ranking.html — 大戶籌碼週排行榜
数据来源: fortune-fred.github.io/plot_stock/weekly_ranking.html
"""

import json
import os
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'weekly_ranking.json')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'docs', 'weekly_ranking.html')

# 信号标签颜色映射
SIGNAL_COLORS = {
    '逆買': '#2563eb',
    '事件驅動': '#7c3aed',
    '加速': '#dc2626',
    '量價背離': '#f59e0b',
    '內外共振': '#0891b2',
    '法人同向': '#059669',
    '籌碼回補': '#ea580c',
    '高波動警示': '#be123c',
    '高度集中': '#4338ca',
    '久盤吸籌': '#65a30d',
    '流動性風險': '#94a3b8',
    '新進榜': '#0ea5e9',
}

# 连增周数标签颜色
STREAK_COLORS = {
    '連增3': '#f59e0b',
    '連增5': '#dc2626',
    '連增7': '#7f1d1d',
}

def load_data():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def render_badge(text, color='#2563eb'):
    return f'<span class="signal-badge" style="background:{color}15;color:{color};border:1px solid {color}30">{text}</span>'

def render_signal_badges(signals):
    badges = []
    for sig in signals:
        # Skip theme tags
        if sig.startswith('theme:'):
            continue
        color = SIGNAL_COLORS.get(sig, '#64748b')
        badges.append(render_badge(sig, color))
    return ' '.join(badges)

def render_streak_badge(streak):
    if not streak or streak == '—':
        return ''
    return f'<span class="streak-badge">{streak}</span>'

def updown_class(val):
    if val.startswith('+'):
        return 'up'
    elif val.startswith('-'):
        return 'down'
    return ''

def generate_html(data):
    fetched = data.get('fetched_at', '')[:10]
    thresholds = data.get('thresholds', {})
    signal_counts = data.get('signal_counts', {})
    
    # Sort signal counts (excluding themes)
    sorted_signals = sorted(
        [(k, v) for k, v in signal_counts.items() if not k.startswith('theme:')],
        key=lambda x: -x[1]
    )
    
    # Generate signal stats cards
    stats_html = ''
    for sig, count in sorted_signals:
        color = SIGNAL_COLORS.get(sig, '#64748b')
        stats_html += f'''
        <div class="stat-card" style="border-left:3px solid {color}">
            <div class="stat-name">{sig}</div>
            <div class="stat-count" style="color:{color}">{count}</div>
        </div>'''
    
    # Generate tables for each threshold
    tables_html = ''
    for threshold in ['200', '400', '1000']:
        td = thresholds.get(threshold, {})
        stocks = td.get('stocks', [])
        stats = td.get('stats', {})
        
        rows_html = ''
        for s in stocks:
            rank_change = s.get('rank_change', '')
            rc_class = 'rc-new' if 'NEW' in rank_change else ('rc-up' if '↑' in rank_change else 'rc-down')
            
            rows_html += f'''
            <tr data-signals=",{','.join(s.get('signals', []))},">
                <td class="rk">{s.get('rank', '')}</td>
                <td class="rd {rc_class}">{rank_change}</td>
                <td><strong>{s.get('code', '')}</strong></td>
                <td>{s.get('name', '')}</td>
                <td><span class="mkt-tag">{s.get('market', '')}</span></td>
                <td class="ind">{s.get('industry', '')}</td>
                <td class="pr">{s.get('price', '')}</td>
                <td class="cg {updown_class(s.get('change_pct', ''))}">{s.get('change_pct', '')}</td>
                <td class="pt">{s.get('big_holder_pct', '')}</td>
                <td class="cg {updown_class(s.get('wow_pct', ''))}">{s.get('wow_pct', '')}</td>
                <td>{render_streak_badge(s.get('streak', ''))}</td>
                <td class="tags">{render_signal_badges(s.get('signals', []))}</td>
            </tr>'''
        
        tables_html += f'''
        <div class="threshold-panel" id="panel-{threshold}" style="display:none">
            <div class="panel-header">
                <h3>門檻 ≥{threshold}張｜共 {len(stocks)} 檔</h3>
                <div class="mini-stats">
                    <span>📈 上漲: {stats.get('nUp', 0)}</span>
                    <span>📉 下跌: {stats.get('nDown', 0)}</span>
                    <span>➡️ 平盤: {stats.get('nFlat', 0)}</span>
                    <span>🚀 加速: {stats.get('nAccel', 0)}</span>
                    <span>🆕 新進榜: {stats.get('nNewG', 0)}</span>
                </div>
            </div>
            <div class="table-responsive">
                <table class="data-table" id="tbl-{threshold}">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>變化</th>
                            <th>代號</th>
                            <th>名稱</th>
                            <th>市場</th>
                            <th>產業</th>
                            <th>價格</th>
                            <th>漲跌%</th>
                            <th>大戶%</th>
                            <th>週增減</th>
                            <th>連增</th>
                            <th>訊號</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>'''
    
    # Generate signal filter buttons
    filter_buttons = ''
    for sig, count in sorted_signals:
        color = SIGNAL_COLORS.get(sig, '#64748b')
        filter_buttons += f'<button class="filter-btn" data-signal="{sig}" style="--c:{color}" onclick="toggleFilter(this, \'{sig}\')">{sig} ({count})</button>'
    
    html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>籌碼週排行｜大戶動向</title>
<link rel="stylesheet" href="css/style.css">
<style>
/* ===== Weekly Ranking Page Styles ===== */
.wr-header {{
    max-width: 1400px; margin: 0 auto; padding: 20px;
}}
.wr-header h1 {{ font-size: 1.5em; margin-bottom: 5px; }}
.wr-header .subtitle {{ color: var(--text-muted); font-size: 0.9em; }}

/* Signal Stats */
.signal-stats {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 10px; max-width: 1400px; margin: 0 auto; padding: 0 20px 20px;
}}
.stat-card {{
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 8px; padding: 12px; text-align: center;
    transition: transform 0.15s, box-shadow 0.15s;
}}
.stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px var(--shadow); }}
.stat-name {{ font-size: 0.82em; color: var(--text-secondary); margin-bottom: 4px; }}
.stat-count {{ font-size: 1.3em; font-weight: 700; }}

/* Threshold Tabs */
.thresh-tabs {{
    display: flex; gap: 8px; max-width: 1400px; margin: 0 auto; padding: 0 20px 15px;
}}
.thresh-tab {{
    padding: 8px 20px; border: 1px solid var(--border); border-radius: 6px;
    background: var(--card-bg); color: var(--text-muted); cursor: pointer;
    font-size: 0.9em; font-weight: 500; transition: all 0.2s;
}}
.thresh-tab:hover {{ border-color: var(--accent); color: var(--accent); }}
.thresh-tab.active {{ background: var(--accent); color: #fff; border-color: var(--accent); }}

/* Filters */
.filter-bar {{
    max-width: 1400px; margin: 0 auto; padding: 0 20px 15px;
    display: flex; flex-wrap: wrap; gap: 6px;
}}
.filter-btn {{
    padding: 5px 12px; border-radius: 20px; border: 1px solid var(--border);
    background: var(--card-bg); color: var(--text-secondary); font-size: 0.8em;
    cursor: pointer; transition: all 0.2s;
}}
.filter-btn:hover {{ border-color: var(--c); color: var(--c); }}
.filter-btn.active {{ background: var(--c); color: #fff; border-color: var(--c); }}
.filter-clear {{
    padding: 5px 12px; border-radius: 20px; border: 1px solid var(--border);
    background: transparent; color: var(--text-muted); font-size: 0.8em;
    cursor: pointer;
}}
.filter-clear:hover {{ color: var(--text); }}

/* Panel */
.threshold-panel {{ max-width: 1400px; margin: 0 auto; padding: 0 20px 20px; }}
.panel-header {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 12px; flex-wrap: wrap; gap: 8px;
}}
.panel-header h3 {{ font-size: 1.1em; color: var(--text); margin: 0; }}
.mini-stats {{ display: flex; gap: 12px; font-size: 0.8em; color: var(--text-muted); flex-wrap: wrap; }}

/* Table Enhancements */
.rd {{ font-size: 0.82em; font-weight: 600; }}
.rc-new {{ color: var(--accent); }}
.rc-up {{ color: var(--up); }}
.rc-down {{ color: var(--down); }}
.mkt-tag {{
    font-size: 0.7em; padding: 2px 6px; border-radius: 4px;
    background: var(--bg); color: var(--text-muted);
}}
.signal-badge {{
    display: inline-block; padding: 2px 8px; border-radius: 12px;
    font-size: 0.72em; font-weight: 500; margin: 1px;
    white-space: nowrap;
}}
.streak-badge {{
    font-size: 0.8em; color: var(--warning); font-weight: 600;
}}
.tags {{ min-width: 180px; }}

/* Responsive */
@media (max-width: 768px) {{
    .signal-stats {{ grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); }}
    .panel-header {{ flex-direction: column; align-items: flex-start; }}
}}
</style>
</head>
<body>
<nav class="navbar">
    <div class="nav-brand">🔥 跟隨大戶選股站</div>
    <div class="nav-links">
        <a href="index.html">📊 首頁</a>
        <a href="watchlist.html">⭐ 自選</a>
        <a href="etf_00981a.html">📈 00981A</a>
        <a href="weekly_ranking.html" class="active">📅 週排行</a>
    </div>
</nav>

<div class="wr-header">
    <h1>📅 大戶籌碼週排行榜</h1>
    <p class="subtitle">來源: fortune-fred.github.io/plot_stock/weekly_ranking.html｜更新: {fetched}</p>
</div>

<!-- Signal Stats -->
<div class="signal-stats">
    {stats_html}
</div>

<!-- Threshold Tabs -->
<div class="thresh-tabs">
    <button class="thresh-tab active" onclick="showThreshold('200', this)">≥200張 (Top 100)</button>
    <button class="thresh-tab" onclick="showThreshold('400', this)">≥400張 (Top 100)</button>
    <button class="thresh-tab" onclick="showThreshold('1000', this)">≥1000張 (Top 100)</button>
</div>

<!-- Signal Filters -->
<div class="filter-bar">
    <button class="filter-clear" onclick="clearFilters()">🔄 清除篩選</button>
    {filter_buttons}
</div>

<!-- Tables -->
{tables_html}

<footer class="footer">
    <p>📅 更新: {fetched} | 來源: 籌碼監控大戶系統 (fortune-fred.github.io/plot_stock)</p>
    <p>⚠️ 僅供研究參考</p>
</footer>

<script>
// Show active threshold panel
function showThreshold(th, btn) {{
    document.querySelectorAll('.thresh-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.threshold-panel').forEach(p => p.style.display = 'none');
    document.getElementById('panel-' + th).style.display = 'block';
    applyFilters();
}}

// Signal filter state
let activeSignal = '';

function toggleFilter(btn, signal) {{
    const wasActive = btn.classList.contains('active');
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    if (!wasActive) {{
        btn.classList.add('active');
        activeSignal = signal;
    }} else {{
        activeSignal = '';
    }}
    applyFilters();
}}

function clearFilters() {{
    activeSignal = '';
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    applyFilters();
}}

function applyFilters() {{
    const visiblePanel = document.querySelector('.threshold-panel[style*="block"]') || document.getElementById('panel-200');
    const rows = visiblePanel.querySelectorAll('tbody tr');
    rows.forEach(row => {{
        const tags = row.getAttribute('data-signals') || '';
        const show = !activeSignal || tags.includes(',' + activeSignal + ',');
        row.style.display = show ? '' : 'none';
    }});
}}

// Show first panel by default
document.getElementById('panel-200').style.display = 'block';
</script>
<script src="js/app.js"></script>
</body>
</html>'''
    
    return html

def main():
    data = load_data()
    html = generate_html(data)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Generated {OUTPUT_PATH}")
    print(f"  Thresholds: {list(data.get('thresholds', {}).keys())}")
    print(f"  Total signals: {len(data.get('signal_counts', {}))}")
    print(f"  Fetched: {data.get('fetched_at', '')}")

if __name__ == '__main__':
    main()
