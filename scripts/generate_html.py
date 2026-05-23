"""
靜態網站生成器
根據選股結果產生 HTML 頁面
"""

import json
import os

from config import SCREEN_CONFIG, DATA_DIR, DOCS_DIR, WATCHLIST, ETF_00981A_HOLDINGS


class HTMLGenerator:
    def __init__(self):
        self.data = {}
        self.raw_data = {}
        self.load_data()

    def load_data(self):
        screened_path = os.path.join(DATA_DIR, "screened_data.json")
        raw_path = os.path.join(DATA_DIR, "raw_data.json")
        if os.path.exists(screened_path):
            with open(screened_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        if os.path.exists(raw_path):
            with open(raw_path, "r", encoding="utf-8") as f:
                self.raw_data = json.load(f)

    def _head(self, title):
        return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="css/style.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
// ===== Chart.js 白底主題全域預設 =====
Chart.defaults.color = '#475569';
Chart.defaults.borderColor = 'rgba(0,0,0,0.06)';
Chart.defaults.font.family = "'Segoe UI', 'Microsoft JhengHei', system-ui, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(30,41,59,0.95)';
Chart.defaults.plugins.tooltip.titleColor = '#f8fafc';
Chart.defaults.plugins.tooltip.bodyColor = '#e2e8f0';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,0.1)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.displayColors = true;
Chart.defaults.plugins.tooltip.boxPadding = 4;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.boxWidth = 8;
Chart.defaults.plugins.legend.labels.padding = 16;
Chart.defaults.scale.grid.color = 'rgba(0,0,0,0.06)';
Chart.defaults.scale.grid.tickColor = 'rgba(0,0,0,0.06)';
Chart.defaults.scale.ticks.color = '#64748b';
</script>
<script src="js/app.js" defer></script>
<script src="js/extra_features.js" defer></script>
</head>"""

    def _nav(self, active=""):
        items = [("index.html","📊 首頁"),("watchlist.html","⭐ 自選"),("etf_00981a.html","📈 00981A"),("sector.html","🔄 族群輪動")]
        html = '<nav class="navbar"><a href="index.html" class="nav-brand">🔥 跟隨大戶選股站</a><span style="color:#334155;">|</span><div class="nav-links">'
        for href, text in items:
            if active and active in href:
                html += f'<span class="nav-active" style="color:var(--active);font-weight:600;font-size:0.85rem;cursor:default;">{text}</span>'
            else:
                html += f'<a href="{href}">{text}</a>'
        html += '</div>'
        # === 全局搜尋框 ===
        stock_map = {}
        for s in self.data.get("screened", []):
            sid = s.get("stock_id")
            sname = s.get("stock_name")
            if sid:
                stock_map[sid] = sname or ""
        html += f'<div class="nav-search"><input type="text" id="globalSearch" list="stockList" placeholder="🔍 輸入代號或名稱查找個股…" onkeydown="if(event.key===\'Enter\')goStock()" onchange="goStock()"><datalist id="stockList">'
        for sid, sname in stock_map.items():
            html += f'<option value="{sid} {sname}"></option>'
        html += '</datalist><button onclick="goStock()">前往</button></div>'
        html += '<button id="csvExportBtn" style="margin-left:12px;padding:6px 14px;background:#334155;color:#94a3b8;border:none;border-radius:6px;cursor:pointer;font-size:13px;">📥 匯出CSV</button>'
        html += '<script>function goStock(){const v=document.getElementById("globalSearch").value.trim();if(!v)return;const m=v.match(/^\\d+/);const id=m?m[0]:v;location.href="stock_"+id+".html";}</script>'
        html += '</nav>'
        return html

    def _footer(self):
        t = self.data.get("update_time", "未知")
        return f'<footer class="footer"><p>📅 更新: {t} | 來源: FinMind/Yahoo/證交所</p><p>⚠️ 僅供研究參考</p></footer>'

    def generate_index(self):
        screened = self.data.get("screened", [])
        big_holder_rank = self.data.get("big_holder_rank", [])
        foreign_buy = [s for s in screened if s.get("foreign_consecutive_buy")]
        bull_stocks = [s for s in screened if s.get("technical",{}).get("trend")=="多頭排列"]
        top_big = big_holder_rank[:50]

        scatter_data = []
        for s in screened:
            if s.get("big_holder_pct") and s.get("big_holder_change") is not None:
                scatter_data.append({"x":s["big_holder_pct"],"y":s["big_holder_change"],"stock_id":s["stock_id"],"stock_name":s["stock_name"]})

        lines = []
        lines.append(self._head("籌碼監控｜首頁"))
        lines.append('<body>')
        lines.append(self._nav("index"))
        lines.append(f'<div class="container"><div class="header-info"><h1>📊 籌碼監控儀表板</h1><p class="subtitle">共 {len(screened)} 支個股｜產出 {self.data.get("update_time","")}</p></div>')

        # === 市場情緒指標儀表板 ===
        lines.append('<div style="max-width:1400px;margin:10px auto;padding:0 20px;"><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px;margin-bottom:15px;">')
        lines.append('<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:15px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.08);"><div style="color:#475569;font-size:12px;margin-bottom:5px;font-weight:600;">🎯 市場情緒</div><div id="marketSentiment" style="font-size:1.4em;font-weight:bold;color:#d97706;text-shadow:0 1px 2px rgba(0,0,0,0.05);">計算中...</div></div>')
        lines.append('<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:15px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.08);"><div style="color:#475569;font-size:12px;margin-bottom:5px;font-weight:600;">📈 上漲家數</div><div id="advancingCount" style="font-size:1.4em;font-weight:bold;color:#15803d;text-shadow:0 1px 2px rgba(0,0,0,0.05);">--</div></div>')
        lines.append('<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:15px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.08);"><div style="color:#475569;font-size:12px;margin-bottom:5px;font-weight:600;">📉 下跌家數</div><div id="decliningCount" style="font-size:1.4em;font-weight:bold;color:#b91c1c;text-shadow:0 1px 2px rgba(0,0,0,0.05);">--</div></div>')
        lines.append('<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:15px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.08);"><div style="color:#475569;font-size:12px;margin-bottom:5px;font-weight:600;">➡️ 平盤家數</div><div id="flatCount" style="font-size:1.4em;font-weight:bold;color:#475569;text-shadow:0 1px 2px rgba(0,0,0,0.05);">--</div></div>')
        lines.append('</div></div>')

        # === 族群輪動儀表板 ===
        lines.append('<div style="max-width:1400px;margin:20px auto;padding:0 20px;"><div style="background:rgba(30,41,59,0.6);border:1px solid #334155;border-radius:12px;padding:20px;margin-bottom:20px;">')
        lines.append('<h2 style="color:#38bdf8;font-size:1.3em;margin:0 0 15px 0;border-bottom:1px solid #334155;padding-bottom:10px;">🔄 族群輪動儀表板 <span style="font-size:12px;color:#94a3b8;font-weight:normal;">(按住 Shift + 點擊股票查看詳情)</span></h2>')
        lines.append('<div id="sectorRotationPanel" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;"><div style="color:#64748b;text-align:center;padding:20px;">載入中...</div></div>')
        lines.append('</div></div>')

        # 散點圖
        lines.append('<div class="card"><h2>🔥 大戶持股%(含外資) vs 週增減</h2><div class="controls"><label>顯示</label><button class="fbtn active" id="sc-all" onclick="setScatter(\'all\',this)">全部</button><button class="fbtn" id="sc-up" onclick="setScatter(\'up\',this)">📈 增加</button><button class="fbtn" id="sc-down" onclick="setScatter(\'down\',this)">📉 減少</button></div><p class="chart-desc">X:大戶持股% Y:週增減% 點擊進入個股</p><div class="chart-container"><canvas id="scatterChart"></canvas></div></div>')

        lines.append('<div class="card"><h2>🔥 雙重認證榜單 (00981A + 大戶增倉 + 法人買超)</h2><div class="table-responsive"><table class="data-table"><thead><tr><th>代號</th><th>名稱</th><th>收盤價</th><th>漲跌%</th><th>外資淨買</th><th>投信淨買</th><th>大戶%</th><th>週增減</th><th>趨勢</th><th>評分</th></tr></thead><tbody>')
        dual_certified = self.data.get("dual_certified", [])
        for s in dual_certified[:30]:
            tech = s.get("technical",{}) or {}
            trend = tech.get("trend","")
            tc = "bull" if "多頭" in trend else "bear" if "空頭" in trend else ""
            close = s.get("close") if s.get("close") is not None else 0.0
            change_pct = s.get("change_pct") if s.get("change_pct") is not None else 0.0
            foreign_net = s.get("foreign_net") if s.get("foreign_net") is not None else 0
            trust_net = s.get("trust_net") if s.get("trust_net") is not None else 0
            big_holder_pct = s.get("big_holder_pct") if s.get("big_holder_pct") is not None else 0.0
            big_holder_change = s.get("big_holder_change") if s.get("big_holder_change") is not None else 0.0
            score = s.get("score") if s.get("score") is not None else 0
            lines.append(f'<tr onclick="location.href=\'stock_{s.get("stock_id","-")}.html\'" class="clickable"><td><strong>{s.get("stock_id","-")}</strong></td><td>{s.get("stock_name","-")}</td><td>{close:.2f}</td><td class="{"up" if change_pct>0 else "down"}">{change_pct:+.2f}%</td><td class="{"buy" if foreign_net>0 else "sell"}">{foreign_net:,}</td><td class="{"buy" if trust_net>0 else "sell"}">{trust_net:,}</td><td class="highlight">{big_holder_pct:.2f}%</td><td class="{"up" if big_holder_change>0 else "down"}">{big_holder_change:+.2f}%</td><td class="{tc}">{trend}</td><td><span class="score">{score}</span></td></tr>')
        lines.append('</tbody></table></div></div>')

        # 外資買超
        lines.append(f'<div class="card"><h2>🌍 外資買超榜單</h2><div class="table-responsive"><table class="data-table"><thead><tr><th>代號</th><th>名稱</th><th>收盤價</th><th>漲跌%</th><th>外資淨買</th><th>大戶%</th><th>趨勢</th><th>評分</th></tr></thead><tbody>')
        for s in foreign_buy[:30]:
            tech = s.get("technical",{}) or {}
            trend = tech.get("trend","")
            tc = "bull" if "多頭" in trend else "bear" if "空頭" in trend else ""
            close = s.get("close") if s.get("close") is not None else 0.0
            change_pct = s.get("change_pct") if s.get("change_pct") is not None else 0.0
            foreign_net = s.get("foreign_net") if s.get("foreign_net") is not None else 0
            big_holder_pct = s.get("big_holder_pct") if s.get("big_holder_pct") is not None else 0.0
            score = s.get("score") if s.get("score") is not None else 0
            lines.append(f'<tr onclick="location.href=\'stock_{s.get("stock_id","-")}.html\'" class="clickable"><td><strong>{s.get("stock_id","-")}</strong></td><td>{s.get("stock_name","-")}</td><td>{close:.2f}</td><td class="{"up" if change_pct>0 else "down"}">{change_pct:+.2f}%</td><td class="buy">{foreign_net:,}</td><td>{big_holder_pct:.2f}%</td><td class="{tc}">{trend}</td><td><span class="score">{score}</span></td></tr>')
        lines.append('</tbody></table></div></div>')

        # 外資買超時間圖表 — Top 5 近 20 日淨買超趨勢
        if foreign_buy:
            top5_foreign = foreign_buy[:5]
            foreign_datasets = []
            shared_dates = None
            for s in top5_foreign:
                sid = s.get("stock_id")
                raw = self.raw_data.get(sid, {})
                fd = raw.get("foreign", [])
                if not fd:
                    continue
                last20 = fd[-20:]
                dates = [f["date"][:10] for f in last20]
                nets = []
                for f in last20:
                    buy = float(f.get("buy", 0)) if f.get("buy") else 0
                    sell = float(f.get("sell", 0)) if f.get("sell") else 0
                    nets.append(buy - sell)
                if shared_dates is None:
                    shared_dates = dates
                foreign_datasets.append({
                    "label": f"{sid} {s.get('stock_name', '')}",
                    "data": nets,
                    "borderColor": None,  # assigned by index later
                    "backgroundColor": "transparent",
                    "fill": False,
                    "tension": 0.3,
                    "pointRadius": 3,
                    "borderWidth": 2
                })
            if shared_dates and foreign_datasets:
                colors = ["#1d4ed8", "#f97316", "#10b981", "#8b5cf6", "#ef4444"]
                for i, ds in enumerate(foreign_datasets):
                    ds["borderColor"] = colors[i % len(colors)]
                fjson = json.dumps(foreign_datasets, ensure_ascii=False)
                lines.append('<div class="card"><h2>🌍 外資買超 — 時間趨勢圖 (Top 5)</h2><p class="chart-desc">近 20 個交易日外資淨買超張數趨勢</p><div class="chart-container"><canvas id="foreignTrendChart"></canvas></div></div>')
                lines.append(f'<script>new Chart(document.getElementById("foreignTrendChart").getContext("2d"),{{type:"line",data:{{labels:{json.dumps(shared_dates)},datasets:{fjson}}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:true,labels:{{usePointStyle:true,boxWidth:8}}}}}},scales:{{x:{{grid:{{color:"rgba(0,0,0,0.05)"}},ticks:{{color:"#64748b",maxRotation:45}}}},y:{{grid:{{color:"rgba(0,0,0,0.05)"}},ticks:{{color:"#64748b"}},title:{{display:true,text:"淨買超 (張)",color:"#64748b"}}}}}}}}}});</script>')

        # 多頭排列
        lines.append('<div class="card"><h2>📈 多頭排列清單</h2><div class="table-responsive"><table class="data-table"><thead><tr><th>代號</th><th>名稱</th><th>收盤價</th><th>20MA</th><th>60MA</th><th>RSI</th><th>大戶%</th><th>外資連買</th></tr></thead><tbody>')
        for s in bull_stocks[:30]:
            tech = s.get("technical",{}) or {}
            close = s.get("close") if s.get("close") is not None else 0.0
            big_holder_pct = s.get("big_holder_pct") if s.get("big_holder_pct") is not None else 0.0
            foreign_consecutive = bool(s.get("foreign_consecutive_buy"))
            lines.append(f'<tr onclick="location.href=\'stock_{s.get("stock_id","-")}.html\'" class="clickable"><td><strong>{s.get("stock_id","-")}</strong></td><td>{s.get("stock_name","-")}</td><td>{close:.2f}</td><td>{tech.get("ma20","-")}</td><td>{tech.get("ma60","-")}</td><td>{tech.get("rsi","-")}</td><td>{big_holder_pct:.2f}%</td><td>{"✅" if foreign_consecutive else "❌"}</td></tr>')
        lines.append('</tbody></table></div></div>')

        # 大戶門檻統計
        watchlist_data = self.data.get("watchlist", [])
        lines.append('<div class="card"><h2>🏛️ 大戶門檻統計 (200檔監控)</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-top:10px;">')
        threshold_stats = {"100": {"count": 0, "min": 999, "max": 0, "sum": 0},
                           "200": {"count": 0, "min": 999, "max": 0, "sum": 0},
                           "400": {"count": 0, "min": 999, "max": 0, "sum": 0},
                           "1000": {"count": 0, "min": 999, "max": 0, "sum": 0}}
        for s in watchlist_data:
            th = s.get("big_holder_threshold", "")
            bp = s.get("big_holder_pct", 0) or 0
            if th and th in threshold_stats and bp > 0:
                threshold_stats[th]["count"] += 1
                threshold_stats[th]["min"] = min(threshold_stats[th]["min"], bp)
                threshold_stats[th]["max"] = max(threshold_stats[th]["max"], bp)
                threshold_stats[th]["sum"] += bp
        for th, label in [("100", "💎 ≥100張 (高價股)"), ("200", "🔸 ≥200張"), ("400", "🔹 ≥400張"), ("1000", "📌 ≥1000張 (低價股)")]:
            stats = threshold_stats[th]
            if stats["count"] > 0:
                avg = stats["sum"] / stats["count"]
                lines.append(f'<div style="background:rgba(255,215,0,0.05);border:1px solid rgba(255,215,0,0.2);border-radius:8px;padding:12px;"><h4 style="color:#ffd700;margin:0 0 8px 0;">{label}</h4><p style="margin:4px 0;color:#ccc;font-size:0.9em;">自選覆蓋: {stats["count"]} 檔</p><p style="margin:4px 0;color:#ccc;font-size:0.9em;">大戶%: {stats["min"]:.1f}% ~ {stats["max"]:.1f}% (avg {avg:.1f}%)</p></div>')
        lines.append('</div></div>')

        # 大戶排名 (全部股票，JS 依門檻篩選)
        all_big = big_holder_rank[:]
        seen_ids = {s["stock_id"] for s in all_big}
        for s in screened:
            if s["stock_id"] not in seen_ids:
                all_big.append(s)
        lines.append('<div class="card"><h2>👑 大戶持股排名（含外資）</h2><div class="controls"><label>顯示前 <input type="number" id="rankLimit" value="50" min="10" max="200" onchange="updateRank()"> 名</label><label>最小持股% <input type="number" id="minPct" value="0" min="0" max="100" step="0.1" onchange="updateRank()"></label><span class="ctrl-sep"></span><label>門檻</label><button class="fbtn active" id="th-all" onclick="setThreshold(\'all\',this)">全部</button><button class="fbtn" id="th-200" onclick="setThreshold(\'200\',this)">≥200張</button><button class="fbtn" id="th-400" onclick="setThreshold(\'400\',this)">≥400張</button><button class="fbtn" id="th-1000" onclick="setThreshold(\'1000\',this)">≥1000張</button></div><div class="table-responsive"><table class="data-table" id="bigHolderTable"><thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>大戶%</th><th>週增減%</th><th>收盤價</th><th>漲跌%</th><th>門檻</th></tr></thead><tbody>')
        for i, s in enumerate(all_big, 1):
            big_holder_pct = s.get("big_holder_pct") if s.get("big_holder_pct") is not None else 0.0
            big_holder_change = s.get("big_holder_change") if s.get("big_holder_change") is not None else 0.0
            close = s.get("close") if s.get("close") is not None else 0.0
            change_pct = s.get("change_pct") if s.get("change_pct") is not None else 0.0
            th = s.get("big_holder_threshold", "") or "—"
            cc = "up" if big_holder_change>0 else "down" if big_holder_change<0 else ""
            sid = s.get("stock_id","-")
            lines.append(f'<tr data-pct="{big_holder_pct}" data-threshold="{th}" onclick="location.href=\'stock_{sid}.html\'" class="clickable"><td>{i}</td><td><strong>{sid}</strong></td><td>{s.get("stock_name","-")}</td><td class="highlight">{big_holder_pct:.2f}%</td><td class="{cc}">{big_holder_change:+.2f}%</td><td>{close:.2f}</td><td class="{"up" if change_pct>0 else "down"}">{change_pct:+.2f}%</td><td>≥{th}張</td></tr>')
        lines.append('</tbody></table></div></div>')

        # === Norway 數據圖表 ===
        lines.append('<div class="card"><h2>🇳🇴 Norway.twsthr.info — 台灣50 大戶持有率排名</h2><div class="chart-container"><canvas id="norwayBarChart"></canvas></div></div>')
        
        # 載入 Norway 數據
        norway_data = []
        try:
            with open("data/norway/taiwan50_weekly.json", "r", encoding="utf-8") as f:
                norway_data = json.load(f)
        except:
            pass
        
        if norway_data:
            # 持有率 bar chart 數據
            norway_sorted = sorted(norway_data, key=lambda x: x.get("last_week_hold_pct", 0), reverse=True)
            norway_labels = [f"{r['stock_code']}\n{r['stock_name']}" for r in norway_sorted[:20]]
            norway_pcts = [r.get("last_week_hold_pct", 0) for r in norway_sorted[:20]]
            norway_changes = [r.get("latest_change", 0) for r in norway_sorted[:20]]
            
            lines.append(f'<script>')
            lines.append(f'new Chart(document.getElementById("norwayBarChart").getContext("2d"),{{')
            lines.append(f'type:"bar",')
            lines.append(f'data:{{')
            lines.append(f'labels:{json.dumps(norway_labels, ensure_ascii=False)},')
            lines.append(f'datasets:[')
            lines.append(f'{{label:"大戶持有率%",data:{json.dumps(norway_pcts)},backgroundColor:"rgba(255,193,7,0.7)",borderColor:"#ffc107",borderWidth:1}},')
            lines.append(f'{{label:"最新週增減%",data:{json.dumps(norway_changes)},backgroundColor:{json.dumps(norway_changes)}.map(v=>v>0?"rgba(46,204,113,0.7)":"rgba(231,76,60,0.7)"),borderColor:{json.dumps(norway_changes)}.map(v=>v>0?"#27ae60":"#c0392b"),borderWidth:1}}')
            lines.append(f']')
            lines.append(f'}},')
            lines.append(f'options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:true}}}}}}')
            lines.append(f'}});')
            lines.append(f'</script>')
        
        # 交叉比對摘要卡片
        cross_data = {}
        try:
            with open("data/cross_analysis/cross_analysis.json", "r", encoding="utf-8") as f:
                cross_data = json.load(f)
        except:
            pass
        
        if cross_data:
            s = cross_data.get("summary", {})
            lines.append('<div class="card"><h2>🔗 數據源交叉比對 (fortune-fred vs Norway)</h2>')
            lines.append('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:15px;margin-top:10px;">')
            lines.append(f'<div style="background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.3);border-radius:8px;padding:12px;text-align:center;"><p style="margin:0;font-size:2rem;font-weight:700;color:#3b82f6;">{s.get("common_stocks",0)}</p><p style="margin:4px 0;color:#94a3b8;font-size:0.85rem;">共同覆蓋股票</p></div>')
            lines.append(f'<div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);border-radius:8px;padding:12px;text-align:center;"><p style="margin:0;font-size:2rem;font-weight:700;color:#10b981;">{s.get("direction_match_rate",0)}%</p><p style="margin:4px 0;color:#94a3b8;font-size:0.85rem;">方向一致率</p></div>')
            lines.append(f'<div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);border-radius:8px;padding:12px;text-align:center;"><p style="margin:0;font-size:2rem;font-weight:700;color:#f59e0b;">{s.get("avg_abs_diff",0)}%</p><p style="margin:4px 0;color:#94a3b8;font-size:0.85rem;">平均絕對差異</p></div>')
            lines.append(f'<div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:8px;padding:12px;text-align:center;"><p style="margin:0;font-size:2rem;font-weight:700;color:#ef4444;">{s.get("max_abs_diff",0)}%</p><p style="margin:4px 0;color:#94a3b8;font-size:0.85rem;">最大差異</p></div>')
            lines.append('</div>')
            lines.append('<p style="text-align:center;margin-top:15px;"><a href="cross_analysis.html" style="display:inline-block;background:#3b82f6;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:600;">📊 查看完整交叉比對報告</a></p>')
            lines.append('</div>')
        
        lines.append('</div>')
        lines.append(self._footer())

        # === 策略回測區（彈出模態框）===
        lines.append('<div id="backtestModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:9998;align-items:center;justify-content:center;padding:20px;">')
        lines.append('<div style="background:#0f172a;border:1px solid #334155;border-radius:12px;max-width:700px;width:100%;max-height:90vh;overflow-y:auto;padding:25px;">')
        lines.append('<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;"><h2 style="color:#38bdf8;margin:0;">🧪 策略回測</h2><button onclick="document.getElementById(\'backtestModal\').style.display=\'none\'" style="background:none;border:none;color:#94a3b8;font-size:20px;cursor:pointer;">✕</button></div>')
        lines.append('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px;">')
        lines.append('<div><label style="color:#94a3b8;font-size:12px;">大戶持股% ≥</label><input type="number" id="ruleMinBh" value="0" min="0" max="100" step="0.1" style="width:100%;padding:8px;margin-top:4px;background:#1e293b;border:1px solid #334155;border-radius:6px;color:#e2e8f0;"></div>')
        lines.append('<div><label style="color:#94a3b8;font-size:12px;">最小漲跌% ≥</label><input type="number" id="ruleMinChange" value="-10" step="0.1" style="width:100%;padding:8px;margin-top:4px;background:#1e293b;border:1px solid #334155;border-radius:6px;color:#e2e8f0;"></div>')
        lines.append('<div><label style="color:#94a3b8;font-size:12px;">最大漲跌% ≤</label><input type="number" id="ruleMaxChange" value="10" step="0.1" style="width:100%;padding:8px;margin-top:4px;background:#1e293b;border:1px solid #334155;border-radius:6px;color:#e2e8f0;"></div>')
        lines.append('<div><label style="color:#94a3b8;font-size:12px;display:flex;align-items:center;gap:5px;"><input type="checkbox" id="ruleBullOnly" style="accent-color:#3b82f6;"> 僅多頭排列</label></div>')
        lines.append('</div>')
        lines.append('<button id="runBacktestBtn" style="width:100%;padding:12px;background:#3b82f6;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">▶️ 執行回測</button>')
        lines.append('<div id="backtestResult" style="margin-top:20px;"></div>')
        lines.append('<p style="color:#64748b;font-size:12px;margin-top:15px;text-align:center;">⚠️ 回測以「當日漲跌%」模擬單日持有報酬，僅供選股條件驗證參考</p>')
        lines.append('</div></div>')

        # 浮動回測按鈕
        lines.append('<button onclick="document.getElementById(\'backtestModal\').style.display=\'flex\'" style="position:fixed;bottom:90px;right:30px;width:50px;height:50px;background:#3b82f6;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:18px;z-index:1000;box-shadow:0 4px 12px rgba(0,0,0,0.3);border:none;">🧪</button>')

        # JS
        sd = json.dumps(scatter_data, ensure_ascii=False)
        lines.append(f'<script>')
        lines.append(f'const scatterData = {sd};')
        lines.append('const ctx = document.getElementById("scatterChart").getContext("2d");')
        lines.append('let scatterChart;function renderScatter(filter){const up=scatterData.filter(d=>d.y>0);const down=scatterData.filter(d=>d.y<0);const flat=scatterData.filter(d=>d.y===0);const ds=[];if(filter==="all"||filter==="up")ds.push({label:"📈 增加",data:up,backgroundColor:"rgba(46,204,113,0.6)",borderColor:"#27ae60",borderWidth:1,pointRadius:6,pointHoverRadius:10});if(filter==="all"||filter==="down")ds.push({label:"📉 減少",data:down,backgroundColor:"rgba(231,76,60,0.6)",borderColor:"#c0392b",borderWidth:1,pointRadius:6,pointHoverRadius:10});if(filter==="all"||filter==="flat")ds.push({label:"➡️ 持平",data:flat,backgroundColor:"rgba(148,163,184,0.6)",borderColor:"#64748b",borderWidth:1,pointRadius:6,pointHoverRadius:10});if(scatterChart)scatterChart.destroy();scatterChart=new Chart(ctx,{type:"scatter",data:{datasets:ds},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true},tooltip:{backgroundColor:"rgba(15,23,42,0.95)",titleColor:"#e2e8f0",bodyColor:"#e2e8f0",borderColor:"#334155",borderWidth:1,cornerRadius:8,padding:10,displayColors:true,callbacks:{label:function(context){const d=context.raw;return `${d.stock_name}(${d.stock_id}) 大戶:${d.x}% 週增減:${d.y>=0?"+":""}${d.y}%`;},title:function(){return"";}}}},scales:{x:{title:{display:true,text:"大戶持股 %",color:"#64748b"},ticks:{color:"#64748b"},grid:{color:"rgba(0,0,0,0.05)"}},y:{title:{display:true,text:"本週增減 %",color:"#64748b"},ticks:{color:"#64748b"},grid:{color:"rgba(0,0,0,0.05)"}}},onClick:(e,elements)=>{if(elements.length>0){const el=elements[0];const d=scatterChart.data.datasets[el.datasetIndex].data[el.index];window.location.href="stock_"+d.stock_id+".html";}}}});}function setScatter(v,btn){["sc-all","sc-up","sc-down"].forEach(id=>document.getElementById(id).classList.remove("active"));btn.classList.add("active");renderScatter(v);}renderScatter("all");')
        lines.append('function updateRank(){const limit=parseInt(document.getElementById("rankLimit").value)||200;const minPct=parseFloat(document.getElementById("minPct").value)||0;const th=document.getElementById("th-all").classList.contains("active")?"all":document.getElementById("th-200").classList.contains("active")?"200":document.getElementById("th-400").classList.contains("active")?"400":document.getElementById("th-1000").classList.contains("active")?"1000":"all";const rows=document.querySelectorAll("#bigHolderTable tbody tr");let shown=0;rows.forEach((row)=>{const pct=parseFloat(row.dataset.pct);const rowTh=row.dataset.threshold||"";const thOk=th==="all"||rowTh===th;const show=shown<limit&&pct>=minPct&&thOk;if(show)shown++;row.style.display=show?"":"none";});}function setThreshold(v,btn){["th-all","th-200","th-400","th-1000"].forEach(id=>document.getElementById(id).classList.remove("active"));btn.classList.add("active");updateRank();}')
        lines.append('</script>')
        lines.append('</body></html>')

        filepath = os.path.join(DOCS_DIR, "index.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"[OK] 首頁: {filepath}")
        return filepath

    def _generate_table_page(self, title, subtitle, page_key, stock_list):
        """通用表格頁面生成"""
        screened = self.data.get("screened", [])
        page_data = [s for s in screened if s["stock_id"] in stock_list]

        lines = []
        lines.append(self._head(title))
        lines.append('<body>')
        lines.append(self._nav(page_key))
        lines.append(f'<div class="container"><div class="header-info"><h1>{title.split("｜")[0]}</h1><p class="subtitle">{subtitle} 共 {len(page_data)} 檔</p></div>')
        lines.append('<div class="card"><div class="table-responsive"><table class="data-table"><thead><tr><th>代號</th><th>名稱</th><th>收盤價</th><th>漲跌%</th><th>開盤價</th><th>外資買超</th><th>外資淨買</th><th>大戶%</th><th>門檻</th><th>週增減</th><th>券資比</th><th>20MA</th><th>60MA</th><th>RSI</th><th>趨勢</th><th>評分</th></tr></thead><tbody>')

        for s in page_data:
            # === None 安全補丁 (2026-05-14) ===
            # data_fetcher 抓不到資料時，防止 f-string .2f 炸掉
            sid = s.get("stock_id") or "-"
            sname = s.get("stock_name") or "-"
            close = s.get("close") if s.get("close") is not None else 0.0
            change_pct = s.get("change_pct") if s.get("change_pct") is not None else 0.0
            foreign_consecutive = bool(s.get("foreign_consecutive_buy"))
            foreign_net = s.get("foreign_net") if s.get("foreign_net") is not None else 0
            big_holder_pct = s.get("big_holder_pct") if s.get("big_holder_pct") is not None else 0.0
            big_holder_threshold = s.get("big_holder_threshold", "") or "—"
            big_holder_change = s.get("big_holder_change") if s.get("big_holder_change") is not None else 0.0
            score = s.get("score") if s.get("score") is not None else 0
            tech = s.get("technical", {}) or {}
            margin = s.get("margin", {}) or {}
            trend = tech.get("trend", "")
            tc = "bull" if "多頭" in trend else "bear" if "空頭" in trend else "neutral"
            open_val = s.get("open") if s.get("open") is not None else 0.0
            lines.append(f'<tr onclick="location.href=\'stock_{sid}.html\'" class="clickable"><td><strong>{sid}</strong></td><td>{sname}</td><td>{close:.2f}</td><td class="{"up" if change_pct>0 else "down"}">{change_pct:+.2f}%</td><td>{open_val:.2f}</td><td>{"✅" if foreign_consecutive else "❌"}</td><td class="{"buy" if foreign_net>0 else "sell"}">{foreign_net:,}</td><td class="highlight">{big_holder_pct:.2f}%</td><td>≥{big_holder_threshold}張</td><td class="{"up" if big_holder_change>0 else "down"}">{big_holder_change:+.2f}%</td><td>{margin.get("ratio","-") if margin else "-"}</td><td>{tech.get("ma20","-")}</td><td>{tech.get("ma60","-")}</td><td>{tech.get("rsi","-")}</td><td class="{tc}">{trend}</td><td><span class="score">{score}</span></td></tr>')
            # === 補丁結束 ===

        lines.append('</tbody></table></div></div></div>')
        lines.append(self._footer())
        lines.append('</body></html>')

        filepath = os.path.join(DOCS_DIR, f"{page_key}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("".join(lines))
        print(f"[OK] {page_key}: {filepath}")
        return filepath

    def generate_watchlist(self):
        return self._generate_table_page("自選清單｜智董籌碼選股站", "⭐ 自選追蹤", "watchlist", WATCHLIST)

    def generate_etf_00981a(self):
        return self._generate_table_page("00981A 持股明細｜智董籌碼選股站", "📈 00981A 成分股", "etf_00981a", ETF_00981A_HOLDINGS)

    def generate_stock_detail(self, stock_id):
        if stock_id not in self.raw_data:
            return None
        data = self.raw_data[stock_id]
        info = data.get("info", {})
        price_data = data.get("price", [])
        foreign = data.get("foreign", [])

        screened_item = None
        for s in self.data.get("screened", []):
            if s["stock_id"] == stock_id:
                screened_item = s
                break

        tech = screened_item.get("technical", {}) if screened_item else {}
        margin = screened_item.get("margin", {}) if screened_item else {}

        lines = []
        lines.append(self._head(f"{stock_id} {info.get('stock_name','')}｜個股看板"))
        lines.append('<body>')
        lines.append(self._nav(""))
        lines.append(f'<div class="container"><div class="stock-header"><h1>{stock_id} {info.get("stock_name","")}</h1><div class="stock-price"><span class="price">{info.get("close",0):.2f}</span><span class="change {"up" if info.get("change_pct",0)>0 else "down"}">{info.get("change_pct",0):+.2f}%</span></div></div>')
        lines.append('<div class="metrics-grid">')

        # === 變數提取（供 helper function 與模板使用） ===
        foreign_consecutive = screened_item.get("foreign_consecutive_buy") if screened_item else False
        foreign_net = screened_item.get("foreign_net") if screened_item and screened_item.get("foreign_net") is not None else 0
        big_holder_pct = screened_item.get("big_holder_pct") if screened_item and screened_item.get("big_holder_pct") is not None else None
        big_holder_change = screened_item.get("big_holder_change") if screened_item and screened_item.get("big_holder_change") is not None else None
        bh_pct_str = f"{big_holder_pct:.2f}" if big_holder_pct is not None else "-"
        bh_chg_str = f"{big_holder_change:+.2f}" if big_holder_change is not None else "-"
        open_val = info.get("open", 0) if info else 0
        change_val = info.get("change", 0) if info else 0
        change_color = "#16a34a" if change_val >= 0 else "#dc2626"
        change_sign = "+" if change_val >= 0 else ""
        bias20 = tech.get("bias20", "-")
        bias60 = tech.get("bias60", "-")
        dual_bear = tech.get("dual_bear", False)

        def _fmt_bias(val):
            if isinstance(val, (int, float)):
                return f"{val:+.2f}%"
            return str(val) + ("%" if val != "-" else "")

        def _bias_color(val):
            if isinstance(val, (int, float)):
                return "#16a34a" if val >= 0 else "#dc2626"
            return "#64748b"

        bias20_str = _fmt_bias(bias20)
        bias60_str = _fmt_bias(bias60)
        bias20_color = _bias_color(bias20)
        bias60_color = _bias_color(bias60)
        dual_bear_badge = f'<span style="background:#dc2626;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem;margin-left:8px;">⚠️ 双破线</span>' if dual_bear else ''
        shareholder_list = data.get("shareholder", [])
        conc = shareholder_list[0].get("concentration", 0) if shareholder_list else 0
        total_count = shareholder_list[0].get("total_count", 0) if shareholder_list else 0
        big_holder_count = shareholder_list[0].get("big_holder_count", 0) if shareholder_list else 0
        conc_color = "#16a34a" if conc >= 50 else "#f97316" if conc >= 30 else "#dc2626"
        # === 變數提取結束 ===

        # === 訊號說明輔助函數 ===
        def _tech_signal(tech):
            trend = tech.get("trend", "-")
            rsi = tech.get("rsi", None)
            if "多頭" in trend:
                return "📈 偏多 — 均線多頭排列"
            elif "空頭" in trend:
                return "📉 偏空 — 均線空頭排列"
            elif rsi is not None and isinstance(rsi, (int, float)):
                if rsi > 70:
                    return "⚠️ 超買 — RSI 偏高"
                elif rsi < 30:
                    return "💡 超賣 — RSI 偏低"
            return "➡️ 盤整 — 趨勢不明"

        def _foreign_signal(consecutive, net):
            if consecutive and net > 0:
                return "📈 外資做多 — 連續買超"
            elif net > 0:
                return "📈 外資買超 — 單日淨買"
            elif net < 0:
                return "📉 外資賣超 — 淨賣出"
            return "➡️ 外資觀望 — 無明顯動向"

        def _big_holder_signal(pct, change):
            if pct is None:
                return "❓ 無大戶數據"
            if change is None:
                return f"{'🔒' if pct >= 50 else '🔸' if pct >= 30 else '🔹'} 大戶持股 {pct:.1f}%"
            if change > 1.0:
                return "🚀 大戶積極進場 — 週增 >1%"
            elif change > 0:
                return "📈 大戶緩步增持 — 週增 <1%"
            elif change < -1.0:
                return "⚠️ 大戶急於出貨 — 週減 >1%"
            elif change < 0:
                return "📉 大戶小幅減持 — 週減 <1%"
            return "➡️ 大戶籌碼持平"

        def _margin_signal(margin):
            if not margin:
                return "❓ 無融資數據"
            ratio = margin.get("ratio", 0)
            if isinstance(ratio, (int, float)):
                if ratio > 0.5:
                    return "⚠️ 融券高比例 — 注意回補風險"
                elif ratio > 0.3:
                    return "🔸 融券比例偏高"
                elif ratio > 0.1:
                    return "➡️ 融券比例正常"
            return "✅ 融券比例低 — 安全"

        def _open_signal(change_val):
            if change_val > 0:
                return "📈 開高 — 盤中走強"
            elif change_val < 0:
                return "📉 開低 — 盤中走弱"
            return "➡️ 平開 —  neutral"

        def _bias_signal(bias20, bias60, dual_bear):
            if dual_bear:
                return "⚠️ 双破線 — 乖離過大+趨勢轉弱"
            b20 = bias20 if isinstance(bias20, (int, float)) else 0
            b60 = bias60 if isinstance(bias60, (int, float)) else 0
            if b20 > 10 or b60 > 15:
                return "⚠️ 乖離過大 — 可能回檔"
            elif b20 < -10 or b60 < -15:
                return "💡 乖離過深 — 可能反彈"
            return "✅ 乖離正常"

        def _conc_signal(conc):
            if conc >= 60:
                return "🔒 高度集中 — 主力控盤"
            elif conc >= 40:
                return "🔸 相對集中 — 籌碼穩定"
            elif conc >= 20:
                return "➡️ 中度分散"
            return "🔹 籌碼分散 — 無主力跡象"

        tech_signal = _tech_signal(tech)
        foreign_signal = _foreign_signal(foreign_consecutive, foreign_net)
        bh_signal = _big_holder_signal(big_holder_pct, big_holder_change)
        margin_signal = _margin_signal(margin)
        open_signal = _open_signal(change_val)
        bias_signal = _bias_signal(bias20, bias60, dual_bear)
        conc_signal = _conc_signal(conc) if shareholder_list else ""
        # === 訊號說明輔助函數結束 ===

        lines.append(f'<div class="metric-card"><h3>📊 技術面</h3><p>20MA: {tech.get("ma20","-")}</p><p>60MA: {tech.get("ma60","-")}</p><p>RSI: {tech.get("rsi","-")}</p><p class="trend">趨勢: {tech.get("trend","-")}</p><p style="margin-top:8px;font-size:0.85rem;color:#64748b;background:rgba(241,245,249,0.5);padding:4px 8px;border-radius:4px;">{tech_signal}</p></div>')
        lines.append(f'<div class="metric-card"><h3>🌍 外資動向</h3><p>今日買超: {"✅" if foreign_consecutive else "❌"}</p><p>淨買超: {foreign_net:,}</p><p style="margin-top:8px;font-size:0.85rem;color:#64748b;background:rgba(241,245,249,0.5);padding:4px 8px;border-radius:4px;">{foreign_signal}</p></div>')
        lines.append(f'<div class="metric-card"><h3>👑 籌碼面</h3><p>大戶持股%(含外資): {bh_pct_str}%</p><p>週增減: {bh_chg_str}%</p><p style="margin-top:8px;font-size:0.85rem;color:#64748b;background:rgba(241,245,249,0.5);padding:4px 8px;border-radius:4px;">{bh_signal}</p></div>')
        lines.append(f'<div class="metric-card"><h3>💰 融資融券</h3><p>券資比: {margin.get("ratio","-") if margin else "-"}</p><p>融資餘額: {margin.get("margin_balance","-") if margin else "-"}</p><p style="margin-top:8px;font-size:0.85rem;color:#64748b;background:rgba(241,245,249,0.5);padding:4px 8px;border-radius:4px;">{margin_signal}</p></div>')
        lines.append(f'<div class="metric-card"><h3>📊 開盤價</h3><p>{open_val:.2f}</p><p style="color:{change_color};">{change_sign}{change_val:.2f}</p><p style="margin-top:8px;font-size:0.85rem;color:#64748b;background:rgba(241,245,249,0.5);padding:4px 8px;border-radius:4px;">{open_signal}</p></div>')
        lines.append(f'<div class="metric-card"><h3>📐 乖離率{dual_bear_badge}</h3><p>20MA乖離: <span style="color:{bias20_color};font-weight:600;">{bias20_str}</span></p><p>60MA乖離: <span style="color:{bias60_color};font-weight:600;">{bias60_str}</span></p><p style="margin-top:8px;font-size:0.85rem;color:#64748b;background:rgba(241,245,249,0.5);padding:4px 8px;border-radius:4px;">{bias_signal}</p></div>')
        if shareholder_list:
            lines.append(f'<div class="metric-card"><h3>👥 集保集中度</h3><p><span style="color:{conc_color};font-weight:600;font-size:1.3rem;">{conc:.2f}%</span></p><p>大戶人數: {big_holder_count:,} / 總人數: {total_count:,}</p><p style="margin-top:8px;font-size:0.85rem;color:#64748b;background:rgba(241,245,249,0.5);padding:4px 8px;border-radius:4px;">{conc_signal}</p></div>')
        lines.append('</div>')
        lines.append('<div class="card"><h2>📈 股價走勢 + 均線 + 成交量</h2><div class="chart-container"><canvas id="priceChart"></canvas></div></div>')
        lines.append('<div class="card"><h2>📊 MACD 指標 (12,26,9)</h2>')
        lines.append('<div id="macd-values" style="display:flex;gap:24px;margin:8px 0 16px;font-size:0.85rem;color:var(--text);"></div>')
        lines.append('<div class="chart-container"><canvas id="macdChart"></canvas></div></div>')
        lines.append('<div class="card"><h2>🌍 外資買賣超</h2><div id="foreignChartWrap"><canvas id="foreignChart"></canvas></div></div>')
        
        # === Norway 6週趨勢圖 ===
        shareholder_list = data.get("shareholder", [])
        if shareholder_list:
            sh = shareholder_list[0]
            weekly = sh.get("weekly_changes", {})
            if weekly:
                lines.append('<div class="card"><h2>🇳🇴 集保大戶持有率 — 6週趨勢</h2><p class="chart-desc">數據來源: Norway.twsthr.info</p><div class="chart-container"><canvas id="norwayWeeklyChart"></canvas></div></div>')
                
                week_dates = list(weekly.keys())
                week_values = list(weekly.values())
                week_total = sh.get("total_change", 0)
                
                lines.append(f'<script>')
                lines.append(f'new Chart(document.getElementById("norwayWeeklyChart").getContext("2d"),{{')
                lines.append(f'type:"line",')
                lines.append(f'data:{{')
                lines.append(f'labels:{json.dumps(week_dates)},')
                lines.append(f'datasets:[')
                lines.append(f'{{label:"週增減%",data:{json.dumps(week_values)},borderColor:"#ffc107",backgroundColor:"rgba(255,193,7,0.1)",fill:true,tension:0.3,pointRadius:4,pointBackgroundColor:{json.dumps(week_values)}.map(v=>v>0?"#27ae60":"#c0392b")}}')
                lines.append(f']')
                lines.append(f'}},')
                lines.append(f'options:{{responsive:true,maintainAspectRatio:false,plugins:{{annotation:{{annotations:{{line1:{{type:"line",yMin:0,yMax:0,borderColor:"rgba(148,163,184,0.5)",borderWidth:1,borderDash:[5,5]}}}}}}}},scales:{{y:{{title:{{display:true,text:"週增減 %"}}}}}}}}')
                lines.append(f'}});')
                lines.append(f'</script>')

                # === 大戶各周變化數據明細表 ===
                lines.append('<div class="card"><h2>📋 大戶各周變化數據明細</h2><p class="chart-desc">Norway.twsthr.info — 每週集保結算日大戶持股比例變化</p><div class="table-responsive"><table class="data-table"><thead><tr><th>週別</th><th>結算日期</th><th>大戶持有率變化</th><th>方向</th><th>累計變化</th></tr></thead><tbody>')
                cumulative = 0.0
                for idx, (wd, wv) in enumerate(zip(week_dates, week_values), 1):
                    cumulative += wv
                    direction_icon = "📈" if wv > 0 else "📉" if wv < 0 else "➡️"
                    direction_class = "up" if wv > 0 else "down" if wv < 0 else "neutral"
                    cum_class = "up" if cumulative > 0 else "down" if cumulative < 0 else "neutral"
                    lines.append(f'<tr><td>第 {idx} 週</td><td>{wd}</td><td class="{direction_class}">{direction_icon} {wv:+.2f}%</td><td>{"增持" if wv > 0 else "減持" if wv < 0 else "持平"}</td><td class="{cum_class}">{cumulative:+.2f}%</td></tr>')
                lines.append(f'<tr style="font-weight:700;background:rgba(255,193,7,0.05);"><td colspan="2">總計（{len(week_dates)} 週）</td><td colspan="2">—</td><td class="{"up" if week_total > 0 else "down" if week_total < 0 else "neutral"}">{week_total:+.2f}%</td></tr>')
                lines.append('</tbody></table></div></div>')
        
        lines.append('</div>')
        lines.append(self._footer())

        # 兼容新舊 price_data 格式
        if isinstance(price_data, dict):
            closes = price_data.get("Close", [])
            price_closes = closes[-60:] if closes else []
            price_labels = [f"D-{i}" for i in range(len(price_closes), 0, -1)]
        elif isinstance(price_data, list):
            last_60 = price_data[-60:] if price_data else []
            price_labels = [p.get("Date", "") for p in last_60]
            price_closes = [p.get("Close", 0) for p in last_60]
        else:
            price_labels = []
            price_closes = []

        # 外資數據
        foreign_dates = [f["date"][:10] for f in foreign[-20:]] if foreign else []
        foreign_nets = []
        for f in foreign[-20:]:
            buy = float(f.get("buy",0)) if f.get("buy") else 0
            sell = float(f.get("sell",0)) if f.get("sell") else 0
            foreign_nets.append(buy - sell)

        lines.append('<script>')
        # 計算均線 (MA5 / MA10 / MA20)
        def calc_ma(data, period):
            ma = []
            for i in range(len(data)):
                if i < period - 1:
                    ma.append(None)
                else:
                    ma.append(round(sum(data[i-period+1:i+1]) / period, 2))
            return ma
        ma5 = calc_ma(price_closes, 5) if len(price_closes) >= 5 else []
        ma10 = calc_ma(price_closes, 10) if len(price_closes) >= 10 else []
        ma20 = calc_ma(price_closes, 20) if len(price_closes) >= 20 else []
        # 股價走勢圖 + 均線
        if len(price_closes) >= 5:
            datasets = [
                {'label': '收盤價', 'data': price_closes, 'borderColor': '#1d4ed8', 'backgroundColor': 'rgba(29,78,216,0.08)', 'fill': True, 'tension': 0.3, 'pointRadius': 0, 'borderWidth': 2},
            ]
            if ma5:
                datasets.append({'label': 'MA5', 'data': ma5, 'borderColor': '#f97316', 'backgroundColor': 'transparent', 'fill': False, 'tension': 0.3, 'pointRadius': 0, 'borderWidth': 1.5})
            if ma10:
                datasets.append({'label': 'MA10', 'data': ma10, 'borderColor': '#8b5cf6', 'backgroundColor': 'transparent', 'fill': False, 'tension': 0.3, 'pointRadius': 0, 'borderWidth': 1.5})
            if ma20:
                datasets.append({'label': 'MA20', 'data': ma20, 'borderColor': '#64748b', 'backgroundColor': 'transparent', 'fill': False, 'tension': 0.3, 'pointRadius': 0, 'borderWidth': 1.5})
            datasets_json = json.dumps(datasets, ensure_ascii=False)
            lines.append(f'new Chart(document.getElementById("priceChart").getContext("2d"),{{type:"line",data:{{labels:{json.dumps(price_labels)},datasets:{datasets_json}}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:true,labels:{{usePointStyle:true,boxWidth:8}}}}}},scales:{{x:{{grid:{{color:"rgba(0,0,0,0.05)"}},ticks:{{color:"#64748b"}}}},y:{{grid:{{color:"rgba(0,0,0,0.05)"}},ticks:{{color:"#64748b"}},title:{{display:true,text:"價格",color:"#64748b"}}}}}}}}}});')
        else:
            lines.append('document.getElementById("priceChart").parentElement.innerHTML = \'<p style="text-align:center;color:#64748b;padding:2rem;">歷史價格數據不足，無法繪製走勢圖</p>\';')

        # 外資買賣超圖 — 若只有 0~1 個數據點則顯文字統計
        if len(foreign_nets) >= 2:
            lines.append(f'new Chart(document.getElementById("foreignChart").getContext("2d"),{{type:"bar",data:{{labels:{json.dumps(foreign_dates)},datasets:[{{label:"外資淨買超",data:{json.dumps(foreign_nets)},backgroundColor:{json.dumps(foreign_nets)}.map(v=>v>0?"rgba(22,163,74,0.7)":"rgba(220,38,38,0.7)"),borderColor:{json.dumps(foreign_nets)}.map(v=>v>0?"#16a34a":"#dc2626"),borderWidth:1}}]}},options:{{responsive:true,maintainAspectRatio:false,scales:{{y:{{title:{{display:true,text:"張數"}}}}}}}}}});')
        else:
            # 單日或無數據時顯文字
            if len(foreign_nets) == 1:
                val = foreign_nets[0]
                color = "#16a34a" if val > 0 else "#dc2626"
                sign = "+" if val > 0 else ""
                lines.append(f'document.getElementById("foreignChartWrap").innerHTML = \'<div style="text-align:center;padding:2rem;"><p style="font-size:1.2rem;color:#1e293b;font-weight:600;">外資 {foreign_dates[0] if foreign_dates else ""} 淨買超</p><p style="font-size:2.5rem;color:{color};font-weight:700;margin:0.5rem 0;">{sign}{val:,.0f} 張</p><p style="color:#64748b;font-size:0.9rem;">{"✅ 買超" if val > 0 else "❌ 賣超"}</p></div>\';')
            else:
                lines.append('document.getElementById("foreignChartWrap").innerHTML = \'<p style="text-align:center;color:#64748b;padding:2rem;">暫無外資買賣超數據</p>\';')

        # === MACD 計算與圖表 (12,26,9) ===
        def calc_ema(data, period):
            ema = []
            multiplier = 2 / (period + 1)
            for i, val in enumerate(data):
                if i == 0:
                    ema.append(val)
                else:
                    ema.append(val * multiplier + ema[i-1] * (1 - multiplier))
            return ema
        if len(price_closes) >= 35:
            ema12 = calc_ema(price_closes, 12)
            ema26 = calc_ema(price_closes, 26)
            macd_line = [round(e12 - e26, 4) for e12, e26 in zip(ema12, ema26)]
            signal_line = calc_ema(macd_line, 9)
            histogram = [round(m - s, 4) for m, s in zip(macd_line, signal_line)]
            macd_labels = price_labels[-len(macd_line):] if len(price_labels) >= len(macd_line) else price_labels

            # MACD 最新數值顯示
            latest_dif = macd_line[-1] if macd_line else 0
            latest_sig = signal_line[-1] if signal_line else 0
            latest_osc = histogram[-1] if histogram else 0
            prev_dif = macd_line[-2] if len(macd_line) >= 2 else latest_dif
            prev_sig = signal_line[-2] if len(signal_line) >= 2 else latest_sig
            prev_osc = histogram[-2] if len(histogram) >= 2 else latest_osc
            def _arrow(val, prev):
                if val > prev: return '<span style="color:#22c55e;">▲</span>'
                elif val < prev: return '<span style="color:#ef4444;">▼</span>'
                return '<span style="color:#94a3b8;">—</span>'
            osc_color = '#22c55e' if latest_osc >= 0 else '#ef4444'
            macd_html = f'<div><strong style="color:var(--text-muted);">DIF(12,26)</strong> <span style="font-weight:600;">{latest_dif:.2f}</span> {_arrow(latest_dif, prev_dif)}</div>' \
                        f'<div><strong style="color:var(--text-muted);">MACD(9)</strong> <span style="font-weight:600;">{latest_sig:.2f}</span> {_arrow(latest_sig, prev_sig)}</div>' \
                        f'<div><strong style="color:var(--text-muted);">OSC</strong> <span style="font-weight:600;color:{osc_color}">{latest_osc:+.2f}</span> {_arrow(latest_osc, prev_osc)}</div>'
            lines.append(f'document.getElementById("macd-values").innerHTML = \'{macd_html}\';')

            lines.append(f'new Chart(document.getElementById("macdChart").getContext("2d"),{{')
            lines.append(f'type:"bar",')
            lines.append(f'data:{{')
            lines.append(f'labels:{json.dumps(macd_labels)},')
            lines.append(f'datasets:[')
            lines.append(f'{{type:"line",label:"MACD 柱線",data:{json.dumps(macd_line)},borderColor:"#38bdf8",backgroundColor:"transparent",fill:false,pointRadius:0,borderWidth:1.5,tension:0.1}},')
            lines.append(f'{{type:"line",label:"訊號線",data:{json.dumps(signal_line)},borderColor:"#fbbf24",backgroundColor:"transparent",fill:false,pointRadius:0,borderWidth:1.5,tension:0.1}},')
            lines.append(f'{{label:"柱狀圖",data:{json.dumps(histogram)},backgroundColor:{json.dumps(histogram)}.map(v=>v>=0?"rgba(34,197,94,0.6)":"rgba(239,68,68,0.6)"),borderColor:{json.dumps(histogram)}.map(v=>v>=0?"#22c55e":"#ef4444"),borderWidth:1}}')
            lines.append(f']')
            lines.append(f'}},')
            lines.append(f'options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:true,labels:{{usePointStyle:true,boxWidth:8}}}}}},scales:{{x:{{grid:{{color:"rgba(0,0,0,0.05)"}},ticks:{{color:"#64748b",maxRotation:45}}}},y:{{grid:{{color:"rgba(0,0,0,0.05)"}},ticks:{{color:"#64748b"}},title:{{display:true,text:"MACD 值",color:"#64748b"}}}}}}}}}});')
        else:
            lines.append('document.getElementById("macd-values").innerHTML = \'\';')
            lines.append('document.getElementById("macdChart").parentElement.innerHTML = \'<p style="text-align:center;color:#94a3b8;padding:2rem;">歷史價格數據不足（需 ≥35 筆），無法計算 MACD</p>\';')
        lines.append('</script>')
        lines.append('</body></html>')

        filepath = os.path.join(DOCS_DIR, f"stock_{stock_id}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("".join(lines))
        return filepath

    def generate_cross_analysis_page(self):
        """生成交叉比對報告頁面"""
        cross_data = {}
        try:
            with open("data/cross_analysis/cross_analysis.json", "r", encoding="utf-8") as f:
                cross_data = json.load(f)
        except:
            return None
        
        lines = []
        lines.append(self._head("交叉比對報告｜智董籌碼選股站"))
        lines.append('<body>')
        lines.append(self._nav(""))
        
        s = cross_data.get("summary", {})
        lines.append(f'<div class="container"><div class="header-info"><h1>🔗 籌碼數據交叉比對報告</h1><p class="subtitle">fortune-fred vs Norway.twsthr.info | 分析日期: {s.get("analysis_date", "")}</p></div>')
        
        # 摘要卡片
        lines.append('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:30px;">')
        lines.append(f'<div class="metric-card"><h3>📊 共同覆蓋</h3><p style="font-size:2rem;font-weight:700;color:#3b82f6;">{s.get("common_stocks", 0)}</p><p>檔股票</p></div>')
        lines.append(f'<div class="metric-card"><h3>✅ 方向一致率</h3><p style="font-size:2rem;font-weight:700;color:#10b981;">{s.get("direction_match_rate", 0)}%</p><p>兩邊增減方向相同</p></div>')
        lines.append(f'<div class="metric-card"><h3>📏 平均差異</h3><p style="font-size:2rem;font-weight:700;color:#f59e0b;">{s.get("avg_abs_diff", 0)}%</p><p>絕對差異平均值</p></div>')
        lines.append(f'<div class="metric-card"><h3>⚠️ 最大差異</h3><p style="font-size:2rem;font-weight:700;color:#ef4444;">{s.get("max_abs_diff", 0)}%</p><p>單一股票最大差異</p></div>')
        lines.append('</div>')
        
        # 差異 Top 20 表格
        lines.append('<div class="card"><h2>📋 差異最大的股票 (Top 20)</h2><div class="table-responsive"><table class="data-table"><thead><tr><th>排名</th><th>代碼</th><th>名稱</th><th>fortune-fred</th><th>Norway</th><th>差異</th><th>方向</th></tr></thead><tbody>')
        for i, c in enumerate(cross_data.get("comparisons", [])[:20], 1):
            direction = "✅ 一致" if c["direction_match"] else "❌ 相反"
            direction_color = "#10b981" if c["direction_match"] else "#ef4444"
            lines.append(f'<tr><td>{i}</td><td><strong>{c["stock_code"]}</strong></td><td>{c["stock_name"]}</td><td>{c["chip_change"]:+.2f}%</td><td>{c["norway_change"]:+.2f}%</td><td>{c["diff"]:+.2f}%</td><td style="color:{direction_color};font-weight:600;">{direction}</td></tr>')
        lines.append('</tbody></table></div></div>')
        
        # 方向不一致列表
        mismatches = [c for c in cross_data.get("comparisons", []) if not c["direction_match"]]
        if mismatches:
            lines.append('<div class="card"><h2>⚠️ 方向不一致的股票</h2><div class="table-responsive"><table class="data-table"><thead><tr><th>代碼</th><th>名稱</th><th>fortune-fred</th><th>Norway</th><th>建議</th></tr></thead><tbody>')
            for c in mismatches:
                if abs(c["chip_change"]) > abs(c["norway_change"]):
                    advice = "以 fortune-fred 為準"
                else:
                    advice = "以 Norway 為準"
                lines.append(f'<tr><td><strong>{c["stock_code"]}</strong></td><td>{c["stock_name"]}</td><td>{c["chip_change"]:+.2f}%</td><td>{c["norway_change"]:+.2f}%</td><td>{advice}</td></tr>')
            lines.append('</tbody></table></div></div>')
        
        lines.append('</div>')
        lines.append(self._footer())
        lines.append('</body></html>')
        
        filepath = os.path.join(DOCS_DIR, "cross_analysis.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("".join(lines))
        print(f"[OK] 交叉比對: {filepath}")
        return filepath

    def generate_sector(self):
        """生成族群輪動儀表板 sector.html — 數據動態填充"""
        import json as _json
        from config import BIG_HOLDER_MISSED

        # === 族群映射表 ===
        SECTOR_MAP = {
            "2317": "semiconductor", "2324": "ai-server", "2327": "passive-component",
            "2330": "semiconductor", "2337": "semiconductor", "2344": "memory",
            "2345": "semiconductor", "2355": "pcb", "2356": "ai-server",
            "2357": "semiconductor", "2368": "pcb", "2376": "ai-server",
            "2377": "semiconductor", "2382": "ai-server", "2383": "pcb",
            "2404": "semiconductor", "2408": "memory", "2409": "display",
            "2428": "semiconductor", "2439": "semiconductor", "2449": "semiconductor",
            "2481": "semiconductor", "2492": "passive-component", "2634": "aerospace-defense",
            "2881": "financial", "2882": "financial", "3006": "memory",
            "3016": "semiconductor", "3017": "semiconductor", "3036": "semiconductor",
            "3037": "pcb", "3217": "semiconductor", "3231": "ai-server",
            "3264": "semiconductor", "3376": "semiconductor", "3443": "semiconductor",
            "3450": "silicon-photonics", "3481": "display", "3653": "semiconductor",
            "3661": "semiconductor", "3665": "semiconductor", "3680": "semiconductor",
            "3707": "sic-power", "3711": "semiconductor", "4961": "semiconductor",
            "4966": "semiconductor", "4967": "semiconductor", "5274": "semiconductor",
            "5347": "semiconductor", "5439": "semiconductor", "6147": "semiconductor",
            "6151": "semiconductor", "6173": "passive-component", "6182": "semiconductor",
            "6187": "semiconductor", "6191": "semiconductor", "6207": "semiconductor",
            "6213": "pcb", "6223": "semiconductor", "6239": "semiconductor",
            "6261": "semiconductor", "6271": "semiconductor", "6274": "pcb",
            "6415": "semiconductor", "6446": "biotech", "6510": "semiconductor",
            "6515": "semiconductor", "6669": "semiconductor", "6770": "memory",
            "6805": "semiconductor", "6821": "satellite", "8042": "passive-component",
            "8046": "pcb", "8150": "semiconductor", "8210": "semiconductor",
            "8261": "sic-power", "8358": "passive-component", "8996": "semiconductor",
            "1590": "semiconductor", "1727": "semiconductor", "1815": "passive-component",
            "2002": "semiconductor", "2301": "semiconductor", "2303": "semiconductor",
            "2308": "semiconductor", "2313": "pcb", "2382": "ai-server",
        }

        # === 讀取模板（從 workspace 備份恢復，避免編碼損壞） ===
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        backup_path = os.path.join(workspace_root, "sector.html")
        template_path = os.path.join(DOCS_DIR, "sector.html")
        if os.path.exists(backup_path):
            with open(backup_path, "r", encoding="utf-8") as f:
                template = f.read()
        else:
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()

        # === 生成 stocks 數組 ===
        screened = self.data.get("screened", [])
        stocks_list = []
        for s in screened:
            sid = s.get("stock_id", "")
            sector = SECTOR_MAP.get(sid, "semiconductor")
            tech = s.get("technical", {}) or {}
            pros, cons = [], []
            if s.get("dual_certified"):
                pros.append("雙重認證")
            bh_chg = s.get("big_holder_change", 0)
            if bh_chg >= 5:
                pros.append("大戶大幅增持")
            elif bh_chg >= 2:
                pros.append("大戶增倉明顯")
            elif bh_chg <= -2:
                cons.append("大戶減倉")
            fn = s.get("foreign_net", 0)
            tn = s.get("trust_net", 0)
            if fn > 0 and tn > 0:
                pros.append("法人同步買超")
            if fn > 10000000:
                pros.append("外資大買")
            cp = s.get("change_pct", 0)
            if cp >= 5:
                pros.append("漲幅強勁")
            elif cp <= -3:
                cons.append("跌幅較大")
            trend = tech.get("trend", "")
            if "多頭" in trend:
                pros.append("均線多頭")
            elif "空頭" in trend:
                cons.append("均線空頭")
            rsi = tech.get("rsi", 0)
            if rsi > 75:
                cons.append("RSI過熱")
            stocks_list.append({
                "ticker": sid,
                "name": s.get("stock_name", ""),
                "sector": sector,
                "price": s.get("close", 0),
                "change_pct": cp,
                "big_holder_pct": s.get("big_holder_pct", 0),
                "bh_wow": bh_chg,
                "foreign": fn,
                "volume": None,
                "eps_q1": None,
                "revenue_yoy": None,
                "pe": None,
                "pros": pros,
                "cons": cons,
            })

        # === 生成 missed 數組 ===
        bhr = self.data.get("big_holder_rank", [])
        bhr_map = {b["stock_id"]: {**b, "rank": i+1} for i, b in enumerate(bhr)}
        missed_list = []
        for sid in BIG_HOLDER_MISSED:
            b = bhr_map.get(sid, {})
            bh_chg = b.get("big_holder_change", 0)
            cp = b.get("change_pct", 0)
            missed_list.append({
                "ticker": sid,
                "name": b.get("stock_name", ""),
                "rank": b.get("rank", 0),
                "bh_wow": f"{bh_chg:+.2f}%",
                "weekly_chg": f"{cp:+.2f}%",
                "bh_pct": f"{b.get('big_holder_pct',0):.2f}%",
                "signals": [],
                "category": SECTOR_MAP.get(sid, "其他"),
                "relation": "",
            })

        # === 替換佔位符 ===
        stocks_js = _json.dumps(stocks_list, ensure_ascii=False)
        missed_js = _json.dumps(missed_list, ensure_ascii=False)
        template = template.replace(
            "// <!-- STOCKS_DATA_START -->\n// <!-- STOCKS_DATA_END -->",
            f"const stocks = {stocks_js};"
        )
        template = template.replace(
            "// <!-- MISSED_DATA_START -->\n// <!-- MISSED_DATA_END -->",
            f"const missed = {missed_js};"
        )

        # 更新統計日期
        update_time = self.data.get("update_time", "")
        bh_date = update_time.split()[0] if update_time else ""
        template = template.replace(
            "更新時間：2026-05-22",
            f"更新時間：{update_time}" if update_time else "更新時間：2026-05-22"
        )
        template = template.replace(
            "大戶籌碼統計日期：2026-05-15",
            f"大戶籌碼統計日期：{bh_date}" if bh_date else "大戶籌碼統計日期：2026-05-15"
        )

        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template)
        print(f"[OK] sector: {template_path}")
        return template_path

    def generate_all(self):
        os.makedirs(DOCS_DIR, exist_ok=True)
        self.generate_index()
        self.generate_watchlist()
        self.generate_etf_00981a()
        self.generate_cross_analysis_page()
        self.generate_sector()
        all_stocks = list(set(WATCHLIST + ETF_00981A_HOLDINGS))
        for stock_id in all_stocks:
            self.generate_stock_detail(stock_id)
        print(f"[OK] 全部完成！共 {len(all_stocks)} 檔個股看板")


def generate():
    gen = HTMLGenerator()
    gen.generate_all()

if __name__ == "__main__":
    generate()
