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
<script src="js/app.js" defer></script>
</head>"""

    def _nav(self, active=""):
        items = [("index.html","📊 首頁"),("watchlist.html","⭐ 自選"),("etf_00981a.html","📈 00981A")]
        html = '<nav class="navbar"><div class="nav-brand">🔥 智董籌碼選股站</div><div class="nav-links">'
        for href, text in items:
            cls = "active" if active in href else ""
            html += f'<a href="{href}" class="{cls}">{text}</a>'
        html += '</div></nav>'
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

        # 散點圖
        lines.append('<div class="card"><h2>🔥 大戶持股% vs 週增減</h2><p class="chart-desc">X:大戶持股% Y:週增減% 點擊進入個股</p><div class="chart-container"><canvas id="scatterChart"></canvas></div></div>')

        # 外資連買
        lines.append(f'<div class="card"><h2>🌍 外資連買 {SCREEN_CONFIG["foreign_buy_days"]} 天榜單</h2><div class="table-responsive"><table class="data-table"><thead><tr><th>代號</th><th>名稱</th><th>收盤價</th><th>漲跌%</th><th>外資淨買</th><th>大戶%</th><th>趨勢</th><th>評分</th></tr></thead><tbody>')
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

        # 多頭排列
        lines.append('<div class="card"><h2>📈 多頭排列清單</h2><div class="table-responsive"><table class="data-table"><thead><tr><th>代號</th><th>名稱</th><th>收盤價</th><th>20MA</th><th>60MA</th><th>RSI</th><th>大戶%</th><th>外資連買</th></tr></thead><tbody>')
        for s in bull_stocks[:30]:
            tech = s.get("technical",{}) or {}
            close = s.get("close") if s.get("close") is not None else 0.0
            big_holder_pct = s.get("big_holder_pct") if s.get("big_holder_pct") is not None else 0.0
            foreign_consecutive = bool(s.get("foreign_consecutive_buy"))
            lines.append(f'<tr onclick="location.href=\'stock_{s.get("stock_id","-")}.html\'" class="clickable"><td><strong>{s.get("stock_id","-")}</strong></td><td>{s.get("stock_name","-")}</td><td>{close:.2f}</td><td>{tech.get("ma20","-")}</td><td>{tech.get("ma60","-")}</td><td>{tech.get("rsi","-")}</td><td>{big_holder_pct:.2f}%</td><td>{"✅" if foreign_consecutive else "❌"}</td></tr>')
        lines.append('</tbody></table></div></div>')

        # 大戶排名
        lines.append('<div class="card"><h2>👑 大戶持股排名 (400張以上)</h2><div class="controls"><label>顯示前 <input type="number" id="rankLimit" value="50" min="10" max="200" onchange="updateRank()"> 名</label><label>最小持股% <input type="number" id="minPct" value="0" min="0" max="100" step="0.1" onchange="updateRank()"></label></div><div class="table-responsive"><table class="data-table" id="bigHolderTable"><thead><tr><th>排名</th><th>代號</th><th>名稱</th><th>大戶%</th><th>週增減%</th><th>收盤價</th><th>漲跌%</th></tr></thead><tbody>')
        for i, s in enumerate(top_big, 1):
            big_holder_pct = s.get("big_holder_pct") if s.get("big_holder_pct") is not None else 0.0
            big_holder_change = s.get("big_holder_change") if s.get("big_holder_change") is not None else 0.0
            close = s.get("close") if s.get("close") is not None else 0.0
            change_pct = s.get("change_pct") if s.get("change_pct") is not None else 0.0
            cc = "up" if big_holder_change>0 else "down" if big_holder_change<0 else ""
            lines.append(f'<tr data-pct="{big_holder_pct}"><td>{i}</td><td><strong>{s.get("stock_id","-")}</strong></td><td>{s.get("stock_name","-")}</td><td class="highlight">{big_holder_pct:.2f}%</td><td class="{cc}">{big_holder_change:+.2f}%</td><td>{close:.2f}</td><td class="{"up" if change_pct>0 else "down"}">{change_pct:+.2f}%</td></tr>')
        lines.append('</tbody></table></div></div>')

        lines.append('</div>')
        lines.append(self._footer())

        # JS
        sd = json.dumps(scatter_data, ensure_ascii=False)
        lines.append(f'<script>')
        lines.append(f'const scatterData = {sd};')
        lines.append('const ctx = document.getElementById("scatterChart").getContext("2d");')
        lines.append('new Chart(ctx, {type:"scatter",data:{datasets:[{label:"個股籌碼分布",data:scatterData.map(d=>({x:d.x,y:d.y})),backgroundColor:scatterData.map(d=>d.y>0?"rgba(46,204,113,0.6)":"rgba(231,76,60,0.6)"),borderColor:scatterData.map(d=>d.y>0?"#27ae60":"#c0392b"),borderWidth:1,pointRadius:6,pointHoverRadius:10}]},options:{responsive:true,maintainAspectRatio:false,plugins:{tooltip:{callbacks:{label:function(c){const d=scatterData[c.dataIndex];return d.stock_id+" "+d.stock_name+": 大戶"+d.x.toFixed(2)+"%,週增減"+d.y.toFixed(2)+"%";}}}},scales:{x:{title:{display:true,text:"大戶持股 %"}},y:{title:{display:true,text:"本週增減 %"}}},onClick:(e,elements)=>{if(elements.length>0){const idx=elements[0].index;window.location.href="stock_"+scatterData[idx].stock_id+".html";}}}});')
        lines.append('function updateRank(){const limit=parseInt(document.getElementById("rankLimit").value)||50;const minPct=parseFloat(document.getElementById("minPct").value)||0;const rows=document.querySelectorAll("#bigHolderTable tbody tr");rows.forEach((row,idx)=>{const pct=parseFloat(row.dataset.pct);row.style.display=(idx<limit&&pct>=minPct)?"":"none";});}')
        lines.append('</script>')
        lines.append('</body></html>')

        filepath = os.path.join(DOCS_DIR, "index.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"✅ 首頁: {filepath}")
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
        lines.append('<div class="card"><div class="table-responsive"><table class="data-table"><thead><tr><th>代號</th><th>名稱</th><th>收盤價</th><th>漲跌%</th><th>外資連買</th><th>外資淨買</th><th>大戶%</th><th>週增減</th><th>券資比</th><th>20MA</th><th>60MA</th><th>RSI</th><th>趨勢</th><th>評分</th></tr></thead><tbody>')

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
            big_holder_change = s.get("big_holder_change") if s.get("big_holder_change") is not None else 0.0
            score = s.get("score") if s.get("score") is not None else 0
            tech = s.get("technical", {}) or {}
            margin = s.get("margin", {}) or {}
            trend = tech.get("trend", "")
            tc = "bull" if "多頭" in trend else "bear" if "空頭" in trend else "neutral"
            lines.append(f'<tr onclick="location.href=\'stock_{sid}.html\'" class="clickable"><td><strong>{sid}</strong></td><td>{sname}</td><td>{close:.2f}</td><td class="{"up" if change_pct>0 else "down"}">{change_pct:+.2f}%</td><td>{"✅" if foreign_consecutive else "❌"}</td><td class="{"buy" if foreign_net>0 else "sell"}">{foreign_net:,}</td><td class="highlight">{big_holder_pct:.2f}%</td><td class="{"up" if big_holder_change>0 else "down"}">{big_holder_change:+.2f}%</td><td>{margin.get("ratio","-") if margin else "-"}</td><td>{tech.get("ma20","-")}</td><td>{tech.get("ma60","-")}</td><td>{tech.get("rsi","-")}</td><td class="{tc}">{trend}</td><td><span class="score">{score}</span></td></tr>')
            # === 補丁結束 ===

        lines.append('</tbody></table></div></div></div>')
        lines.append(self._footer())
        lines.append('</body></html>')

        filepath = os.path.join(DOCS_DIR, f"{page_key}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("".join(lines))
        print(f"✅ {page_key}: {filepath}")
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
        lines.append(f'<div class="metric-card"><h3>📊 技術面</h3><p>20MA: {tech.get("ma20","-")}</p><p>60MA: {tech.get("ma60","-")}</p><p>RSI: {tech.get("rsi","-")}</p><p class="trend">趨勢: {tech.get("trend","-")}</p></div>')
        # === None-safe patch for f-string formatting ===
        foreign_consecutive = screened_item and screened_item.get("foreign_consecutive_buy")
        foreign_net = screened_item["foreign_net"] if screened_item and screened_item.get("foreign_net") is not None else 0
        big_holder_pct = screened_item["big_holder_pct"] if screened_item and screened_item.get("big_holder_pct") is not None else None
        big_holder_change = screened_item["big_holder_change"] if screened_item and screened_item.get("big_holder_change") is not None else None
        bh_pct_str = f"{big_holder_pct:.2f}" if big_holder_pct is not None else "-"
        bh_chg_str = f"{big_holder_change:+.2f}" if big_holder_change is not None else "-"
        # === patch end ===
        lines.append(f'<div class="metric-card"><h3>🌍 外資動向</h3><p>連買{SCREEN_CONFIG["foreign_buy_days"]}天: {"✅" if foreign_consecutive else "❌"}</p><p>淨買超: {foreign_net:,}</p></div>')
        lines.append(f'<div class="metric-card"><h3>👑 籌碼面</h3><p>大戶持股: {bh_pct_str}%</p><p>週增減: {bh_chg_str}%</p></div>')
        lines.append(f'<div class="metric-card"><h3>💰 融資融券</h3><p>券資比: {margin.get("ratio","-") if margin else "-"}</p><p>融資餘額: {margin.get("margin_balance","-") if margin else "-"}</p></div>')
        lines.append('</div>')
        lines.append('<div class="card"><h2>📈 股價走勢</h2><div class="chart-container"><canvas id="priceChart"></canvas></div></div>')
        lines.append('<div class="card"><h2>🌍 外資買賣超</h2><div class="chart-container"><canvas id="foreignChart"></canvas></div></div>')
        lines.append('</div>')
        lines.append(self._footer())

        # 兼容新舊 price_data 格式
        if isinstance(price_data, dict):
            # 新格式: {"Close": [...], "High": [...], ...}
            closes = price_data.get("Close", [])
            price_closes = closes[-60:] if closes else []
            price_labels = [f"D-{i}" for i in range(len(price_closes), 0, -1)]
        elif isinstance(price_data, list):
            # 舊格式: [{"Date": ..., "Close": ...}, ...]
            last_60 = price_data[-60:] if price_data else []
            price_labels = [p.get("Date", "") for p in last_60]
            price_closes = [p.get("Close", 0) for p in last_60]
        else:
            price_labels = []
            price_closes = []
        foreign_dates = [f["date"][:10] for f in foreign[-20:]] if foreign else []
        foreign_nets = []
        for f in foreign[-20:]:
            buy = float(f.get("buy",0)) if f.get("buy") else 0
            sell = float(f.get("sell",0)) if f.get("sell") else 0
            foreign_nets.append(buy - sell)

        lines.append('<script>')
        lines.append(f'new Chart(document.getElementById("priceChart").getContext("2d"),{{type:"line",data:{{labels:{json.dumps(price_labels)},datasets:[{{label:"收盤價",data:{json.dumps(price_closes)},borderColor:"#3498db",backgroundColor:"rgba(52,152,219,0.1)",fill:true,tension:0.4}}]}},options:{{responsive:true,maintainAspectRatio:false,scales:{{y:{{title:{{display:true,text:"價格"}}}}}}}}}});')
        lines.append(f'new Chart(document.getElementById("foreignChart").getContext("2d"),{{type:"bar",data:{{labels:{json.dumps(foreign_dates)},datasets:[{{label:"外資淨買超",data:{json.dumps(foreign_nets)},backgroundColor:{json.dumps(foreign_nets)}.map(v=>v>0?"rgba(46,204,113,0.7)":"rgba(231,76,60,0.7)"),borderColor:{json.dumps(foreign_nets)}.map(v=>v>0?"#27ae60":"#c0392b"),borderWidth:1}}]}},options:{{responsive:true,maintainAspectRatio:false,scales:{{y:{{title:{{display:true,text:"張數"}}}}}}}}}});')
        lines.append('</script>')
        lines.append('</body></html>')

        filepath = os.path.join(DOCS_DIR, f"stock_{stock_id}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("".join(lines))
        return filepath

    def generate_all(self):
        os.makedirs(DOCS_DIR, exist_ok=True)
        self.generate_index()
        self.generate_watchlist()
        self.generate_etf_00981a()
        all_stocks = list(set(WATCHLIST + ETF_00981A_HOLDINGS))
        for stock_id in all_stocks:
            self.generate_stock_detail(stock_id)
        print(f"✅ 全部完成！共 {len(all_stocks)} 檔個股看板")


def generate():
    gen = HTMLGenerator()
    gen.generate_all()

if __name__ == "__main__":
    generate()
