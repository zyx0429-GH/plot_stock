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
        const rows = document.querySelectorAll('.data-table tbody tr.clickable, #bigHolderTable tbody tr');
        const seen = new Set();
        _allStocks = Array.from(rows).map(tr => {
            const tds = tr.querySelectorAll('td');
            if (tds.length < 4) return null;
            const code = tds[0]?.textContent?.trim() || '';
            const name = tds[1]?.textContent?.trim() || '';
            if (!code || !/^\d{4,}$/.test(code) || seen.has(code)) return null;
            seen.add(code);

            const close = parseFloat(tds[2]?.textContent?.replace(/,/g,'')) || 0;
            const changePct = parseFloat(tds[3]?.textContent) || 0;

            let bhPct = 0;
            if (tr.dataset.pct) {
                bhPct = parseFloat(tr.dataset.pct);
            } else {
                const text = tr.textContent;
                // 嘗試從「大戶%」欄位精確匹配
                const bhMatch = text.match(/大戶%?[\s:]*([\d.]+)%/);
                if (bhMatch) bhPct = parseFloat(bhMatch[1]);
            }

            const text = tr.textContent;
            let wowChange = 0;
            const allPct = text.match(/([+-]?[\d.]+)%/g);
            if (allPct && allPct.length >= 2) {
                for (const p of allPct) {
                    const v = parseFloat(p);
                    if (!isNaN(v) && Math.abs(v) < 15 && Math.abs(v - bhPct) > 0.1 && Math.abs(v - changePct) > 0.1) {
                        wowChange = v;
                        break;
                    }
                }
            }

            let trend = '';
            if (text.includes('多頭排列')) trend = '多頭排列';
            else if (text.includes('空頭排列')) trend = '空頭排列';

            let foreignBuy = text.includes('外資連買') || text.includes('✅');

            let rsi = 0;
            const rsiMatch = text.match(/RSI[:\s]*([\d.]+)/);
            if (rsiMatch) rsi = parseFloat(rsiMatch[1]);

            return {
                code, name, close, change_pct: changePct,
                big_holder_pct: bhPct, wow_change: wowChange,
                trend, foreign_buy: foreignBuy, rsi,
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
                <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:15px;text-align:center;">
                    <div style="color:var(--text-muted);font-size:12px;margin-bottom:5px;">選中檔數</div>
                    <div style="font-size:1.5em;font-weight:bold;color:#1e293b;">${result.selectedCount} / ${result.total}</div>
                </div>
                <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:15px;text-align:center;">
                    <div style="color:var(--text-muted);font-size:12px;margin-bottom:5px;">勝率</div>
                    <div style="font-size:1.5em;font-weight:bold;color:var(--accent);">${result.winRate}%</div>
                </div>
                <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:15px;text-align:center;">
                    <div style="color:var(--text-muted);font-size:12px;margin-bottom:5px;">平均報酬</div>
                    <div style="font-size:1.5em;font-weight:bold;color:${color};">${result.avgReturn}%</div>
                </div>
                <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:15px;text-align:center;">
                    <div style="color:var(--text-muted);font-size:12px;margin-bottom:5px;">最大單日虧損</div>
                    <div style="font-size:1.5em;font-weight:bold;color:#dc2626;">${result.maxLoss}%</div>
                </div>
                <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:15px;text-align:center;">
                    <div style="color:var(--text-muted);font-size:12px;margin-bottom:5px;">最大單日獲利</div>
                    <div style="font-size:1.5em;font-weight:bold;color:#16a34a;">${result.maxGain}%</div>
                </div>
            </div>
            ${result.selectedCount > 0 ? `
            <div style="margin-top:15px;">
                <div style="color:#f59e0b;font-weight:bold;margin-bottom:8px;">📋 選中股票</div>
                <div style="display:flex;flex-wrap:wrap;gap:6px;">
                    ${result.matched.map(s => `<span style="padding:3px 10px;border-radius:4px;background:var(--badge-bg);color:var(--text);font-size:12px;">${s.code} ${s.name} <span style="color:${s.change_pct>=0?'#16a34a':'#dc2626'}">${s.change_pct>=0?'+':''}${s.change_pct.toFixed(2)}%</span></span>`).join('')}
                </div>
            </div>` : ''}
        `;
    }

    // ===================== 2. 族群輪動 =====================
    const SECTOR_MAP = {
        // 最細分類放前面 (優先匹配)
        'IC設計': ['2357','2337','3006','4961','6257','3665','6669','8086'],
        '晶圓代工': ['6805'],
        '封測': ['3016','3045'],
        '記憶體': ['2408'],
        'AI伺服器/電子組裝': ['2317','2324','2356','2376','2382','3231','2404'],
        '石英元件': ['3042','8289','2484','6174','3221','8182'],
        '銅箔基板': ['2383','6213','6274','6672','8924'],
        '矽晶圓': ['3532','5483','1560','8028'],
        '電容/鋁質電容': ['2327','2492','6173','8042','8043','1815','3026','6207','8358','3236','3624','6155','6432','2375','3090'],
        '被動元件': ['2472','2478'],
        'PCB': ['2313','2355','2368','3037','8046'],
        '光電面板': ['2409','3481'],
        '通信網路': ['2345','5328','8096'],
        '金融保險': ['2881','2882','2850','2880','2883','2885','2886','2887','2890','2892'],
        '食品': ['1216','3005'],
        '塑化化工': ['1301','1319','2002','1605'],
        '鋼鐵金屬': ['2030','2031','2032','2033','2034','2023','2025'],
        '汽車': ['2634'],
        '生技醫療': ['6182'],
        'SiC功率': ['3707','8261'],
        '航太軍工': ['2634'],
        '衛星': ['6821'],
        'ETF': ['00981A'],
        // 較大分類放後面 (只放未歸類的股票)
        '半導體(其他)': ['2344'],
        '電子上游-IC-封測': ['2454','3661','3443','5274','4966','6415','6104','6462','6485','4919','3663','3675','2379','2330','2303','5347','6770','3711','2449','3264','6147','6239','6261','4967','3680','6187','6223','6510','6515'],
        '電子零組件': ['1590','2352','2428','2439','2449','2481','3017','3217','3356','3357','3376','3450','3498','3535','3537','5291','5425','5439','6127','6191','6271','6284','6727','8040','8091','8150','8210','8996'],
    };

    function getSector(code) {
        for (const [sector, codes] of Object.entries(SECTOR_MAP)) {
            if (codes.includes(code)) return sector;
        }
        return '其他';
    }

    // 更細部嚴謹的評分函數
    function calculateDetailedScore(stock) {
        let score = 50; // 基礎分
        const text = stock.element?.textContent || '';

        // ===== 技術面（最高 30 分） =====
        if (stock.trend === '多頭排列') {
            score += 18;
            // 額外加強：20MA > 60MA 的距離
            const ma20Match = text.match(/(\d+\.?\d*)\s+\d+\.?\d*\s+\d+\.?\d*/);
        } else if (stock.trend === '空頭排列') {
            score -= 12;
        }

        if (stock.rsi > 0) {
            if (stock.rsi >= 50 && stock.rsi < 70) score += 8;   // 健康動能區
            else if (stock.rsi >= 40 && stock.rsi < 50) score += 4;
            else if (stock.rsi >= 70 && stock.rsi < 80) score += 3; // 偏熱但仍可
            else if (stock.rsi >= 80) score -= 5;                  // 過熱警示
            else if (stock.rsi >= 30 && stock.rsi < 40) score += 2;
            else if (stock.rsi < 30) score += 5;                   // 超賣反彈潛力
        }

        // ===== 籌碼面（最高 25 分） =====
        const bh = stock.big_holder_pct;
        if (bh >= 80) score += 15;
        else if (bh >= 65) score += 12;
        else if (bh >= 50) score += 8;
        else if (bh >= 35) score += 4;
        else if (bh >= 20) score += 1;
        else if (bh > 0) score -= 2;  // 大戶極低，籌碼渙散

        const wow = stock.wow_change;
        if (Math.abs(wow) > 0.01) {
            if (wow >= 5) score += 10;       // 大幅增持
            else if (wow >= 3) score += 7;
            else if (wow >= 1) score += 4;
            else if (wow >= 0.3) score += 2;
            else if (wow <= -5) score -= 8;  // 大幅減持
            else if (wow <= -3) score -= 5;
            else if (wow <= -1) score -= 3;
            else if (wow < -0.3) score -= 1;
        }

        // ===== 法人面（最高 15 分） =====
        if (stock.foreign_buy) score += 8;
        if (text.includes('投信淨買')) {
            const trustMatch = text.match(/投信淨買[^\d]*(\d{1,3}(?:,\d{3})*)/);
            if (trustMatch) {
                const trustVal = parseInt(trustMatch[1].replace(/,/g,''));
                if (trustVal > 500000) score += 7;
                else if (trustVal > 100000) score += 4;
                else if (trustVal > 0) score += 2;
            }
        }
        if (text.includes('外資淨買')) {
            const foreignMatch = text.match(/外資淨買[^\d]*(\d{1,3}(?:,\d{3})*)/);
            if (foreignMatch) {
                const fVal = parseInt(foreignMatch[1].replace(/,/g,''));
                if (fVal > 2000000) score += 5;
                else if (fVal > 500000) score += 3;
            }
        }

        // ===== 漲跌穩健度（最高 10 分，可負分） =====
        const absChg = Math.abs(stock.change_pct);
        if (absChg >= 7) score -= 6;        // 過度波動，追高危險
        else if (absChg >= 5) score -= 3;
        else if (absChg >= 3) score += 2;   // 溫和強勢
        else if (absChg >= 1) score += 5;
        else if (absChg < 1) score += 3;    // 低波動，穩健

        // ===== 綜合加成/減成 =====
        // 雙強認證：多頭 + 外資連買 + 大戶增倉
        if (stock.trend === '多頭排列' && stock.foreign_buy && wow >= 1) score += 5;
        // 三弱警訊：空頭 + 外資賣 + 大戶減持
        if (stock.trend === '空頭排列' && !stock.foreign_buy && wow <= -1) score -= 5;

        return clamp(Math.round(score), 0, 100);
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
            .map(([name, data]) => ({ name, avgChange: data.count ? data.totalChange / data.count : 0, count: data.count, upCount: data.upCount, stocks: data.stocks }))
            .sort((a, b) => b.avgChange - a.avgChange);

        panel.innerHTML = sorted.map(s => {
            const color = s.avgChange >= 0 ? '#16a34a' : '#dc2626';
            const heat = s.avgChange > 2 ? '🔥🔥🔥' : s.avgChange > 0 ? '🔥' : '❄️';
            const topScore = s.stocks.length ? Math.max(...s.stocks.map(x => calculateDetailedScore(x))) : 0;
            const scoreLabel = topScore >= 80 ? 'A+' : topScore >= 65 ? 'A' : topScore >= 50 ? 'B' : topScore >= 35 ? 'C' : 'D';
            const scoreColor = topScore >= 80 ? '#16a34a' : topScore >= 65 ? '#16a34a' : topScore >= 50 ? '#f59e0b' : topScore >= 35 ? '#f97316' : '#dc2626';
            return `<div class="sector-card" data-sector="${s.name}" style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:15px;cursor:pointer;transition:all 0.2s;position:relative;"
                onmouseenter="this.style.borderColor='var(--accent)';this.style.transform='translateY(-2px)';this.style.boxShadow='0 4px 12px rgba(37,99,235,0.10)';"
                onmouseleave="this.style.borderColor='var(--border)';this.style.transform='';this.style.boxShadow='';">
                <div style="position:absolute;top:10px;right:12px;font-size:11px;font-weight:700;color:${scoreColor};background:${scoreColor}15;padding:2px 8px;border-radius:10px;border:1px solid ${scoreColor}30;">${scoreLabel}</div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;padding-right:40px;">
                    <span style="font-weight:bold;color:var(--text);font-size:14px;">${s.name}</span>
                    <span style="font-size:12px;">${heat}</span>
                </div>
                <div style="font-size:1.5em;font-weight:bold;color:${color};margin-bottom:5px;">${s.avgChange>=0?'+':''}${s.avgChange.toFixed(2)}%</div>
                <div style="font-size:12px;color:var(--text-muted);">
                    <div>股票數: ${s.count} 檔</div>
                    <div>上漲: ${s.upCount} 檔</div>
                </div>
                <div style="margin-top:8px;font-size:11px;color:var(--text-muted);text-align:center;padding-top:8px;border-top:1px solid var(--border);">
                    👆 點擊查看個股詳情
                </div>
            </div>`;
        }).join('');

        // 綁定點擊事件
        panel.querySelectorAll('.sector-card').forEach(card => {
            card.addEventListener('click', () => {
                const sector = card.dataset.sector;
                const data = sorted.find(x => x.name === sector);
                if (data) showSectorPopup(sector, data.stocks);
            });
        });
    }

    // 族群詳情彈窗
    function showSectorPopup(sectorName, stocks) {
        const modal = document.createElement('div');
        modal.id = 'sectorPopupModal';
        modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px;';

        const sortedStocks = [...stocks].sort((a, b) => calculateDetailedScore(b) - calculateDetailedScore(a));

        const rowsHtml = sortedStocks.map(s => {
            const score = calculateDetailedScore(s);
            const scoreColor = score >= 80 ? '#16a34a' : score >= 65 ? '#16a34a' : score >= 50 ? '#f59e0b' : score >= 35 ? '#f97316' : '#dc2626';
            const scoreBg = score >= 80 ? 'rgba(22,163,74,0.12)' : score >= 65 ? 'rgba(22,163,74,0.12)' : score >= 50 ? 'rgba(245,158,11,0.12)' : score >= 35 ? 'rgba(249,115,22,0.12)' : 'rgba(220,38,38,0.12)';
            const changeColor = s.change_pct >= 0 ? '#16a34a' : '#dc2626';
            const changeSign = s.change_pct >= 0 ? '+' : '';
            const wowColor = s.wow_change > 0 ? '#16a34a' : s.wow_change < 0 ? '#dc2626' : 'var(--text-muted)';
            const wowSign = s.wow_change > 0 ? '+' : '';

            return `
            <tr onclick="location.href='stock_${s.code}.html'" class="clickable" style="cursor:pointer;border-bottom:1px solid var(--border);transition:background 0.15s;" onmouseenter="this.style.background='rgba(37,99,235,0.04)'" onmouseleave="this.style.background=''">
                <td style="padding:10px 8px;"><strong style="color:var(--text);">${s.code}</strong></td>
                <td style="padding:10px 8px;color:var(--text);">${s.name}</td>
                <td style="padding:10px 8px;text-align:right;color:var(--text);">${s.close > 0 ? s.close.toFixed(2) : '—'}</td>
                <td style="padding:10px 8px;text-align:right;color:${changeColor};font-weight:600;">${s.change_pct !== 0 ? changeSign + s.change_pct.toFixed(2) + '%' : '—'}</td>
                <td style="padding:10px 8px;text-align:right;color:var(--warning);font-weight:600;">${s.big_holder_pct > 0 ? s.big_holder_pct.toFixed(2) + '%' : '—'}</td>
                <td style="padding:10px 8px;text-align:right;color:${wowColor};font-weight:600;">${s.wow_change !== 0 ? wowSign + s.wow_change.toFixed(2) + '%' : '—'}</td>
                <td style="padding:10px 8px;text-align:center;">${s.trend ? '<span style="color:' + (s.trend === '多頭排列' ? '#16a34a' : '#dc2626') + ';font-size:12px;">' + s.trend + '</span>' : '—'}</td>
                <td style="padding:10px 8px;text-align:center;font-size:14px;">${s.foreign_buy ? '<span style="color:#16a34a;">✅</span>' : '<span style="color:var(--text-muted);">❌</span>'}</td>
                <td style="padding:10px 8px;text-align:center;"><span style="display:inline-block;padding:3px 10px;border-radius:12px;background:${scoreBg};color:${scoreColor};font-weight:bold;font-size:13px;min-width:36px;text-align:center;">${score}</span></td>
            </tr>`;
        }).join('');

        // 計算族群統計
        const avgScore = sortedStocks.length ? (sortedStocks.reduce((sum, s) => sum + calculateDetailedScore(s), 0) / sortedStocks.length).toFixed(1) : 0;
        const bullCount = sortedStocks.filter(s => s.trend === '多頭排列').length;
        const hotStocks = sortedStocks.filter(s => calculateDetailedScore(s) >= 65).length;

        modal.innerHTML = `
            <div style="background:var(--bg);border:1px solid var(--border);border-radius:12px;max-width:950px;width:100%;max-height:90vh;overflow-y:auto;padding:25px;position:relative;">
                <button onclick="document.getElementById('sectorPopupModal').remove()" style="position:absolute;top:15px;right:15px;background:none;border:none;color:var(--text-muted);font-size:20px;cursor:pointer;z-index:10;">✕</button>
                <h2 style="color:var(--accent);margin:0 0 5px 0;font-size:1.4em;">🔄 ${sectorName}</h2>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:10px;margin:0 0 15px 0;">
                    <div style="background:var(--card-bg);border-radius:6px;padding:8px 12px;text-align:center;">
                        <div style="color:var(--text-muted);font-size:11px;">個股數</div>
                        <div style="color:var(--text);font-weight:bold;font-size:1.2em;">${stocks.length}</div>
                    </div>
                    <div style="background:var(--card-bg);border-radius:6px;padding:8px 12px;text-align:center;">
                        <div style="color:var(--text-muted);font-size:11px;">平均評分</div>
                        <div style="color:${avgScore >= 60 ? '#16a34a' : avgScore >= 45 ? '#f59e0b' : '#dc2626'};font-weight:bold;font-size:1.2em;">${avgScore}</div>
                    </div>
                    <div style="background:var(--card-bg);border-radius:6px;padding:8px 12px;text-align:center;">
                        <div style="color:var(--text-muted);font-size:11px;">多頭排列</div>
                        <div style="color:#16a34a;font-weight:bold;font-size:1.2em;">${bullCount} 檔</div>
                    </div>
                    <div style="background:var(--card-bg);border-radius:6px;padding:8px 12px;text-align:center;">
                        <div style="color:var(--text-muted);font-size:11px;">強勢股 (≥65)</div>
                        <div style="color:#f59e0b;font-weight:bold;font-size:1.2em;">${hotStocks} 檔</div>
                    </div>
                </div>
                <div style="overflow-x:auto;border:1px solid var(--border);border-radius:8px;">
                    <table style="width:100%;border-collapse:collapse;font-size:13px;">
                        <thead>
                            <tr style="border-bottom:1px solid var(--border);background:var(--card-bg);">
                                <th style="text-align:left;padding:10px 8px;color:var(--text-muted);font-weight:600;font-size:12px;">代號</th>
                                <th style="text-align:left;padding:10px 8px;color:var(--text-muted);font-weight:600;font-size:12px;">名稱</th>
                                <th style="text-align:right;padding:10px 8px;color:var(--text-muted);font-weight:600;font-size:12px;">收盤價</th>
                                <th style="text-align:right;padding:10px 8px;color:var(--text-muted);font-weight:600;font-size:12px;">漲跌%</th>
                                <th style="text-align:right;padding:10px 8px;color:var(--text-muted);font-weight:600;font-size:12px;">大戶%</th>
                                <th style="text-align:right;padding:10px 8px;color:var(--text-muted);font-weight:600;font-size:12px;">週增減</th>
                                <th style="text-align:center;padding:10px 8px;color:var(--text-muted);font-weight:600;font-size:12px;">趨勢</th>
                                <th style="text-align:center;padding:10px 8px;color:var(--text-muted);font-weight:600;font-size:12px;">外資連買</th>
                                <th style="text-align:center;padding:10px 8px;color:var(--text-muted);font-weight:600;font-size:12px;">評分</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rowsHtml}
                        </tbody>
                    </table>
                </div>
                <p style="color:var(--text-muted);font-size:11px;margin-top:12px;text-align:center;">⚠️ 評分綜合技術面、籌碼面、法人面、漲跌穩健度計算 · 點擊列可進入個股頁面</p>
            </div>
        `;
        document.body.appendChild(modal);

        const escHandler = e => { if (e.key === 'Escape') { modal.remove(); document.removeEventListener('keydown', escHandler); } };
        document.addEventListener('keydown', escHandler);
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
            else if (pct >= 45) { text = '➡️ 中性'; color = 'var(--text-muted)'; }
            else if (pct >= 30) { text = '📉 偏空'; color = '#f59e0b'; }
            else { text = '❄️ 極度悲觀'; color = 'var(--accent)'; }
            sentEl.textContent = `${text} (${pct.toFixed(1)}%)`;
            sentEl.style.color = color;
        }
    }

    // ===================== 3.5 各族群情緒 =====================
    function renderSectorSentiment() {
        const stocks = getAllStocks();
        const sectorMap = {
            'semiconductor': { name: '🔧 半導體', ids: ['2330','2317','2454','2303','2337','2344','2345','2357','2404','2428','2439','2449','2481','3006','3036','3231','3264','3443','3535','3653','3661','3665','3680','3711','4919','4961','4966','4967','5347','5439','6104','6155','6182','6187','6191','6207','6223','6239','6261','6271','6415','6510','6515','6669','6770','6805','8040','8042','8091','8150','8210','8289','8358','8996','1590','1727','2002','2301','2308','2313','2324','2327','2377','2382','2383','2408','2409','3016','3017','3037','3376','3450','3481','5274'] },
            'ai-server': { name: '🤖 AI伺服器', ids: ['2324','2356','2376','2382','3231','3661','6669'] },
            'passive-component': { name: '🔌 被動元件', ids: ['2327','2472','2478','2492','6173','8042','8043','1815','3026','2375','3090','6207','8358'] },
            'pcb': { name: '📟 PCB', ids: ['2313','2355','2368','2383','3037','6213','6274','8046'] },
            'memory': { name: '💾 記憶體', ids: ['2344','2408','3006','6770'] },
            'display': { name: '🖥️ 面板', ids: ['2409','3481'] },
            'financial': { name: '🏦 金融', ids: ['2881','2882','2850','2880','2883','2885','2886','2887','2890','2892'] },
        };

        const panel = $('sectorSentimentPanel');
        if (!panel) return;

        const html = [];
        for (const [key, cfg] of Object.entries(sectorMap)) {
            const sectorStocks = stocks.filter(s => cfg.ids.includes(s.code));
            if (sectorStocks.length === 0) continue;
            const up = sectorStocks.filter(s => s.change_pct > 0).length;
            const pct = (up / sectorStocks.length) * 100;
            let emoji, colorClass;
            if (pct >= 70) { emoji = '🔥'; colorClass = 'sentiment-up'; }
            else if (pct >= 55) { emoji = '📈'; colorClass = 'sentiment-up'; }
            else if (pct >= 45) { emoji = '➡️'; colorClass = 'sentiment-flat'; }
            else if (pct >= 30) { emoji = '📉'; colorClass = 'sentiment-down'; }
            else { emoji = '❄️'; colorClass = 'sentiment-down'; }
            html.push(`<div class="mini-card" style="text-align:center;padding:10px;"><div style="font-size:0.85rem;color:var(--text-muted);">${cfg.name}</div><div class="value ${colorClass}" style="font-size:1.1rem;">${emoji} ${pct.toFixed(0)}%</div><div style="font-size:0.7rem;color:var(--text-muted);">${up}/${sectorStocks.length} 上漲</div></div>`);
        }
        panel.innerHTML = html.join('') || '<div style="color:var(--text-muted);text-align:center;padding:10px;">暫無族群數據</div>';
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
            <div style="background:var(--bg);border:1px solid var(--border);border-radius:12px;max-width:600px;width:100%;max-height:90vh;overflow-y:auto;padding:25px;position:relative;">
                <button onclick="document.getElementById('stockPopupModal').remove()" style="position:absolute;top:15px;right:15px;background:none;border:none;color:var(--text-muted);font-size:20px;cursor:pointer;">✕</button>
                <h2 style="color:var(--accent);margin:0 0 15px 0;font-size:1.4em;">${code} ${name}</h2>
                <div style="display:flex;gap:15px;margin-bottom:15px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:120px;background:var(--card-bg);border-radius:8px;padding:12px;text-align:center;">
                        <div style="color:var(--text-muted);font-size:12px;">收盤價</div>
                        <div style="font-size:1.3em;font-weight:bold;color:var(--text);">${close}</div>
                    </div>
                    <div style="flex:1;min-width:120px;background:var(--card-bg);border-radius:8px;padding:12px;text-align:center;">
                        <div style="color:var(--text-muted);font-size:12px;">漲跌</div>
                        <div style="font-size:1.3em;font-weight:bold;color:${change.includes('-')?'#dc2626':'#16a34a'};">${change}</div>
                    </div>
                </div>
                <div style="margin-bottom:15px;">
                    <div style="color:#f59e0b;font-weight:bold;margin-bottom:8px;">📊 五維雷達圖</div>
                    <div style="max-width:350px;margin:0 auto;">
                        <canvas id="radarChartPopup"></canvas>
                    </div>
                </div>
                <div style="margin-bottom:15px;">
                    <div style="color:#f59e0b;font-weight:bold;margin-bottom:8px;">🎯 訊號標籤</div>
                    <div style="display:flex;flex-wrap:wrap;gap:5px;">
                        ${generateSignalTags(stockText)}
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:12px;color:var(--text-muted);">
                    <div style="background:var(--card-bg);border-radius:6px;padding:10px;">
                        <div style="color:var(--text);font-weight:bold;margin-bottom:4px;">💰 買點</div>
                        ${getBuySignalText(stockText)}
                    </div>
                    <div style="background:var(--card-bg);border-radius:6px;padding:10px;">
                        <div style="color:var(--text);font-weight:bold;margin-bottom:4px;">📉 停損</div>
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
                                ticks: { stepSize: 2, color: 'var(--text-muted)', backdropColor: 'transparent' },
                                grid: { color: 'var(--border)' },
                                pointLabels: { color: 'var(--chart-text)', font: { size: 12 } }
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
            else if (rsi < 30) tags.push({t:`❄️ RSI ${rsi}`,c:'var(--accent)',bg:'var(--accent-glow)'});
        }
        return tags.map(t => `<span style="padding:3px 8px;border-radius:4px;font-size:11px;color:${t.c};background:${t.bg};border:1px solid ${t.c}40;">${t.t}</span>`).join('');
    }

    function getBuySignalText(text) {
        if (text.includes('多頭排列') && (text.includes('外資連買') || text.includes('✅'))) return '<span style="color:#16a34a;">📈 雙強認證 — 可考慮分批佈局</span>';
        if (text.includes('多頭排列')) return '<span style="color:#16a34a;">📈 趨勢偏多 — 回測均線時關注</span>';
        if (text.includes('外資連買') || text.includes('✅')) return '<span style="color:#f59e0b;">💰 外資買超 — 觀察籌碼配合</span>';
        return '<span style="color:var(--text-muted);">➖ 暫無明確買點</span>';
    }

    function getStopLossText(text, closeStr) {
        const close = parseFloat(closeStr) || 0;
        if (!close) return '<span style="color:var(--text-muted);">無法計算</span>';
        // 簡化：固定 7% 停損 + 技術停損估計
        const fixedStop = (close * 0.93).toFixed(1);
        return `<span style="color:#dc2626;">固定 7%: ${fixedStop}</span><br><span style="color:var(--text-muted);font-size:11px;">建議同時觀察跌破 MA20</span>`;
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
        btn.style.cssText = 'position:fixed;bottom:30px;right:30px;width:50px;height:50px;background:var(--text-secondary);color:var(--text);border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:20px;z-index:1000;opacity:0;transition:opacity 0.3s;box-shadow:0 4px 12px rgba(0,0,0,0.3);';
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
                hint.style.cssText = 'text-align:center;color:var(--text-muted);font-size:13px;margin:8px 0;';
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
            renderSectorSentiment();
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
