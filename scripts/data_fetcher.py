"""
台股資料抓取模組 — TWSE 官方 API 版本
免費、無額度限制
"""

import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
import json
import os
import warnings

warnings.filterwarnings('ignore')

from config import DATA_DIR, WATCHLIST, ETF_00981A_HOLDINGS


class TWStockDataFetcher:
    """台股資料抓取器 — TWSE + Yahoo Finance"""

    def __init__(self, api_token=None):
        self.api_token = api_token
        self.twse_base = "https://www.twse.com.tw"
        self.session = requests.Session()
        # 減少 SSL 驗證警告
        self.session.verify = False
        print(f"[INFO] DataFetcher initialized (TWSE + Yahoo Finance mode)")

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

    def _yf_price(self, stock_id, days=60):
        """用 yfinance 抓股價歷史 — 嘗試 .TW 和 .TWO"""
        for suffix in [".TW", ".TWO"]:
            try:
                ticker = yf.Ticker(f"{stock_id}{suffix}")
                df = ticker.history(period=f"{days}d")
                if not df.empty:
                    return df
            except Exception:
                pass
        return pd.DataFrame()

    def _calc_technical(self, df):
        """計算技術指標 (MA20, MA60, RSI)"""
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
        # Trend
        if ma20 and ma60:
            trend = "短多頭" if ma20 > ma60 else "短空頭"
        else:
            trend = ""
        return {
            "ma20": round(ma20, 2) if ma20 else "-",
            "ma60": round(ma60, 2) if ma60 else "-",
            "rsi": round(rsi, 1) if rsi else "-",
            "trend": trend,
        }

    def fetch_all_data(self, stock_list):
        """批次抓取所有個股資料 — TWSE API + Yahoo Finance"""
        results = {}
        today_str = datetime.now().strftime("%Y%m%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        print(f"[INFO] Fetching TWSE data for {len(stock_list)} stocks...")
        print(f"[INFO] Using date: {today_str}")

        # === Step 1: 抓取全市場每日成交資料 (STOCK_DAY_ALL) ===
        print("[INFO] Fetching STOCK_DAY_ALL...")
        day_all = self._twse_get("exchangeReport/STOCK_DAY_ALL", {"response": "json", "date": today_str})
        if not day_all.get("data"):
            # 若今天沒資料，試昨天
            print("[WARN] No data for today, trying yesterday...")
            day_all = self._twse_get("exchangeReport/STOCK_DAY_ALL", {"response": "json", "date": yesterday})
        price_map = {}
        if day_all.get("data"):
            for row in day_all["data"]:
                # row: [證券代號, 證券名稱, 成交股數, 成交金額, 開盤價, 最高價, 最低價, 收盤價, 漲跌價差, 成交筆數]
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
                except Exception as e:
                    pass
        print(f"[INFO] STOCK_DAY_ALL: {len(price_map)} stocks")

        # === Step 2: 抓取三大法人買賣超 (T86) ===
        print("[INFO] Fetching T86 (institutional investors)...")
        t86 = self._twse_get("fund/T86", {"response": "json", "date": today_str, "selectType": "ALLBUT0999"})
        if not t86.get("data"):
            t86 = self._twse_get("fund/T86", {"response": "json", "date": yesterday, "selectType": "ALLBUT0999"})
        foreign_map = {}
        if t86.get("data") and t86.get("fields"):
            # fields: [證券代號, 證券名稱, 外資買進股數, 外資賣出股數, 外資買賣超股數, ...]
            fidx = {name: i for i, name in enumerate(t86["fields"])}
            for row in t86["data"]:
                sid = row[fidx.get("證券代號", 0)]
                try:
                    buy = int(row[fidx.get("外資買進股數", 6)].replace(",", ""))
                    sell = int(row[fidx.get("外資賣出股數", 7)].replace(",", ""))
                    net = int(row[fidx.get("外資買賣超股數", 8)].replace(",", ""))
                    foreign_map[sid.lstrip("0") or "0"] = {"buy": buy, "sell": sell, "net": net}
                except Exception:
                    pass
        print(f"[INFO] T86: {len(foreign_map)} stocks")

        # === Step 3: 抓取融資融券 (MI_MARGN) ===
        print("[INFO] Fetching MI_MARGN (margin trading)...")
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
                        ratio = short_balance / margin_balance if margin_balance > 0 else 0
                        margin_map[sid.lstrip("0") or "0"] = {
                            "margin_balance": margin_balance,
                            "short_balance": short_balance,
                            "ratio": round(ratio, 4),
                        }
                    except Exception:
                        pass
        print(f"[INFO] MI_MARGN: {len(margin_map)} stocks")

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

                margin_data = margin_map.get(stock_id, {})
                margin_list = []
                if margin_data:
                    margin_list = [{
                        "date": today_str,
                        "margin_balance": margin_data["margin_balance"],
                        "short_balance": margin_data["short_balance"],
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
                    "margin": margin_list,
                    "holding": [],  # 大戶持股暫時不抓
                    "price": price_dict,
                }
                print("[OK]")
            except Exception as e:
                print(f"[ERR] {e}")

            time.sleep(0.3)  # 避免 yfinance rate limit

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


if __name__ == "__main__":
    fetcher = TWStockDataFetcher()
    all_stocks = list(WATCHLIST) + [
        "2330", "2317", "2454", "2303", "2881", "2882", "1216", "1301", "3008", "0050", "0056",
        "3006", "2345", "2376", "2301", "2327", "2313", "2409", "3481", "3037", "2357",
        "3661", "2382", "6415", "5274", "2344", "2356", "2377", "2383", "30277", "3665",
        "4967", "6213", "8150", "8042", "8046", "8996", "5439", "6805", "6770", "6669",
        "4961", "6271", "6274", "3443", "3376", "3264", "3217", "2428", "2439", "2449",
        "2492", "2481", "4919", "3711", "3680", "6191", "6187", "6182", "6173", "6147",
        "1815", "1590", "1319", "00981A", "1605", "6239", "6261", "3356", "3661", "6510",
        "6515", "4966", "3005", "6257", "3016", "6104", "6177", "2352", "2324", "2404",
        "2408", "2023", "2025", "2030", "2031", "2032", "2033", "2034",
    ]
    # 去重
    all_stocks = list(dict.fromkeys(all_stocks))
    fetcher.fetch_all_data(all_stocks)
    fetcher.fetch_etf_data()
