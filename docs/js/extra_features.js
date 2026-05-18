/**
 * plot_stock 擴充功能 — 策略回測、族群輪動、市場情緒、個股彈窗、雷達圖
 * 由 generate_html.py 在 build 時引入
 */

(function() {
    'use strict';

    // ===================== 工具函式 =====================
    const $ = id => document.getElementById(id);
    const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

    // ===================== 股票資料快取 =====================
    let _allStocks = null;
    function getAllStocks() {
        if (_allStocks) return _allStocks;
        // 從頁面上所有表格抓取股票資料
        const rows = document.querySelectorAll('.data-table tbody tr.clickable');
        _allStocks = Array.from(rows).map(tr => {
            const tds = tr.querySelectorAll('td');
            if (tds.length < 4) return null;
            const code = tds[1]?.textContent?.trim() || '';
            const name = tds[2]?.textContent?.trim() || '';
            const close = parseFloat(tds[3]?.textContent) || 0;
            const changePct = parseFloat(tds[4]?.textContent) || 0;
            // 嘗試從 inline dataset 或 pattern match 取得其他欄位
            const bhMatch = tr.textContent.match(/(\d+\.?\d*)%/g);
            const bhPct = bhMatch ? parseFloat(bhMatch[0]) : 0;
            return {
                code, name, close, change_pct: changePct,
                big_holder_pct: bhPct,
                element: tr
            };
        }).filter(Boolean);
        return _allStocks;
    }

    // ===================== 1. 策略回測引擎 =====================
    function runBacktest(rules) {
        const stocks = getAllStocks();
        const matched = stocks.filter(s => {
            // 簡化規則：只檢查今日數據條件
            if (rules.minBigHolderPct && s.big_holder_pct < rules.minBigHolderPct) return false;
            if (rules.maxChangePct !== undefined && s.change_pct > rules.maxChangePct) return false;
            if (rules.minChangePct !== undefined && s.change_pct < rules.minChangePct) return false;
            // 多頭排列：從趨勢欄位判斷
            const trendText = s.element.textContent;
            if (rules.bullOnly && !trendText.includes('多頭排列')) return false;
            return true;
        });

        // 模擬報酬（用今日漲跌當作「1日持有」報酬的 proxy）
        const returns = matched.map(s => s.change_pct);
        const avgReturn = returns.length ? returns.reduce((a,b)=>a+b,0)/returns.length : 0;
        const winRate = returns.length ? returns.filter(r=>r>0).length / returns.length * 100 : 0;
        const maxLoss = returns.length ? Math.min(...returns) : 0;
        const maxGain = returns.length ? Math.max(...returns) : 0;

        return {
            matched,
            total: stocks.length,
            winRate: winRate.toFixed(1),
            avgReturn: avgReturn.toFixed(2),
            maxLoss: maxLoss.toFixed(2),
            maxGain: maxGain.toFixed(2),
            selectedCount: matched.length
        };
    }

    function renderBacktestResults(result) {
        const el = $('backtestResult');
        if (!el) return;
        const color = parseFloat(result.avgReturn) >= 0 ? '#16a34a' : '#dc2626';
        el.innerHTML = `
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:15px;">
                <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:15px;text-align:center;">
                    <div style="color:#94a3b8;font-size:12px;margin-bottom:5px;">選中檔數</div>
                    <div style="font-size:1.5em;font-weight:bold;color:#e2e8f0;">${result.selectedCount} / ${result.total}</div>
                </div>
                <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:15px;text-align:center;">
                    <div style="color:#94a3b8;font-size:12px;margin-bottom:5px;">勝率</div>
                    <div style="font-size:1.5em;font-weight:bold;color:#38bdf8;">${result.winRate}%</div>
                </div>
                <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:15px;text-align:center;">
                    <div style="color:#94a3b8;font-size:12px;margin-bottom:5px;">平均報酬</div>
                    <div style="font-size:1.5em;font-weight:bold;color:${color};">${result.avgReturn}%</div>
                </div>
                <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:15px;text-align:center;">
                    <div style="color:#94a3b8;font-size:12px;margin-bottom:5px;">最大單日虧損</div>
                    <div style="font-size:1.5em;font-weight:bold;color:#dc2626;">${result.maxLoss}%</div>
                </div>
                <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:15px;text-align:center;">
                    <div style="color:#94a3b8;font-size:12px;margin-bottom:5px;">最大單日獲利</div>
                    <div style="font-size:1.5em;font-weight:bold;color:#16a34a;">${result.maxGain}%</div>
                </div>
            </div>
            ${result.selectedCount > 0 ? `
            <div style="margin-top:15px;">
                <div style="color:#fbbf24;font-weight:bold;margin-bottom:8px;">📋 選中股票</div>
                <div style="display:flex;flex-wrap:wrap;gap:6px;">
                    ${result.matched.map(s => `<span style="padding:3px 10px;border-radius:4px;background:#334155;color:#e2e8f0;font-size:12px;">${s.code} ${s.name} <span style="color:${s.change_pct>=0?'#16a34a':'#dc2626'}">${s.change_pct>=0?'+':''}${s.change_pct.toFixed(2)}%</span></span>`).join('')}
                </div>
            </div>` : ''}
        `;
    }

    // ===================== 2. 族群輪動 =====================
    const SECTOR_MAP = {
        '半導體': ['2330','2303','5347','2344','3006','4967','6770','3016','6182','6261','6805','3661','3443','4919','4961','4966','6213','6223','6510','6415','6257'],
        '電子零組件': ['2317','2327','2449','2492','3450','3665','3680','6147','6173','6187','6271','8042','8358','2408','3017','3481','2376','2383','3037','5439'],
        '金融': ['2881','2882'],
        '傳產': ['1216','1301','1319','2002','1590','2355','2356','2404','2409','2428','2481','3005','6177','2030','2031','2032','2033','2034','2025','2023'],
        '汽車': [],
        '消費': [],
        '航運': [],
        '能源': ['1605','2308']
    };

    function getSector(code) {
        for (const [sector, codes] of Object.entries(SECTOR_MAP)) {
            if (codes.includes(code)) return sector;
        }
        return '其他';
    }

    function renderSectorRotation() {
        const stocks = getAllStocks();
        const sectorData = {};
        stocks.forEach(s => {
            const sector = getSector(s.code);
            if (!sectorData[sector]) sectorData[sector] = { stocks: [], totalChange: 0, count: 0, upCount: 0 };
            sectorData[sector].stocks.push(s);
            sectorData[sector].totalChange += s.change_pct;
            sectorData[sector].count++;
            if (s.change_pct > 0) sectorData[sector].upCount++;
        });

        const panel = $('sectorRotationPanel');
        if (!panel) return;

        const sorted = Object.entries(sectorData)
            .map(([name, data]) => ({ name, avgChange: data.count ? data.totalChange / data.count : 0, count: data.count, upCount: data.upCount }))
            .sort((a, b) => b.avgChange - a.avgChange);

        panel.innerHTML = sorted.map(s => {
            const color = s.avgChange >= 0 ? '#16a34a' : '#dc2626';
            const heat = s.avgChange > 2 ? '🔥🔥🔥' : s.avgChange > 0 ? '🔥' : '❄️';
            return `<div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:15px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-weight:bold;color:#e2e8f0;font-size:14px;">${s.name}</span>
                    <span style="font-size:12px;">${heat}</span>
                </div>
                <div style="font-size:1.5em;font-weight:bold;color:${color};margin-bottom:5px;">${s.avgChange>=0?'+':''}${s.avgChange.toFixed(2)}%</div>
                <div style="font-size:12px;color:#94a3b8;">
                    <div>股票數: ${s.count} 檔</div>
                    <div>上漲: ${s.upCount} 檔</div>
                </div>
            </div>`;
        }).join('');
    }

    // ===================== 3. 市場情緒指標 =====================
    function renderMarketSentiment() {
        const stocks = getAllStocks();
        const adv = stocks.filter(s => s.change_pct > 0).length;
        const dec = stocks.filter(s => s.change_pct < 0).length;
        const flat = stocks.length - adv - dec;
        const pct = stocks.length ? (adv / stocks.length) * 100 : 50;

        const advEl = $('advancingCount');
        const decEl = $('decliningCount');
        const flatEl = $('flatCount');
        const sentEl = $('marketSentiment');

        if (advEl) advEl.textContent = adv;
        if (decEl) decEl.textContent = dec;
        if (flatEl) flatEl.textContent = flat;

        if (sentEl) {
            let text, color;
            if (pct >= 70) { text = '🔥 極度樂觀'; color = '#dc2626'; }
            else if (pct >= 55) { text = '📈 偏多'; color = '#16a34a'; }
            else if (pct >= 45) { text = '➡️ 中性'; color = '#94a3b8'; }
            else if (pct >= 30) { text = '📉 偏空'; color = '#f59e0b'; }
            else { text = '❄️ 極度悲觀'; color = '#38bdf8'; }
            sentEl.textContent = `${text} (${pct.toFixed(1)}%)`;
            sentEl.style.color = color;
        }
    }

    // ===================== 4. 個股彈窗 + 雷達圖 =====================
    function calculateRiskScore(stockText) {
        let score = 5;
        if (stockText.includes('RSI')) {
            const rsiMatch = stockText.match(/RSI[:\s]*([\d.]+)/);
            if (rsiMatch) {
                const rsi = parseFloat(rsiMatch[1]);
                if (rsi > 80) score += 3;
                else if (rsi > 70) score += 1.5;
                else if (rsi < 25) score -= 2;
                else if (rsi < 35) score -= 1;
            }
        }
        const changeMatch = stockText.match(/([+-]?\d+\.?\d*)%/);
        if (changeMatch) {
            const chg = Math.abs(parseFloat(changeMatch[1]));
            if (chg > 8) score += 2;
            else if (chg > 5) score += 1;
        }
        return clamp(score, 0, 10);
    }

    function calculateFundamentalScore(stockText) {
        let score = 5;
        if (stockText.includes('多頭排列')) score += 1.5;
        if (stockText.includes('外資連買') || stockText.includes('✅')) score += 1;
        if (stockText.includes('大戶積極進場') || stockText.includes('🚀')) score += 1;
        if (stockText.includes('空頭排列')) score -= 2;
        return clamp(score, 0, 10);
    }

    function showStockPopup(row) {
        // 從 row 抓取所有可見文字
        const stockText = row.textContent;
        const tds = row.querySelectorAll('td');
        const code = tds[1]?.textContent?.trim() || '';
        const name = tds[2]?.textContent?.trim() || '';
        const close = tds[3]?.textContent?.trim() || '';
        const change = tds[4]?.textContent?.trim() || '';

        // 計算各維度分數
        const chipScore = stockText.includes('大戶%') ? (parseFloat(stockText.match(/(\d+\.?\d*)%/)?.[1]) || 50) / 10 : 5;
        const techScore = stockText.includes('多頭排列') ? 8 : stockText.includes('空頭排列') ? 3 : 5;
        const foreignScore = stockText.includes('外資買超') || stockText.includes('✅') ? 8 : 4;
        const volumeScore = 5;
        const riskScore = calculateRiskScore(stockText);
        const fundScore = calculateFundamentalScore(stockText);

        const modal = document.createElement('div');
        modal.id = 'stockPopupModal';
        modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px;';
        modal.innerHTML = `
            <div style="background:#0f172a;border:1px solid #334155;border-radius:12px;max-width:600px;width:100%;max-height:90vh;overflow-y:auto;padding:25px;position:relative;">
                <button onclick="document.getElementById('stockPopupModal').remove()" style="position:absolute;top:15px;right:15px;background:none;border:none;color:#94a3b8;font-size:20px;cursor:pointer;">✕</button>
                <h2 style="color:#38bdf8;margin:0 0 15px 0;font-size:1.4em;">${code} ${name}</h2>
                <div style="display:flex;gap:15px;margin-bottom:15px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:120px;background:#1e293b;border-radius:8px;padding:12px;text-align:center;">
                        <div style="color:#94a3b8;font-size:12px;">收盤價</div>
                        <div style="font-size:1.3em;font-weight:bold;color:#e2e8f0;">${close}</div>
                    </div>
                    <div style="flex:1;min-width:120px;background:#1e293b;border-radius:8px;padding:12px;text-align:center;">
                        <div style="color:#94a3b8;font-size:12px;">漲跌</div>
                        <div style="font-size:1.3em;font-weight:bold;color:${change.includes('-')?'#dc2626':'#16a34a'};">${change}</div>
                    </div>
                </div>
                <div style="margin-bottom:15px;">
                    <div style="color:#fbbf24;font-weight:bold;margin-bottom:8px;">📊 五維雷達圖</div>
                    <div style="max-width:350px;margin:0 auto;">
                        <canvas id="radarChartPopup"></canvas>
                    </div>
                </div>
                <div style="margin-bottom:15px;">
                    <div style="color:#fbbf24;font-weight:bold;margin-bottom:8px;">🎯 訊號標籤</div>
                    <div style="display:flex;flex-wrap:wrap;gap:5px;">
                        ${generateSignalTags(stockText)}
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:12px;color:#94a3b8;">
                    <div style="background:#1e293b;border-radius:6px;padding:10px;">
                        <div style="color:#e2e8f0;font-weight:bold;margin-bottom:4px;">💰 買點</div>
                        ${getBuySignalText(stockText)}
                    </div>
                    <div style="background:#1e293b;border-radius:6px;padding:10px;">
                        <div style="color:#e2e8f0;font-weight:bold;margin-bottom:4px;">📉 停損</div>
                        ${getStopLossText(stockText, close)}
                    </div>
                </div>
                <div style="margin-top:15px;text-align:center;">
                    <a href="stock_${code}.html" style="display:inline-block;background:#3b82f6;color:#fff;padding:8px 20px;border-radius:6px;text-decoration:none;font-size:14px;">📈 查看完整個股頁面</a>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // 繪製雷達圖
        requestAnimationFrame(() => {
            const ctx = document.getElementById('radarChartPopup');
            if (ctx && typeof Chart !== 'undefined') {
                new Chart(ctx, {
                    type: 'radar',
                    data: {
                        labels: ['籌碼面', '技術面', '外資動向', '量能', '基本面'],
                        datasets: [{
                            label: '個股評分',
                            data: [clamp(chipScore,0,10), clamp(techScore,0,10), clamp(foreignScore,0,10), clamp(volumeScore,0,10), clamp(fundScore,0,10)],
                            backgroundColor: 'rgba(59,130,246,0.2)',
                            borderColor: '#3b82f6',
                            pointBackgroundColor: '#3b82f6',
                            pointBorderColor: '#fff',
                            pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: '#3b82f6',
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            r: {
                                min: 0, max: 10,
                                ticks: { stepSize: 2, color: '#64748b', backdropColor: 'transparent' },
                                grid: { color: '#334155' },
                                pointLabels: { color: '#e2e8f0', font: { size: 12 } }
                            }
                        },
                        plugins: { legend: { display: false } }
                    }
                });
            }
        });

        // ESC 關閉
        const escHandler = e => { if (e.key === 'Escape') { modal.remove(); document.removeEventListener('keydown', escHandler); } };
        document.addEventListener('keydown', escHandler);
    }

    function generateSignalTags(text) {
        const tags = [];
        if (text.includes('多頭排列')) tags.push({t:'📈 多頭排列',c:'#16a34a',bg:'#16a34a20'});
        if (text.includes('外資連買') || text.includes('✅')) tags.push({t:'💰 外資連買',c:'#16a34a',bg:'#16a34a20'});
        if (text.includes('大戶積極進場') || text.includes('🚀')) tags.push({t:'👑 大戶進場',c:'#f59e0b',bg:'#f59e0b20'});
        if (text.includes('空頭排列')) tags.push({t:'📉 空頭排列',c:'#dc2626',bg:'#dc262620'});
        const rsiMatch = text.match(/RSI[:\s]*([\d.]+)/);
        if (rsiMatch) {
            const rsi = parseFloat(rsiMatch[1]);
            if (rsi > 75) tags.push({t:`🔥 RSI ${rsi}`,c:'#dc2626',bg:'#dc262620'});
            else if (rsi < 30) tags.push({t:`❄️ RSI ${rsi}`,c:'#38bdf8',bg:'#38bdf820'});
        }
        return tags.map(t => `<span style="padding:3px 8px;border-radius:4px;font-size:11px;color:${t.c};background:${t.bg};border:1px solid ${t.c}40;">${t.t}</span>`).join('');
    }

    function getBuySignalText(text) {
        if (text.includes('多頭排列') && (text.includes('外資連買') || text.includes('✅'))) return '<span style="color:#16a34a;">📈 雙強認證 — 可考慮分批佈局</span>';
        if (text.includes('多頭排列')) return '<span style="color:#16a34a;">📈 趨勢偏多 — 回測均線時關注</span>';
        if (text.includes('外資連買') || text.includes('✅')) return '<span style="color:#f59e0b;">💰 外資買超 — 觀察籌碼配合</span>';
        return '<span style="color:#94a3b8;">➖ 暫無明確買點</span>';
    }

    function getStopLossText(text, closeStr) {
        const close = parseFloat(closeStr) || 0;
        if (!close) return '<span style="color:#94a3b8;">無法計算</span>';
        // 簡化：固定 7% 停損 + 技術停損估計
        const fixedStop = (close * 0.93).toFixed(1);
        return `<span style="color:#dc2626;">固定 7%: ${fixedStop}</span><br><span style="color:#94a3b8;font-size:11px;">建議同時觀察跌破 MA20</span>`;
    }

    // ===================== 5. CSV 匯出 =====================
    function exportToCSV() {
        const stocks = getAllStocks();
        if (!stocks.length) { alert('沒有資料可匯出'); return; }
        const headers = ['代號','名稱','收盤價','漲跌%','大戶%'];
        const rows = stocks.map(s => [s.code, s.name, s.close, s.change_pct, s.big_holder_pct].join(','));
        const csv = '\uFEFF' + [headers.join(','), ...rows].join('\n');
        const blob = new Blob([csv], {type:'text/csv;charset=utf-8;'});
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `plot_stock_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
    }

    // ===================== 6. 滾動到頂 + 快捷鍵 =====================
    function initScrollTop() {
        const btn = document.createElement('div');
        btn.innerHTML = '⬆️';
        btn.style.cssText = 'position:fixed;bottom:30px;right:30px;width:50px;height:50px;background:#334155;color:#e2e8f0;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:20px;z-index:1000;opacity:0;transition:opacity 0.3s;box-shadow:0 4px 12px rgba(0,0,0,0.3);';
        btn.onclick = () => window.scrollTo({top:0, behavior:'smooth'});
        document.body.appendChild(btn);
        window.addEventListener('scroll', () => { btn.style.opacity = window.scrollY > 500 ? '1' : '0'; });
    }

    function initKeyboardShortcuts() {
        document.addEventListener('keydown', e => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const search = document.getElementById('globalSearch') || document.getElementById('stockSearch');
                if (search) search.focus();
            }
            if (e.key === 'Escape') {
                const modal = document.getElementById('stockPopupModal');
                if (modal) modal.remove();
            }
        });
    }

    // ===================== 7. 表格行點擊攔截 + 搜尋即時過濾 =====================
    function initTableClick() {
        document.querySelectorAll('.data-table tbody tr.clickable').forEach(row => {
            // 保留原有 onclick，但加入 shift+點擊 彈出詳情
            row.addEventListener('click', e => {
                if (e.shiftKey) {
                    e.preventDefault();
                    e.stopPropagation();
                    showStockPopup(row);
                }
            });
        });
    }

    // 即時過濾所有表格
    function initLiveFilter() {
        const search = document.getElementById('globalSearch');
        if (!search) return;
        search.addEventListener('input', e => {
            const term = e.target.value.trim().toLowerCase();
            const tables = document.querySelectorAll('.data-table tbody');
            tables.forEach(tb => {
                let visible = 0;
                tb.querySelectorAll('tr').forEach(tr => {
                    const text = tr.textContent.toLowerCase();
                    const show = !term || text.includes(term);
                    tr.style.display = show ? '' : 'none';
                    if (show) visible++;
                });
            });
            // 顯示統計
            let hint = document.getElementById('filterHint');
            if (!hint) {
                hint = document.createElement('div');
                hint.id = 'filterHint';
                hint.style.cssText = 'text-align:center;color:#94a3b8;font-size:13px;margin:8px 0;';
                const firstCard = document.querySelector('.card');
                if (firstCard) firstCard.before(hint);
            }
            if (term) {
                const allRows = document.querySelectorAll('.data-table tbody tr');
                const visibleRows = document.querySelectorAll('.data-table tbody tr:not([style*="none"])');
                hint.textContent = `🔍 「${term}」找到 ${visibleRows.length} / ${allRows.length} 筆結果`;
            } else {
                hint.textContent = '';
            }
        });
    }

    // ===================== 8. 初始化入口 =====================
    function init() {
        // 等待頁面資料載入
        setTimeout(() => {
            renderMarketSentiment();
            renderSectorRotation();
            initScrollTop();
            initKeyboardShortcuts();
            initTableClick();
            initLiveFilter();

            // 綁定回測按鈕
            const runBtn = $('runBacktestBtn');
            if (runBtn) {
                runBtn.addEventListener('click', () => {
                    const rules = {
                        minBigHolderPct: parseFloat($('ruleMinBh')?.value) || 0,
                        maxChangePct: parseFloat($('ruleMaxChange')?.value) || 999,
                        minChangePct: parseFloat($('ruleMinChange')?.value) || -999,
                        bullOnly: $('ruleBullOnly')?.checked || false
                    };
                    const result = runBacktest(rules);
                    renderBacktestResults(result);
                });
            }

            // 綁定 CSV 按鈕
            const csvBtn = $('csvExportBtn');
            if (csvBtn) csvBtn.addEventListener('click', exportToCSV);
        }, 500);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
