"""
選股邏輯模組
根據用戶條件篩選個股
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

from config import SCREEN_CONFIG, TECH_CONFIG, DATA_DIR


class StockScreener:
    """選股篩選器"""

    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.config = SCREEN_CONFIG
        self.tech = TECH_CONFIG
        self.results = {}

    def _calc_ma(self, price_data, period):
        """計算移動平均線"""
        if not price_data:
            return None
        df = pd.DataFrame(price_data)
        if "Close" not in df.columns or len(df) < period:
            return None
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        return df["Close"].rolling(window=period).mean().iloc[-1] if len(df) >= period else None

    def _calc_rsi(self, price_data, period=14):
        """計算 RSI"""
        if not price_data or len(price_data) < period + 1:
            return None
        df = pd.DataFrame(price_data)
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None

    def check_foreign_buy(self, stock_id):
        """檢查外資買超 (兼容單日數據)"""
        data = self.raw_data.get(stock_id, {})
        foreign = data.get("foreign", [])
        if not foreign:
            # 如果沒有外資數據，檢查 raw_data info 中是否有外資淨買
            info = data.get("info", {})
            foreign_net = info.get("foreign_net", 0)
            return foreign_net > 0, foreign_net, []

        df = pd.DataFrame(foreign)
        if "net" not in df.columns:
            # 兼容舊格式 (buy/sell)
            if "buy" in df.columns and "sell" in df.columns:
                df["net"] = pd.to_numeric(df["buy"], errors="coerce") - pd.to_numeric(df["sell"], errors="coerce")
            else:
                return False, 0, []

        df["net"] = pd.to_numeric(df["net"], errors="coerce")
        latest_net = df["net"].iloc[-1] if not df.empty else 0
        total_net = df["net"].sum()

        # 連買天數 (兼容單日數據：只要有買超就算)
        days = self.config["foreign_buy_days"]
        recent = df.tail(days)
        consecutive_buy = all(recent["net"] > 0) if len(recent) >= days else all(df["net"] > 0)

        return consecutive_buy, int(total_net), recent.to_dict("records")

    def check_big_holder(self, stock_id):
        """檢查大戶持股 (兼容無數據時回傳 0)"""
        data = self.raw_data.get(stock_id, {})
        holding = data.get("holding", [])
        if not holding:
            return 0, 0, []

        df = pd.DataFrame(holding)
        if "percent" not in df.columns:
            return 0, 0, []

        df["percent"] = pd.to_numeric(df["percent"], errors="coerce")
        latest = df.iloc[-1] if not df.empty else None

        if latest is not None and not pd.isna(latest["percent"]):
            pct = float(latest["percent"])
            # 計算週增減
            if len(df) >= 5:
                prev = df.iloc[-5]["percent"] if len(df) >= 5 else df.iloc[0]["percent"]
                change = pct - float(prev)
            else:
                change = 0
            return pct, round(change, 2), df.to_dict("records")

        return 0, 0, []

    def check_margin(self, stock_id):
        """檢查融資融券 (券資比)"""
        data = self.raw_data.get(stock_id, {})
        margin = data.get("margin", [])
        if not margin:
            return None, None, None, []

        df = pd.DataFrame(margin)
        if df.empty:
            return None, None, None, []

        latest = df.iloc[-1]
        margin_balance = float(latest.get("margin_balance", 0)) if "margin_balance" in latest else 0
        short_balance = float(latest.get("short_balance", 0)) if "short_balance" in latest else 0

        ratio = short_balance / margin_balance if margin_balance > 0 else 0

        # 計算單日變化%
        if len(df) >= 2:
            prev = df.iloc[-2]
            prev_margin = float(prev.get("margin_balance", 0)) if "margin_balance" in prev else 0
            prev_short = float(prev.get("short_balance", 0)) if "short_balance" in prev else 0
            margin_change = ((margin_balance - prev_margin) / prev_margin * 100) if prev_margin > 0 else 0
            short_change = ((short_balance - prev_short) / prev_short * 100) if prev_short > 0 else 0
        else:
            margin_change = 0
            short_change = 0

        return {
            "margin_balance": int(margin_balance),
            "short_balance": int(short_balance),
            "ratio": round(ratio, 3),
            "margin_change_pct": round(margin_change, 2),
            "short_change_pct": round(short_change, 2),
        }, margin_change, short_change, df.to_dict("records")

    def check_technical(self, stock_id):
        """檢查技術指標 (MA + RSI)"""
        data = self.raw_data.get(stock_id, {})
        price_data = data.get("price", {})

        # 兼容新舊格式：新格式是 dict {"Close": [...], ...}，舊格式是 list
        if isinstance(price_data, dict):
            close_list = price_data.get("Close", [])
            if close_list:
                price_data = [{"Close": c} for c in close_list]
            else:
                price_data = []

        if not price_data:
            return {}

        ma20 = self._calc_ma(price_data, self.tech["ma_short"])
        ma60 = self._calc_ma(price_data, self.tech["ma_long"])
        rsi = self._calc_rsi(price_data, self.tech["rsi_period"])

        # 最新收盤價
        latest_close = float(price_data[-1]["Close"]) if price_data else 0

        # 判斷趨勢
        trend = "中性"
        if ma20 and ma60 and latest_close:
            if latest_close > ma20 > ma60:
                trend = "多頭排列"
            elif latest_close < ma20 < ma60:
                trend = "空頭排列"
            elif ma20 > ma60:
                trend = "短期強勢"
            else:
                trend = "短期弱勢"

        return {
            "close": round(latest_close, 2),
            "ma20": round(ma20, 2) if ma20 else None,
            "ma60": round(ma60, 2) if ma60 else None,
            "rsi": round(rsi, 1) if rsi else None,
            "trend": trend,
            "above_ma20": latest_close > ma20 if ma20 and latest_close else None,
            "above_ma60": latest_close > ma60 if ma60 and latest_close else None,
        }

    def screen_all(self, stock_list):
        """對所有個股執行選股篩選"""
        screened = []
        big_holder_rank = []

        print(f"開始篩選 {len(stock_list)} 檔個股...")

        for stock_id in stock_list:
            if stock_id not in self.raw_data:
                continue

            info = self.raw_data[stock_id].get("info", {})
            if not info:
                continue

            # 各項檢查
            foreign_ok, foreign_net, foreign_detail = self.check_foreign_buy(stock_id)
            big_pct, big_change, holding_detail = self.check_big_holder(stock_id)
            margin_data, margin_chg, short_chg, margin_detail = self.check_margin(stock_id)
            tech = self.check_technical(stock_id)

            result = {
                "stock_id": stock_id,
                "stock_name": info.get("stock_name", ""),
                "close": info.get("close", 0),
                "change_pct": round(info.get("change_pct", 0), 2),
                "volume": info.get("volume", 0),

                # 外資
                "foreign_buy_days": self.config["foreign_buy_days"],
                "foreign_consecutive_buy": foreign_ok,
                "foreign_net": foreign_net,
                "foreign_detail": foreign_detail,

                # 大戶
                "big_holder_pct": round(big_pct, 2) if big_pct else None,
                "big_holder_change": big_change,
                "big_holder_detail": holding_detail,

                # 融資券
                "margin": margin_data,

                # 技術
                "technical": tech,

                # 綜合評分
                "score": 0,
                "signals": [],
            }

            # 計算綜合評分
            score = 0
            signals = []

            if foreign_ok:
                score += 30
                signals.append(f"外資連買{self.config['foreign_buy_days']}天")
            if big_pct and big_pct > 50:
                score += 20
                signals.append(f"大戶持股{big_pct:.1f}%")
            if margin_data and margin_data["ratio"] > self.config["margin_ratio_threshold"]:
                score += 10
                signals.append(f"券資比{margin_data['ratio']:.2f}")
            if tech.get("trend") == "多頭排列":
                score += 25
                signals.append("多頭排列")
            elif tech.get("trend") == "短期強勢":
                score += 15
                signals.append("短期強勢")
            if tech.get("rsi") and 30 < tech["rsi"] < 70:
                score += 10
                signals.append(f"RSI {tech['rsi']}")

            result["score"] = score
            result["signals"] = signals

            screened.append(result)

            # 大戶排名資料 (兼容無數據時用 0)
            big_holder_rank.append({
                "stock_id": stock_id,
                "stock_name": info.get("stock_name", ""),
                "big_holder_pct": round(big_pct, 2) if big_pct else 0,
                "big_holder_change": big_change if big_change else 0,
                "close": info.get("close", 0),
                "change_pct": round(info.get("change_pct", 0), 2),
            })

        # 排序
        screened.sort(key=lambda x: x["score"], reverse=True)
        big_holder_rank.sort(key=lambda x: x["big_holder_pct"], reverse=True)

        # 生成子列表 (兼容 TWSE API 單日數據)
        foreign_buy = [s for s in screened if s.get("foreign_net", 0) > 0]
        bull_stocks = [s for s in screened if s.get("technical", {}).get("trend") in ["多頭排列", "短期強勢"]]

        self.results = {
            "screened": screened,
            "big_holder_rank": big_holder_rank,
            "foreign_buy": foreign_buy,
            "bull_stocks": bull_stocks,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total": len(screened),
        }

        return self.results

    def save_results(self, filename="screened_data.json"):
        """儲存選股結果"""
        os.makedirs(DATA_DIR, exist_ok=True)
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        print(f"選股結果已儲存: {filepath}")
        return filepath


def run_screening():
    """主入口：執行選股"""
    from config import WATCHLIST, ETF_00981A_HOLDINGS

    # 讀取原始資料
    raw_path = os.path.join(DATA_DIR, "raw_data.json")
    if not os.path.exists(raw_path):
        print(f"找不到原始資料: {raw_path}")
        return {}

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # 執行選股
    screener = StockScreener(raw_data)
    all_stocks = list(set(WATCHLIST + ETF_00981A_HOLDINGS))
    results = screener.screen_all(all_stocks)
    screener.save_results()

    return results


if __name__ == "__main__":
    run_screening()
