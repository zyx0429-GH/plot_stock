import sys

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\generate_html.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix nav - add 00982A before big_holder_top25
old = '("etf_00981a.html","?? 00981A"),("big_holder_top25.html","??jTOP25")'
new = '("etf_00981a.html","?? 00981A"),("etf_00982a.html","?? 00982A"),("big_holder_top25.html","??jTOP25")'

if old in content:
    content = content.replace(old, new)
    sys.stdout.write('[OK] Added 00982A to nav\n')
else:
    sys.stdout.write('[WARN] Nav patch not applied\n')

# Add 00982A dual certified and triple certified to index page after 00981A dual certified
# Find the end of dual certified section
old2 = '''        lines.append('</tbody></table></div></div>')

        # 外資買超 / 賣超榜單（單日數據）'''

new2 = '''        lines.append('</tbody></table></div></div>')

        # 雙重認證榜單 (00982A)
        dual_certified_982a = self.data.get("dual_certified_982a", [])
        lines.append('<div class="card"><h2>🔥 雙重認證榜單 (00982A + 大戶增倉 + 法人買超)</h2><div class="table-responsive"><table class="data-table"><thead><tr><th>代號</th><th>名稱</th><th>收盤價</th><th>漲跌%</th><th>外資淨買</th><th>投信淨買</th><th>大戶%</th><th>週增減</th><th>趨勢</th><th>評分</th></tr></thead><tbody>')
        for s in dual_certified_982a[:20]:
            tech = s.get("technical", {}) or {}
            trend = tech.get("trend", "")
            tc = "bull" if "多頭" in trend else "bear" if "空頭" in trend else ""
            close = s.get("close") if s.get("close") is not None else 0.0
            change_pct = s.get("change_pct") if s.get("change_pct") is not None else 0.0
            foreign_net = s.get("foreign_net") if s.get("foreign_net") is not None else 0
            trust_net = s.get("trust_net") if s.get("trust_net") is not None else 0
            big_holder_pct = s.get("big_holder_pct") if s.get("big_holder_pct") is not None else 0.0
            big_holder_change = s.get("big_holder_change") if s.get("big_holder_change") is not None else 0.0
            score = s.get("score") if s.get("score") is not None else 0
            lines.append(f'<tr onclick="location.href=\'stock_{s.get(\"stock_id\",\"-\")}.html\'" class="clickable"><td><strong>{s.get(\"stock_id\",\"-\")}</strong></td><td>{s.get(\"stock_name\",\"-\")}</td><td>{close:.2f}</td><td class="{{\"up\" if change_pct>0 else \"down\"}}">{change_pct:+.2f}%</td><td class="{{\"buy\" if foreign_net>0 else \"sell\"}}">{foreign_net:,}</td><td class="{{\"buy\" if trust_net>0 else \"sell\"}}">{trust_net:,}</td><td class="highlight">{big_holder_pct:.2f}%</td><td class="{{\"up\" if big_holder_change>0 else \"down\"}}">{big_holder_change:+.2f}%</td><td class="{tc}">{trend}</td><td><span class="score">{score}</span></td></tr>')
        lines.append('</tbody></table></div></div>')

        # 三重認證榜單 (00981A 或 00982A + 大戶增倉 + 法人買超)
        triple_certified = self.data.get("triple_certified", [])
        lines.append('<div class="card"><h2>👑 三重認證榜單 (00981A 或 00982A + 大戶增倉 + 法人買超)</h2><p class="chart-desc">入選 00981A 或 00982A 成分股（任一即可），且大戶增倉 + 法人買超 — 最強篩選條件</p><div class="table-responsive"><table class="data-table"><thead><tr><th>代號</th><th>名稱</th><th>收盤價</th><th>漲跌%</th><th>外資淨買</th><th>投信淨買</th><th>大戶%</th><th>週增減</th><th>趨勢</th><th>評分</th></tr></thead><tbody>')
        for s in triple_certified[:20]:
            tech = s.get("technical", {}) or {}
            trend = tech.get("trend", "")
            tc = "bull" if "多頭" in trend else "bear" if "空頭" in trend else ""
            close = s.get("close") if s.get("close") is not None else 0.0
            change_pct = s.get("change_pct") if s.get("change_pct") is not None else 0.0
            foreign_net = s.get("foreign_net") if s.get("foreign_net") is not None else 0
            trust_net = s.get("trust_net") if s.get("trust_net") is not None else 0
            big_holder_pct = s.get("big_holder_pct") if s.get("big_holder_pct") is not None else 0.0
            big_holder_change = s.get("big_holder_change") if s.get("big_holder_change") is not None else 0.0
            score = s.get("score") if s.get("score") is not None else 0
            lines.append(f'<tr onclick="location.href=\'stock_{s.get(\"stock_id\",\"-\")}.html\'" class="clickable"><td><strong>{s.get(\"stock_id\",\"-\")}</strong></td><td>{s.get(\"stock_name\",\"-\")}</td><td>{close:.2f}</td><td class="{{\"up\" if change_pct>0 else \"down\"}}">{change_pct:+.2f}%</td><td class="{{\"buy\" if foreign_net>0 else \"sell\"}}">{foreign_net:,}</td><td class="{{\"buy\" if trust_net>0 else \"sell\"}}">{trust_net:,}</td><td class="highlight">{big_holder_pct:.2f}%</td><td class="{{\"up\" if big_holder_change>0 else \"down\"}}">{big_holder_change:+.2f}%</td><td class="{tc}">{trend}</td><td><span class="score">{score}</span></td></tr>')
        lines.append('</tbody></table></div></div>')

        # 外資買超 / 賣超榜單（單日數據）'''

if old2 in content:
    content = content.replace(old2, new2)
    sys.stdout.write('[OK] Added 00982A dual and triple certified to index\n')
else:
    sys.stdout.write('[WARN] Index page patch not applied\n')

with open(r'C:\Users\user\.kimi_openclaw\workspace\plot_stock\scripts\generate_html.py', 'w', encoding='utf-8') as f:
    f.write(content)

sys.stdout.write('Done!\n')
