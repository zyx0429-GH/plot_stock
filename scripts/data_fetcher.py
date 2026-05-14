"""
台股資料抓取模組
支援 FinMind API + Yahoo Finance (技術指標)
"""

import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
import json
import os

from config import FINMIND_API_TOKEN, DATA_DIR, WATCHLIST, ETF_00981A_HOLDINGS


class TWStockDataFetcher:
    """台股資料抓取器"""

    def __init__(self, api_token=None):
        self.api_token = api_token or FINMIND_API_TOKEN
        if not self.api_token:
            print("[WARN] FinMind API Token 為空！請設定環境變數 FINMIND_API_TOKEN")
        self.base_url = "https://api.finmindtrade.com/api/v4/data"
        self.session = requests.Session()

    def _finmind_request(self, dataset, data_id, start_date, end_date):
        """發送 FinMind API 請求"""
        params = {
            "dataset": dataset,
            "data_id": data_id,
            "start_date": start_date,
            "end_date": end_date,
            "token": self.api_token,
        }
        try:
            resp = self.session.get(self.base_url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if "data" in data and data["data"]:
                return pd.DataFrame(data["data"])
            return pd.DataFrame()
        except Exception as e:
            print(f"[ERROR] FinMind API 錯誤 ({dataset}/{data_id}): {e}")
            return pd.DataFrame()

    def get_stock_price(self, stock_id, days=120):
        """抓取股價資料 (給技術指標用)"""
        end = datetime.now()
        start = end - timedelta(days=days)
        try:
            ticker = yf.Ticker(f"{stock_id}.TW")
            df = ticker.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))
            if df.empty:
                ticker = yf.Ticker(f"{stock_id}.TWO")
                df = ticker.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))
            return df
        except Exception as e:
            print(f"[ERROR] Yahoo Finance 錯誤 ({stock_id}): {e}")
            return pd.DataFrame()

    def get_foreign_investment(self, stock_id, days=30):
        """抓取外資買賣超資料 (三大法人)"""
        end = datetime.now()
        start = end - timedelta(days=days)
        df = self._finmind_request(
            "TaiwanStockInstitutionalInvestorsBuySell",
            stock_id,
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d")
        )
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            # 外資 = Foreign_Investor
            foreign = df[df["name"] == "Foreign_Investor"].copy()
            return foreign.sort_values("date")
        return pd.DataFrame()

    def get_margin_trading(self, stock_id, days=30):
        """抓取融資融券資料"""
        end = datetime.now()
        start = end - timedelta(days=days)
        df = self._finmind_request(
            "TaiwanStockMarginPurchaseShortSale",
            stock_id,
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d")
        )
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            # FinMind v4 欄位名稱：MarginPurchaseTodayBalance / ShortSaleTodayBalance
            margin_col = "MarginPurchaseTodayBalance" if "MarginPurchaseTodayBalance" in df.columns else "margin_purchase"
            short_col = "ShortSaleTodayBalance" if "ShortSaleTodayBalance" in df.columns else "short_sale"
            if margin_col in df.columns and short_col in df.columns:
                df["margin_balance"] = pd.to_numeric(df[margin_col], errors="coerce")
                df["short_balance"] = pd.to_numeric(df[short_col], errors="coerce")
                df["margin_short_ratio"] = df["short_balance"] / df["margin_balance"].replace(0, np.nan)
                return df.sort_values("date")
        return pd.DataFrame()

    def get_stock_holding(self, stock_id, days=30):
        """抓取股權分散表 (大戶持股) - 免費版 FinMind 可能無此欄位"""
        end = datetime.now()
        start = end - timedelta(days=days)
        df = self._finmind_request(
            "TaiwanStockShareholding",
            stock_id,
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d")
        )
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            # 免費版 FinMind 的 TaiwanStockShareholding 只有外資持股，沒有 HoldingSharesLevel
            # 若欄位不存在則回傳空 DataFrame，不拋錯
            if "HoldingSharesLevel" not in df.columns:
                return pd.DataFrame()
            big_holder = df[df["HoldingSharesLevel"].str.contains("400", na=False)].copy()
            if not big_holder.empty:
                big_holder["percent"] = pd.to_numeric(big_holder["percent"], errors="coerce")
                return big_holder.sort_values("date")
        return pd.DataFrame()

    def get_stock_info(self, stock_id):
        """抓取個股基本資料"""
        end = datetime.now()
        start = end - timedelta(days=5)
        df = self._finmind_request(
            "TaiwanStockPrice",
            stock_id,
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d")
        )
        if not df.empty:
            latest = df.iloc[-1]
            return {
                "stock_id": stock_id,
                "stock_name": latest.get("stock_name", ""),
                "close": float(latest.get("close", 0)),
                "open": float(latest.get("open", 0)),
                "high": float(latest.get("max", 0)),
                "low": float(latest.get("min", 0)),
                "volume": int(latest.get("Trading_Volume", 0)),
                "change": float(latest.get("spread", 0)),
                "change_pct": float(latest.get("spread", 0)) / float(latest.get("close", 1)) * 100,
            }
        return None

    def fetch_all_data(self, stock_list):
        """批次抓取所有個股資料"""
        results = {}
        total = len(stock_list)
        print(f"開始抓取 {total} 檔個股資料...")

        for i, stock_id in enumerate(stock_list, 1):
            print(f"[{i}/{total}] 抓取 {stock_id}...", end=" ")
            try:
                info = self.get_stock_info(stock_id)
                if info:
                    foreign = self.get_foreign_investment(stock_id, days=14)
                    margin = self.get_margin_trading(stock_id, days=14)
                    holding = self.get_stock_holding(stock_id, days=14)
                    price_df = self.get_stock_price(stock_id, days=120)

                    results[stock_id] = {
                        "info": info,
                        "foreign": foreign.to_dict("records") if not foreign.empty else [],
                        "margin": margin.to_dict("records") if not margin.empty else [],
                        "holding": holding.to_dict("records") if not holding.empty else [],
                        "price": self._price_to_dict(price_df),
                    }
                    print("[OK]")
                else:
                    print("[NO DATA]")
            except Exception as e:
                import traceback
                print(f"[ERR] {e}")
                traceback.print_exc()

            time.sleep(0.5)  # 避免 API 過載

        return results

    def _price_to_dict(self, df):
        """將價格 DataFrame 轉為 dict"""
        if df.empty:
            return []
        df = df.reset_index()
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
        return df[["Date", "Open", "High", "Low", "Close", "Volume"]].to_dict("records")

    def save_to_json(self, data, filename="stock_data.json"):
        """儲存資料到 JSON"""
        # 確保 data/ 目錄存在
        os.makedirs(DATA_DIR, exist_ok=True)
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"資料已儲存: {filepath}")
        return filepath


def fetch_all():
    """主入口：抓取自選清單 + 00981A 成分股"""
    fetcher = TWStockDataFetcher()

    # 合併清單去重
    all_stocks = list(set(WATCHLIST + ETF_00981A_HOLDINGS))
    all_stocks.sort()

    # 抓取資料
    data = fetcher.fetch_all_data(all_stocks)

    # 儲存
    fetcher.save_to_json(data, "raw_data.json")
    return data


if __name__ == "__main__":
    fetch_all()
