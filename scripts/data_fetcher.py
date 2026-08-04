"""
台股資料抓取模組 — TWSE 官方 API + TPEX 櫃買中心 API 版本
免費、無額度限制
上市(TWSE) + 上櫃(TPEX) 雙源覆蓋
"""

import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
import json
import os
import re
import warnings

warnings.filterwarnings('ignore')

from config import DATA_DIR, WATCHLIST, ETF_00981A_HOLDINGS, ETF_00982A_HOLDINGS


class TWStockDataFetcher:
    """台股資料抓取器 — TWSE + TPEX + Yahoo Finance"""

    def __init__(self, api_token=None):
        self.api_token = api_token
        self.twse_base = "https://www.twse.com.tw"
        self.tpex_base = "https://www.tpex.org.tw"
        self.session = requests.Session()
        # 減少 SSL 驗證警告
        self.session.verify = False
        print(f"[INFO] DataFetcher initialized (TWSE + TPEX + Yahoo Finance mode)")

    def _twse_get(self, endpoint, params):
        """發送 TWSE API 請求"""
        url = f"{self.twse_base}/{endpoint}"
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data.get("stat") == "OK":
                return data
            else:
                print(f"[WARN] TWSE API {endpoint}: stat={data.get('stat')}")
                return {}
        except Exception as e:
            print(f"[ERROR] TWSE API {endpoint}: {e}")
            return {}

    def _tpex_get(self, endpoint, params):
        """發送 TPEX API 請求 (櫃買中心)"""
        url = f"{self.tpex_base}/{endpoint}"
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[ERROR] TPEX API {endpoint}: {e}")
            return {}

    @staticmethod
    def _roc_date(gregorian_date_str):
        """將西元日期 YYYYMMDD 轉為民國年格式 YYY/MM/DD"""
        if not gregorian_date_str or len(gregorian_date_str) != 8:
            return ""
        year = int(gregorian_date_str[:4]) - 1911
        month = gregorian_date_str[4:6]
        day = gregorian_date_str[6:8]
        return f"{year}/{month}/{day}"

    @staticmethod
    def _strip_html_tags(text):
        """去除 HTML 標籤，提取純文字"""
        if not text:
            return ""
        clean = re.sub(r'<[^>]+>', '', str(text))
        return clean.strip()

    @staticmethod
    def _parse_tpex_change(change_field):
        """解析 TPEX 漲跌欄位 (可能含 HTML) 提取數值"""
        clean = TWStockDataFetcher._strip_html_tags(change_field)
        if not clean:
            return 0.0
        # 去除 + - X 等非數字前綴後的數值
        m = re.search(r'[+\-]?[\d,]+\.?\d*', clean.replace(",", ""))
        if m:
            try:
                return float(m.group().replace(",", ""))
            except:
                return 0.0
        return 0.0

    @staticmethod
    def _merge_chip_monitoring(results):
        """已停用: fortune-fred 數據源已停更，大戶數據改由 Norway.twsthr.info 提供
        請使用 _merge_mndtas() 獲取最新大戶籌碼數據
        """
        print("[INFO] chip-monitoring (fortune-fred) is deprecated. Use Norway.twsthr.info instead.")
        return
        import glob
        # 本地開發路徑 (workspace/memory/)
        local_dirs = [
            os.path.join(os.path.dirname(__file__), "..", "..", "memory", "chip-monitoring", "weekly"),
            os.path.join(os.path.dirname(__file__), "..", "..", "memory", "chip_monitoring", "weekly"),
        ]
        # 線上路徑 (GitHub Actions 部署時用，與 scripts/ 同層的 data/)
        repo_dirs = [
            os.path.join(os.path.dirname(__file__), "..", "data", "chip-monitoring", "weekly"),
            os.path.join(os.path.dirname(__file__), "..", "data", "chip_monitoring", "weekly"),
        ]
        
        all_dirs = local_dirs + repo_dirs
        all_files = []
        for d in all_dirs:
            if os.path.isdir(d):
                all_files.extend(sorted(glob.glob(os.path.join(d, "*-full.json")), reverse=True))
        # 如果沒有 -full.json，回退到舊版格式
        for d in all_dirs:
            if os.path.isdir(d):
                all_files.extend(sorted(glob.glob(os.path.join(d, "[0-9]*-[0-9]*-[0-9]*.json")), reverse=True))
        
        weekly_files = []
        seen = set()
        for f in all_files:
            if f not in seen:
                seen.add(f)
                weekly_files.append(f)
        
        if not weekly_files:
            print("[INFO] No chip-monitoring weekly data found, skipping merge.")
            return
        
        latest_file = weekly_files[0]
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                chip_data = json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load chip monitoring data: {e}")
            return
        
        chip_lookup = {}
        is_full_format = "all_stocks" in chip_data
        
        if is_full_format:
            # 新版完整 200 檔格式
            for item in chip_data.get("all_stocks", []):
                ticker = str(item.get("ticker", "")).lstrip("0") or "0"
                if ticker:
                    # 解析 price_str 提取門檻
                    price_str = item.get("price_str", "")
                    threshold = "未知"
                    if "≥1000" in price_str:
                        threshold = "1000"
                    elif "≥400" in price_str:
                        threshold = "400"
                    elif "≥200" in price_str:
                        threshold = "200"
                    elif "≥100" in price_str:
                        threshold = "100"
                    
                    chip_lookup[ticker] = {
                        "big_holder_pct": item.get("bh_pct", 0.0),
                        "big_holder_change_pct": item.get("bh_wow", 0.0),
                        "threshold": threshold,
                        "date": chip_data.get("date", ""),
                    }
        else:
            # 舊版 top100 格式
            for category in ["top100_increase", "top100_decrease"]:
                for item in chip_data.get(category, []):
                    ticker = str(item.get("ticker", "")).lstrip("0") or "0"
                    if ticker:
                        bh_pct_str = item.get("bh_pct", "0%").replace("%", "")
                        bh_wow_str = item.get("bh_wow", "0%").replace("%", "")
                        try:
                            bh_pct = float(bh_pct_str)
                        except:
                            bh_pct = 0.0
                        try:
                            bh_wow = float(bh_wow_str)
                        except:
                            bh_wow = 0.0
                        chip_lookup[ticker] = {
                            "big_holder_pct": bh_pct,
                            "big_holder_change_pct": bh_wow,
                            "consecutive": item.get("consecutive", "—"),
                            "signals": item.get("signals", []),
                            "category": "increase" if category == "top100_increase" else "decrease",
                            "date": chip_data.get("date", ""),
                        }
        
        merged_count = 0
        for sid in results:
            if sid in chip_lookup:
                chip = chip_lookup[sid]
                results[sid]["holding"] = [{
                    "date": chip.get("date", ""),
                    "big_holder_pct": chip["big_holder_pct"],
                    "big_holder_change_pct": chip["big_holder_change_pct"],
                    "threshold": chip.get("threshold", "—"),
                }]
                merged_count += 1
        
        print(f"[INFO] Chip monitoring merged: {merged_count} stocks from {os.path.basename(latest_file)} (format: {'full' if is_full_format else 'legacy'})")

    def _yf_price(self, stock_id, days=60):
        """用 yfinance 抓股價歷史 — 嘗試 .TW 和 .TWO, auto_adjust=False 避免 adjusted close
        靜默處理退市股票錯誤，避免 stderr 輸出干擾 PowerShell"""
        import contextlib
        import io
        for suffix in [".TW", ".TWO"]:
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    ticker = yf.Ticker(f"{stock_id}{suffix}")
                    df = ticker.history(period=f"{days}d", auto_adjust=False)
                    if not df.empty:
                        return df
            except Exception:
                pass
        return pd.DataFrame()

    def _calc_technical(self, df):
        """計算技術指標 (MA20, MA60, RSI, MACD, KD, Bollinger Bands)"""
        if df.empty or len(df) < 20:
            return {}
        close = df["Close"]
        ma20 = close.rolling(20).mean().iloc[-1] if len(df) >= 20 else None
        ma60 = close.rolling(60).mean().iloc[-1] if len(df) >= 60 else None
        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain.iloc[-1] / avg_loss.iloc[-1] if avg_loss.iloc[-1] != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if avg_loss.iloc[-1] != 0 else 50
        # 乖離率 (BIAS)
        last_close = close.iloc[-1] if len(close) > 0 else None
        bias20 = None
        bias60 = None
        if last_close is not None and not pd.isna(last_close):
            if ma20 is not None and not pd.isna(ma20) and ma20 != 0:
                bias20 = (last_close - ma20) / ma20 * 100
            if ma60 is not None and not pd.isna(ma60) and ma60 != 0:
                bias60 = (last_close - ma60) / ma60 * 100

        # Trend
        if ma20 and ma60:
            trend = "短多頭" if ma20 > ma60 else "短空頭"
        else:
            trend = ""

        # MACD (12, 26, 9)
        macd_result = {}
        if len(df) >= 35:
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()
            hist = dif - dea
            latest_dif = dif.iloc[-1]
            latest_dea = dea.iloc[-1]
            latest_hist = hist.iloc[-1]
            macd_score = 50
            if latest_dif > 0:
                macd_score += 15
            else:
                macd_score -= 15
            if latest_hist > 0:
                macd_score += 15
            else:
                macd_score -= 15
            if len(hist) >= 2 and hist.iloc[-1] > hist.iloc[-2]:
                macd_score += 10
            else:
                macd_score -= 10
            macd_score = max(0, min(100, macd_score))
            
            if latest_dif > latest_dea and latest_dif > 0:
                macd_signal = "多頭強勢"
            elif latest_dif > latest_dea and latest_dif < 0:
                macd_signal = "多頭轉強"
            elif latest_dif < latest_dea and latest_dif > 0:
                macd_signal = "多頭轉弱"
            else:
                macd_signal = "空頭弱勢"
            
            macd_result = {
                "dif": round(latest_dif, 4) if not pd.isna(latest_dif) else "-",
                "dea": round(latest_dea, 4) if not pd.isna(latest_dea) else "-",
                "hist": round(latest_hist, 4) if not pd.isna(latest_hist) else "-",
                "score": macd_score,
                "signal": macd_signal,
            }
        else:
            macd_result = {"dif": "-", "dea": "-", "hist": "-", "score": "-", "signal": "資料不足"}

        # KD (9, 3, 3)
        kd_result = {}
        if len(df) >= 9:
            low_min = df["Low"].rolling(window=9, min_periods=1).min()
            high_max = df["High"].rolling(window=9, min_periods=1).max()
            rsv = (close - low_min) / (high_max - low_min) * 100
            rsv = rsv.fillna(50)
            
            k = [50]
            for i in range(1, len(df)):
                k.append((2/3) * k[i-1] + (1/3) * rsv.iloc[i])
            d = [50]
            for i in range(1, len(df)):
                d.append((2/3) * d[i-1] + (1/3) * k[i])
            
            latest_k = k[-1]
            latest_d = d[-1]
            
            if latest_k > 80 and latest_d > 80:
                kd_signal = "超買區 — 注意回檔"
            elif latest_k < 20 and latest_d < 20:
                kd_signal = "超賣區 — 可能反彈"
            elif latest_k > latest_d and latest_k > latest_d + 5:
                kd_signal = "黃金交叉 — 偏多"
            elif latest_k < latest_d and latest_d > latest_k + 5:
                kd_signal = "死亡交叉 — 偏空"
            else:
                kd_signal = "盤整 — 方向不明"
            
            kd_result = {
                "k": round(latest_k, 2),
                "d": round(latest_d, 2),
                "signal": kd_signal,
            }
        else:
            kd_result = {"k": "-", "d": "-", "signal": "資料不足"}

        # Bollinger Bands (20, 2)
        bb_result = {}
        if len(df) >= 20:
            bb_middle = close.rolling(20).mean()
            bb_std = close.rolling(20).std()
            bb_upper = bb_middle + bb_std * 2
            bb_lower = bb_middle - bb_std * 2
            bb_bw = ((bb_upper - bb_lower) / bb_middle) * 100
            bb_pct = (close - bb_lower) / (bb_upper - bb_lower)
            
            latest_upper = bb_upper.iloc[-1]
            latest_lower = bb_lower.iloc[-1]
            latest_middle = bb_middle.iloc[-1]
            latest_pct = bb_pct.iloc[-1]
            
            if last_close >= latest_upper:
                pos = "upper_band"
                pos_text = "觸及上軌"
            elif last_close <= latest_lower:
                pos = "lower_band"
                pos_text = "觸及下軌"
            elif last_close > latest_middle:
                pos = "upper_half"
                pos_text = "上軌與中軌之間"
            else:
                pos = "lower_half"
                pos_text = "下軌與中軌之間"
            
            bb_result = {
                "upper": round(latest_upper, 2) if not pd.isna(latest_upper) else "-",
                "middle": round(latest_middle, 2) if not pd.isna(latest_middle) else "-",
                "lower": round(latest_lower, 2) if not pd.isna(latest_lower) else "-",
                "position": pos,
                "position_text": pos_text,
                "pct_b": round(latest_pct, 4) if not pd.isna(latest_pct) else "-",
            }
        else:
            bb_result = {"upper": "-", "middle": "-", "lower": "-", "position": "-", "position_text": "資料不足", "pct_b": "-"}

        return {
            "ma20": round(ma20, 2) if ma20 else "-",
            "ma60": round(ma60, 2) if ma60 else "-",
            "rsi": round(rsi, 1) if rsi else "-",
            "trend": trend,
            "bias20": round(bias20, 2) if bias20 is not None and not pd.isna(bias20) else "-",
            "bias60": round(bias60, 2) if bias60 is not None and not pd.isna(bias60) else "-",
            "macd": macd_result,
            "kd": kd_result,
            "bollinger": bb_result,
        }

    def _fetch_tpex_quotes(self, today_str, yesterday_str):
        """抓取 TPEX 上櫃每日收盤行情"""
        roc_today = self._roc_date(today_str)
        roc_yesterday = self._roc_date(yesterday_str)
        price_map = {}

        for d in [roc_today, roc_yesterday]:
            if not d:
                continue
            print(f"[INFO] Fetching TPEX quotes for {d}...")
            data = self._tpex_get("web/stock/aftertrading/daily_close_quotes/stk_quote_result.php", {
                "l": "zh-tw", "d": d, "_": "0"
            })
            tables = data.get("tables", [])
            if tables and tables[0].get("data"):
                table = tables[0]
                rows = table.get("data", [])
                print(f"[INFO] TPEX quotes: {len(rows)} stocks for {d}")
                for row in rows:
                    if len(row) < 11:
                        continue
                    sid = str(row[0]).lstrip("0") or "0"
                    try:
                        close_raw = str(row[2]).replace(",", "")
                        close_val = float(close_raw) if close_raw != "--" else 0.0
                        change_raw = str(row[3]) if row[3] is not None else ""
                        change_val = self._parse_tpex_change(change_raw)
                        open_raw = str(row[4]).replace(",", "")
                        high_raw = str(row[5]).replace(",", "")
                        low_raw = str(row[6]).replace(",", "")
                        vol_raw = str(row[8]).replace(",", "")

                        price_map[sid] = {
                            "stock_name": str(row[1]).strip(),
                            "close": close_val,
                            "change": change_val,
                            "open": float(open_raw) if open_raw != "--" else 0.0,
                            "high": float(high_raw) if high_raw != "--" else 0.0,
                            "low": float(low_raw) if low_raw != "--" else 0.0,
                            "volume": int(vol_raw) if vol_raw else 0,
                        }
                    except Exception:
                        pass
                break  # 有資料就跳出
            else:
                print(f"[WARN] No TPEX quotes for {d}")
        return price_map

    def _fetch_tpex_institutional(self, today_str, yesterday_str):
        """抓取 TPEX 上櫃三大法人買賣超 (外資 + 投信)"""
        roc_today = self._roc_date(today_str)
        roc_yesterday = self._roc_date(yesterday_str)
        foreign_map = {}
        trust_map = {}

        for d in [roc_today, roc_yesterday]:
            if not d:
                continue
            print(f"[INFO] Fetching TPEX institutional for {d}...")
            data = self._tpex_get("web/stock/3insti/daily_trade/3itrade_hedge_result.php", {
                "l": "zh-tw", "se": "AL", "t": "D", "d": d, "_": "0"
            })
            tables = data.get("tables", [])
            if tables and tables[0].get("data"):
                rows = tables[0].get("data", [])
                print(f"[INFO] TPEX institutional: {len(rows)} stocks for {d}")
                for row in rows:
                    if len(row) < 11:
                        continue
                    sid = str(row[0]).lstrip("0") or "0"
                    try:
                        # 外陸資(不含外資自營商) net = idx 4, 外資自營商 net = idx 7
                        f_net1 = int(str(row[4]).replace(",", "")) if len(row) > 4 else 0
                        f_net2 = int(str(row[7]).replace(",", "")) if len(row) > 7 else 0
                        f_buy1 = int(str(row[2]).replace(",", "")) if len(row) > 2 else 0
                        f_sell1 = int(str(row[3]).replace(",", "")) if len(row) > 3 else 0
                        f_buy2 = int(str(row[5]).replace(",", "")) if len(row) > 5 else 0
                        f_sell2 = int(str(row[6]).replace(",", "")) if len(row) > 6 else 0
                        foreign_net = f_net1 + f_net2
                        foreign_buy = f_buy1 + f_buy2
                        foreign_sell = f_sell1 + f_sell2

                        # 投信 net = idx 10, buy = idx 8, sell = idx 9
                        t_buy = int(str(row[8]).replace(",", "")) if len(row) > 8 else 0
                        t_sell = int(str(row[9]).replace(",", "")) if len(row) > 9 else 0
                        t_net = int(str(row[10]).replace(",", "")) if len(row) > 10 else 0

                        foreign_map[sid] = {"buy": foreign_buy, "sell": foreign_sell, "net": foreign_net}
                        trust_map[sid] = {"buy": t_buy, "sell": t_sell, "net": t_net}
                    except Exception:
                        pass
                break
            else:
                print(f"[WARN] No TPEX institutional for {d}")
        return foreign_map, trust_map

    def _fetch_tpex_margin(self, today_str, yesterday_str):
        """抓取 TPEX 上櫃融資融券餘額"""
        roc_today = self._roc_date(today_str)
        roc_yesterday = self._roc_date(yesterday_str)
        margin_map = {}

        for d in [roc_today, roc_yesterday]:
            if not d:
                continue
            print(f"[INFO] Fetching TPEX margin for {d}...")
            data = self._tpex_get("web/stock/margin_trading/margin_balance/margin_bal_result.php", {
                "l": "zh-tw", "o": "json", "d": d, "_": "0"
            })
            tables = data.get("tables", [])
            if tables and tables[0].get("data"):
                table = tables[0]
                rows = table.get("data", [])
                print(f"[INFO] TPEX margin: {len(rows)} stocks for {d}")
                for row in rows:
                    if len(row) < 19:
                        continue
                    sid = str(row[0]).lstrip("0") or "0"
                    try:
                        prev_margin = int(str(row[2]).replace(",", ""))  # 前資餘額
                        margin_balance = int(str(row[6]).replace(",", ""))  # 資餘額
                        prev_short = int(str(row[10]).replace(",", ""))  # 前券餘額
                        short_balance = int(str(row[14]).replace(",", ""))  # 券餘額
                        margin_usage_str = str(row[8]).replace(",", "") if row[8] else "0"
                        margin_usage = float(margin_usage_str) if margin_usage_str else 0
                        ratio = short_balance / margin_balance if margin_balance > 0 else 0
                        margin_map[sid] = {
                            "margin_balance": margin_balance,
                            "short_balance": short_balance,
                            "margin_prev": prev_margin,
                            "short_prev": prev_short,
                            "margin_change": margin_balance - prev_margin,
                            "short_change": short_balance - prev_short,
                            "margin_usage_pct": round(margin_usage, 2),
                            "ratio": round(ratio, 4),
                        }
                    except Exception:
                        pass
                break  # 有資料就跳出
            else:
                print(f"[WARN] No TPEX margin for {d}")
        return margin_map

    @staticmethod
    def _get_last_trading_day(date_str):
        """回退到最近交易日（週六回退到週五，週日回退到週五）"""
        dt = datetime.strptime(date_str, "%Y%m%d")
        weekday = dt.weekday()  # 0=週一, 5=週六, 6=週日
        if weekday == 5:  # 週六
            dt = dt - timedelta(days=1)
        elif weekday == 6:  # 週日
            dt = dt - timedelta(days=2)
        return dt.strftime("%Y%m%d")

    def fetch_all_data(self, stock_list):
        """批次抓取所有個股資料 — TWSE API + TPEX API + Yahoo Finance"""
        results = {}
        today_str_raw = datetime.now().strftime("%Y%m%d")
        today_str = self._get_last_trading_day(today_str_raw)
        yesterday = (datetime.strptime(today_str, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
        yesterday = self._get_last_trading_day(yesterday)
        print(f"[INFO] Fetching data for {len(stock_list)} stocks...")
        print(f"[INFO] Today (raw): {today_str_raw} -> adjusted to trading day: {today_str}")
        print(f"[INFO] Yesterday adjusted to trading day: {yesterday}")

        # === Step 1: 抓取上市每日成交資料 (STOCK_DAY_ALL) ===
        print("[INFO] Fetching TWSE STOCK_DAY_ALL...")
        day_all = self._twse_get("exchangeReport/STOCK_DAY_ALL", {"response": "json", "date": today_str})
        if not day_all.get("data"):
            print("[WARN] No data for today, trying yesterday...")
            day_all = self._twse_get("exchangeReport/STOCK_DAY_ALL", {"response": "json", "date": yesterday})
        price_map = {}
        if day_all.get("data"):
            for row in day_all["data"]:
                sid = row[0]
                try:
                    price_map[sid.lstrip("0") or "0"] = {
                        "stock_name": row[1].strip(),
                        "volume": int(row[2].replace(",", "")),
                        "open": float(row[4].replace(",", "")) if row[4] != "--" else 0,
                        "high": float(row[5].replace(",", "")) if row[5] != "--" else 0,
                        "low": float(row[6].replace(",", "")) if row[6] != "--" else 0,
                        "close": float(row[7].replace(",", "")) if row[7] != "--" else 0,
                        "change": float(row[8].replace(",", "").replace("+", "").replace("X", "0")) if row[8] != "--" else 0,
                        "trades": int(row[9].replace(",", "")),
                    }
                except Exception:
                    pass
        print(f"[INFO] TWSE STOCK_DAY_ALL: {len(price_map)} stocks")

        # === Step 1b: 抓取上櫃每日成交資料 (TPEX) ===
        tpex_price_map = self._fetch_tpex_quotes(today_str, yesterday)
        print(f"[INFO] TPEX quotes: {len(tpex_price_map)} stocks")
        # 合併：以上市為主，上櫃補缺
        for sid, pdata in tpex_price_map.items():
            if sid not in price_map:
                price_map[sid] = pdata

        # === Step 2: 抓取上市三大法人買賣超 (T86) ===
        print("[INFO] Fetching TWSE T86 (institutional investors)...")
        t86 = self._twse_get("fund/T86", {"response": "json", "date": today_str, "selectType": "ALLBUT0999"})
        if not t86.get("data"):
            t86 = self._twse_get("fund/T86", {"response": "json", "date": yesterday, "selectType": "ALLBUT0999"})
        foreign_map = {}
        trust_map = {}
        if t86.get("data") and t86.get("fields"):
            fidx = {name: i for i, name in enumerate(t86["fields"])}
            for row in t86["data"]:
                sid = row[fidx.get("證券代號", 0)]
                try:
                    f_buy = int(row[fidx.get("外資買進股數", 2)].replace(",", ""))
                    f_sell = int(row[fidx.get("外資賣出股數", 3)].replace(",", ""))
                    f_net = int(row[fidx.get("外資買賣超股數", 4)].replace(",", ""))
                    foreign_map[sid.lstrip("0") or "0"] = {"buy": f_buy, "sell": f_sell, "net": f_net}
                    t_buy = int(row[fidx.get("投信買進股數", 5)].replace(",", ""))
                    t_sell = int(row[fidx.get("投信賣出股數", 6)].replace(",", ""))
                    t_net = int(row[fidx.get("投信買賣超股數", 7)].replace(",", ""))
                    trust_map[sid.lstrip("0") or "0"] = {"buy": t_buy, "sell": t_sell, "net": t_net}
                except Exception:
                    pass
        print(f"[INFO] TWSE T86: 外資={len(foreign_map)} stocks, 投信={len(trust_map)} stocks")

        # === Step 2b: 抓取上櫃三大法人買賣超 (TPEX) ===
        tpex_foreign_map, tpex_trust_map = self._fetch_tpex_institutional(today_str, yesterday)
        print(f"[INFO] TPEX T86: 外資={len(tpex_foreign_map)} stocks, 投信={len(tpex_trust_map)} stocks")
        # 合併：以上市為主，上櫃補缺
        for sid, fdata in tpex_foreign_map.items():
            if sid not in foreign_map:
                foreign_map[sid] = fdata
        for sid, tdata in tpex_trust_map.items():
            if sid not in trust_map:
                trust_map[sid] = tdata

        # === Step 3: 抓取上市融資融券 (MI_MARGN) ===
        print("[INFO] Fetching TWSE MI_MARGN (margin trading)...")
        margn = self._twse_get("exchangeReport/MI_MARGN", {"response": "json", "date": today_str, "selectType": "ALL"})
        if not margn.get("tables"):
            margn = self._twse_get("exchangeReport/MI_MARGN", {"response": "json", "date": yesterday, "selectType": "ALL"})
        margin_map = {}
        if margn.get("tables") and len(margn["tables"]) >= 2:
            table1 = margn["tables"][1]
            if table1.get("data") and table1.get("fields"):
                fidx = {name: i for i, name in enumerate(table1["fields"])}
                for row in table1["data"]:
                    sid = row[fidx.get("證券代號", 0)]
                    try:
                        margin_balance = int(row[fidx.get("融資今日餘額", 6)].replace(",", ""))
                        short_balance = int(row[fidx.get("融券今日餘額", 12)].replace(",", ""))
                        prev_margin = int(row[fidx.get("融資昨日餘額", 5)].replace(",", ""))
                        prev_short = int(row[fidx.get("融券昨日餘額", 11)].replace(",", ""))
                        ratio = short_balance / margin_balance if margin_balance > 0 else 0
                        margin_map[sid.lstrip("0") or "0"] = {
                            "margin_balance": margin_balance,
                            "short_balance": short_balance,
                            "margin_prev": prev_margin,
                            "short_prev": prev_short,
                            "margin_change": margin_balance - prev_margin,
                            "short_change": short_balance - prev_short,
                            "margin_usage_pct": None,
                            "ratio": round(ratio, 4),
                        }
                    except Exception:
                        pass
        print(f"[INFO] TWSE MI_MARGN: {len(margin_map)} stocks")

        # === Step 3c: 抓取上櫃融資融券 (TPEX) ===
        tpex_margin_map = self._fetch_tpex_margin(today_str, yesterday)
        print(f"[INFO] TPEX margin: {len(tpex_margin_map)} stocks")
        # 合併：以上市為主，上櫃補缺
        for sid, mdata in tpex_margin_map.items():
            if sid not in margin_map:
                margin_map[sid] = mdata

        # === Step 4: 用 yfinance 抓歷史價格算技術指標 ===
        print("[INFO] Fetching yfinance history for technical indicators...")
        for i, stock_id in enumerate(stock_list, 1):
            print(f"[{i}/{len(stock_list)}] {stock_id}...", end=" ")
            try:
                price_info = price_map.get(stock_id, {})
                yf_df = self._yf_price(stock_id, days=60)
                tech = self._calc_technical(yf_df)

                close = price_info.get("close", 0)
                prev_close = close - price_info.get("change", 0)
                change_pct = (price_info.get("change", 0) / prev_close * 100) if prev_close != 0 else 0

                info = {
                    "stock_id": stock_id,
                    "stock_name": price_info.get("stock_name", ""),
                    "close": close,
                    "open": price_info.get("open", 0),
                    "high": price_info.get("high", 0),
                    "low": price_info.get("low", 0),
                    "volume": price_info.get("volume", 0),
                    "change": price_info.get("change", 0),
                    "change_pct": change_pct,
                }

                foreign_data = foreign_map.get(stock_id, {})
                foreign_list = []
                if foreign_data:
                    foreign_list = [{
                        "date": today_str,
                        "buy": foreign_data["buy"],
                        "sell": foreign_data["sell"],
                        "net": foreign_data["net"],
                    }]
                info["foreign_net"] = foreign_data.get("net", 0)

                trust_data = trust_map.get(stock_id, {})
                trust_list = []
                if trust_data:
                    trust_list = [{
                        "date": today_str,
                        "buy": trust_data["buy"],
                        "sell": trust_data["sell"],
                        "net": trust_data["net"],
                    }]
                info["trust_net"] = trust_data.get("net", 0)

                margin_data = margin_map.get(stock_id, {})
                margin_list = []
                if margin_data:
                    margin_list = [{
                        "date": today_str,
                        "margin_balance": margin_data["margin_balance"],
                        "short_balance": margin_data["short_balance"],
                        "margin_prev": margin_data.get("margin_prev", 0),
                        "short_prev": margin_data.get("short_prev", 0),
                        "margin_change": margin_data.get("margin_change", 0),
                        "short_change": margin_data.get("short_change", 0),
                        "margin_usage_pct": margin_data.get("margin_usage_pct"),
                        "margin_short_ratio": margin_data["ratio"],
                    }]

                # 價格歷史（供 stock_screener 計算 MA/RSI）
                price_dict = {}
                if not yf_df.empty:
                    price_dict = {
                        "Close": [round(float(x), 2) for x in yf_df["Close"].tolist()],
                        "High": [round(float(x), 2) for x in yf_df["High"].tolist()],
                        "Low": [round(float(x), 2) for x in yf_df["Low"].tolist()],
                        "Open": [round(float(x), 2) for x in yf_df["Open"].tolist()],
                        "Volume": [int(x) for x in yf_df["Volume"].tolist()],
                    }
                    # 也加入預計算技術指標供 generate_html 使用
                    price_dict.update(tech)
                else:
                    price_dict = tech  # 包含 ma20/ma60/rsi/trend

                results[stock_id] = {
                    "info": info,
                    "foreign": foreign_list,
                    "trust": trust_list,
                    "margin": margin_list,
                    "holding": [],  # 大戶持股暫時不抓
                    "price": price_dict,
                }
                print("[OK]")
            except Exception as e:
                print(f"[ERR] {e}")

            time.sleep(0.3)  # 避免 yfinance rate limit

        # === Step 5: Merge 大戶週報資料 (如果有) ===
        self._merge_chip_monitoring(results)

        # === Step 6: Merge 集保人數分級統計 (MNDTAS) ===
        self._merge_mndtas(results)

        # === Step 7: 累積歷史外資/投信/融資數據 (保留最近30天) ===
        results = self._accumulate_history(results, today_str)

        # === Save ===
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, "raw_data.json"), "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Data saved: {len(results)} stocks")
        return results

    def _accumulate_history(self, results, today_str):
        """將當日數據與已有歷史數據合併，保留最近30天"""
        raw_path = os.path.join(DATA_DIR, "raw_data.json")
        if not os.path.exists(raw_path):
            print("[INFO] No existing raw_data.json, starting fresh history")
            return results

        try:
            with open(raw_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load existing raw_data.json: {e}")
            return results

        MAX_HISTORY_DAYS = 30

        for stock_id, new_record in results.items():
            old_record = old_data.get(stock_id, {})

            # 累積外資數據
            old_foreign = old_record.get("foreign", [])
            new_foreign = new_record.get("foreign", [])
            if new_foreign:
                # 去除重複日期，保留新數據
                date_set = {f["date"] for f in new_foreign}
                merged = [f for f in old_foreign if f.get("date") not in date_set]
                merged.extend(new_foreign)
                merged.sort(key=lambda x: x.get("date", ""))
                # 只保留最近30天
                new_record["foreign"] = merged[-MAX_HISTORY_DAYS:]
            elif old_foreign:
                new_record["foreign"] = old_foreign[-MAX_HISTORY_DAYS:]

            # 累積投信數據
            old_trust = old_record.get("trust", [])
            new_trust = new_record.get("trust", [])
            if new_trust:
                date_set = {t["date"] for t in new_trust}
                merged = [t for t in old_trust if t.get("date") not in date_set]
                merged.extend(new_trust)
                merged.sort(key=lambda x: x.get("date", ""))
                new_record["trust"] = merged[-MAX_HISTORY_DAYS:]
            elif old_trust:
                new_record["trust"] = old_trust[-MAX_HISTORY_DAYS:]

            # 累積融資數據
            old_margin = old_record.get("margin", [])
            new_margin = new_record.get("margin", [])
            if new_margin:
                date_set = {m["date"] for m in new_margin}
                merged = [m for m in old_margin if m.get("date") not in date_set]
                merged.extend(new_margin)
                merged.sort(key=lambda x: x.get("date", ""))
                new_record["margin"] = merged[-MAX_HISTORY_DAYS:]
            elif old_margin:
                new_record["margin"] = old_margin[-MAX_HISTORY_DAYS:]

        print(f"[INFO] History accumulated: up to {MAX_HISTORY_DAYS} days for foreign/trust/margin")
        return results

    def _merge_mndtas(self, results):
        """用 Norway.twsthr.info 集保籌碼數據替代 TWSE MNDTAS
        數據來源: data/norway/all_stocks_weekly.json (由 norway_fetcher.py 生成)
        """
        print("[INFO] Loading Norway.twsthr.info chip data (MNDTAS substitute)...")
        
        norway_files = [
            "data/norway/all_stocks_weekly.json",
            "data/norway/taiwan50_weekly.json",
        ]
        
        chip_lookup = {}
        for nf in norway_files:
            if not os.path.exists(nf):
                continue
            try:
                with open(nf, "r", encoding="utf-8") as f:
                    records = json.load(f)
                for r in records:
                    code = r.get("stock_code", "")
                    if code:
                        chip_lookup[code] = r
                print(f"[INFO] Loaded {len(records)} records from {nf}")
            except Exception as e:
                print(f"[WARN] Failed to load {nf}: {e}")
        
        print(f"[INFO] Total chip lookup entries: {len(chip_lookup)}")
        
        # Guard: if chip data is insufficient, preserve existing shareholder data
        if len(chip_lookup) < 1000:
            print(f"[WARN] Norway chip data insufficient ({len(chip_lookup)} records). Preserving existing shareholder data from raw_data.json...")
            existing_raw_path = os.path.join(DATA_DIR, "raw_data.json")
            if os.path.exists(existing_raw_path):
                try:
                    with open(existing_raw_path, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                    preserved = 0
                    for sid in results:
                        if sid in existing_data and existing_data[sid].get("shareholder"):
                            results[sid]["shareholder"] = existing_data[sid]["shareholder"]
                            preserved += 1
                    print(f"[INFO] Preserved shareholder data for {preserved} stocks from existing raw_data.json")
                    # Save and return early
                    os.makedirs(DATA_DIR, exist_ok=True)
                    with open(os.path.join(DATA_DIR, "raw_data.json"), "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                    print(f"[INFO] Data saved: {len(results)} stocks")
                    return results
                except Exception as e:
                    print(f"[WARN] Failed to preserve existing shareholder data: {e}")
            else:
                print("[WARN] No existing raw_data.json found to preserve shareholder data")
        
        merged = 0
        for sid in results:
            if sid in chip_lookup:
                chip = chip_lookup[sid]
                weekly = chip.get("weekly_changes", {})
                # 取最新週增減 (最後一個日期)
                latest_change = list(weekly.values())[-1] if weekly else None
                # 計算近4週趨勢
                recent_values = list(weekly.values())[-4:] if weekly else []
                trend_direction = "up" if len(recent_values) >= 2 and recent_values[-1] > recent_values[0] else "down" if len(recent_values) >= 2 else "flat"
                
                results[sid]["shareholder"] = [{
                    "date": chip.get("latest_change", ""),
                    "total_count": 0,  # Norway 無總人數
                    "big_holder_count": 0,
                    "concentration": chip.get("last_week_hold_pct", 0),
                    "threshold_shares": chip.get("threshold_shares", 0),
                    "threshold_code": chip.get("threshold_code", 0),
                    "category": chip.get("category", ""),
                    "weekly_changes": weekly,
                    "latest_change": latest_change,
                    "total_change": chip.get("total_change", 0),
                    "trend_direction": trend_direction,
                    "is_taiwan50": chip.get("is_taiwan50", False),
                }]
                merged += 1
        
        print(f"[INFO] Norway chip data merged: {merged} stocks")
        
        # Guard: if merged too few, data might be corrupted
        if merged < 100 and len(results) > 150:
            print(f"[WARN] Only {merged} stocks merged with chip data (expected >150). Data might be corrupted.")
            existing_raw_path = os.path.join(DATA_DIR, "raw_data.json")
            if os.path.exists(existing_raw_path):
                try:
                    with open(existing_raw_path, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                    preserved = 0
                    for sid in results:
                        if sid in existing_data and existing_data[sid].get("shareholder"):
                            results[sid]["shareholder"] = existing_data[sid]["shareholder"]
                            preserved += 1
                    print(f"[INFO] Emergency fallback: preserved shareholder data for {preserved} stocks from existing raw_data.json")
                except Exception as e:
                    print(f"[WARN] Failed to preserve existing data: {e}")
        
        # === Save ===
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, "raw_data.json"), "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Data saved: {len(results)} stocks")
        return results

    def fetch_etf_data(self, etf_code="00981A", holdings=None):
        """抓取 ETF 成分股資料"""
        if holdings is None:
            holdings = ETF_00981A_HOLDINGS
        # 兼容 list 和 dict 两种格式
        if isinstance(holdings, list):
            holdings = {sid: 0.0 for sid in holdings}
        results = {}
        for stock_id, weight in holdings.items():
            df = self._yf_price(stock_id, days=30)
            if not df.empty:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                results[stock_id] = {
                    "weight": weight,
                    "close": round(latest["Close"], 2),
                    "change_pct": round((latest["Close"] - prev["Close"]) / prev["Close"] * 100, 2) if prev["Close"] != 0 else 0,
                }
            time.sleep(0.2)
        with open(os.path.join(DATA_DIR, "etf_data.json"), "w", encoding="utf-8") as f:
            json.dump({"etf_code": etf_code, "holdings": results}, f, ensure_ascii=False, indent=2)
        return results

    def _price_to_dict(self, df):
        """相容舊接口"""
        if df.empty:
            return {}
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        change_pct = (latest["Close"] - prev["Close"]) / prev["Close"] * 100 if prev["Close"] != 0 else 0
        return {
            "close": round(latest["Close"], 2),
            "change_pct": round(change_pct, 2),
            "volume": int(latest["Volume"]),
        }


def fetch_all():
    """模組級入口：供 main.py 調用"""
    fetcher = TWStockDataFetcher()
    all_stocks = list(WATCHLIST) + [
        "2330", "2317", "2454", "2303", "2881", "2882", "1216", "1301", "3008", "0050", "0056",
        "3006", "2345", "2376", "2301", "2327", "2313", "2409", "3481", "3037", "2357",
        "3661", "2382", "6415", "2344", "2356", "2377", "2383", "3665",
        "4967", "6213", "8150", "8046", "8996", "5439", "6805", "6770", "6669",
        "4961", "6271", "3443", "3376", "2428", "2439", "2449",
        "2492", "2481", "4919", "3711", "6191",
        "1590", "1319", "00981A", "1605", "6239", "3356", "6515",
        "3005", "3016", "6177", "2352", "2324", "2404",
        "2408", "2023", "2025", "2030", "2031", "2032", "2033", "2034",
    ]
    
    # 載入 weekly_ranking.json 中的股票，確保散點圖所有股票都有完整數據
    weekly_stocks = set()
    try:
        weekly_path = os.path.join(DATA_DIR, "weekly_ranking.json")
        if os.path.exists(weekly_path):
            with open(weekly_path, "r", encoding="utf-8") as f:
                wr = json.load(f)
            for th in ["200", "400", "1000"]:
                for s in wr.get("thresholds", {}).get(th, {}).get("stocks", []):
                    code = s.get("code", "")
                    if code and code not in all_stocks:
                        weekly_stocks.add(code)
            print(f"[INFO] Added {len(weekly_stocks)} stocks from weekly_ranking.json")
    except Exception as e:
        print(f"[WARN] Could not load weekly_ranking.json: {e}")
    
    all_stocks = list(dict.fromkeys(list(all_stocks) + list(weekly_stocks)))
    
    # 確保 00981A / 00982A 成分股都在抓取列表中
    etf_stocks = list(ETF_00981A_HOLDINGS) + list(ETF_00982A_HOLDINGS)
    all_stocks = list(dict.fromkeys(list(all_stocks) + etf_stocks))
    print(f"[INFO] Added {len(etf_stocks)} ETF holdings (00981A: {len(ETF_00981A_HOLDINGS)}, 00982A: {len(ETF_00982A_HOLDINGS)})")
    
    print(f"[INFO] Total stocks to fetch: {len(all_stocks)}")
    fetcher.fetch_all_data(all_stocks)
    fetcher.fetch_etf_data()


if __name__ == "__main__":
    fetch_all()
