import pandas as pd
import json
import os
from datetime import datetime
from config import SCREEN_CONFIG, DATA_DIR, WATCHLIST, ETF_00981A_HOLDINGS


class StockScreener:
    """台股篩選器 (兼容 TWSE API 單日數據)"""

    def __init__(self, config=None):
        self.config = config or SCREEN_CONFIG
        self.raw_data = self._load_raw_data()
        self.results = {}

    def _load_raw_data(self):
        """載入原始資料"""
        path = os.path.join(DATA_DIR, "raw_data.json")
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_stock_info(self, stock_id):
        """獲取股票基本資訊"""
        data = self.raw_data.get(stock_id, {})
        return data.get("info", {})

    def _get_technical_analysis(self, stock_id):
        """技術分析"""
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

        df = pd.DataFrame(price_data)
        if "Close" not in df.columns:
            return {}

        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        close = df["Close"]

        if len(df) < 20:
            return {}

        ma20 = close.rolling(20).mean().iloc[-1]
        ma60 = close.rolling(60).mean().iloc[-1] if len(df) >= 60 else None

        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain.iloc[-1] / avg_loss.iloc[-1] if avg_loss.iloc[-1] != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if avg_loss.iloc[-1] != 0 else 50

        # 趨勢判斷
        if ma20 and ma60:
            trend = "多頭排列" if ma20 > ma60 else "空頭排列"
        else:
            trend = "短期震盪"

        return {
            "ma20": round(ma20, 2) if not pd.isna(ma20) else "-",
            "ma60": round(ma60, 2) if ma60 and not pd.isna(ma60) else "-",
            "rsi": round(rsi, 1) if not pd.isna(rsi) else "-",
            "trend": trend,
        }

    def check_foreign_buy(self, stock_id):
        """檢查外資買超 (兼容單日數據)"""
        data = self.raw_data.get(stock_id, {})
        foreign = data.get("foreign", [])
        if not foreign:
            info = data.get("info", {})
            foreign_net = info.get("foreign_net", 0)
            return foreign_net > 0, foreign_net, []

        df = pd.DataFrame(foreign)
        if "net" not in df.columns:
            if "buy" in df.columns and "sell" in df.columns:
                df["net"] = pd.to_numeric(df["buy"], errors="coerce") - pd.to_numeric(df["sell"], errors="coerce")
            else:
                return False, 0, []

        df["net"] = pd.to_numeric(df["net"], errors="coerce")
        latest_net = df["net"].iloc[-1] if not df.empty else 0
        total_net = df["net"].sum()

        days = self.config["foreign_buy_days"]
        recent = df.tail(days)
        consecutive_buy = all(recent["net"] > 0) if len(recent) >= days else all(df["net"] > 0)
        return consecutive_buy, int(total_net), recent.to_dict("records")

    def check_trust_buy(self, stock_id):
        """檢查投信買超 (兼容單日數據)"""
        data = self.raw_data.get(stock_id, {})
        trust = data.get("trust", [])
        if not trust:
            info = data.get("info", {})
            trust_net = info.get("trust_net", 0)
            return trust_net > 0, trust_net, []

        df = pd.DataFrame(trust)
        if "net" not in df.columns:
            return False, 0, []

        df["net"] = pd.to_numeric(df["net"], errors="coerce")
        latest_net = df["net"].iloc[-1] if not df.empty else 0
        total_net = df["net"].sum()

        days = self.config["foreign_buy_days"]
        recent = df.tail(days)
        consecutive_buy = all(recent["net"] > 0) if len(recent) >= days else all(df["net"] > 0)
        return consecutive_buy, int(total_net), recent.to_dict("records")

    def check_dual_certified(self, stock_id, info, tech, big_pct, big_change, foreign_consecutive, trust_consecutive):
        """
        雙重認證篩選:
        條件1: 在 00981A 成分股清單中
        條件2: 400大戶近期增倉 (big_holder_change > 0)
        條件3: 外資連買 or 投信連買
        """
        is_in_00981a = stock_id in ETF_00981A_HOLDINGS
        big_holder_increasing = big_change > 0 if big_change else False
        buying = foreign_consecutive or trust_consecutive
        return is_in_00981a and big_holder_increasing and buying

    def check_big_holder(self, stock_id):
        """檢查大戶持股 (兼容週報 big_holder_pct / 舊接口 percent)"""
        data = self.raw_data.get(stock_id, {})
        holding = data.get("holding", [])
        if not holding:
            return 0, 0, "", []

        df = pd.DataFrame(holding)
        # 優先使用大戶週報的欄位名
        pct_col = None
        for c in ["big_holder_pct", "percent"]:
            if c in df.columns:
                pct_col = c
                break
        if not pct_col:
            return 0, 0, "", []

        df[pct_col] = pd.to_numeric(df[pct_col], errors="coerce")
        latest = df.iloc[-1] if not df.empty else None

        if latest is not None and not pd.isna(latest[pct_col]):
            pct = float(latest[pct_col])
            # 優先使用週報的週增減欄位
            if "big_holder_change_pct" in df.columns:
                change = float(pd.to_numeric(latest.get("big_holder_change_pct", 0), errors="coerce"))
            elif len(df) >= 2:
                prev = df.iloc[-2][pct_col] if len(df) >= 2 else df.iloc[0][pct_col]
                change = pct - float(prev)
            else:
                change = 0
            threshold = str(latest.get("threshold", "—")) if "threshold" in df.columns else "—"
            return pct, round(change, 2), threshold, df.to_dict("records")

        return 0, 0, "", []

    def check_margin(self, stock_id):
        """檢查融資融券"""
        data = self.raw_data.get(stock_id, {})
        margin = data.get("margin", [])
        if not margin:
            return None

        df = pd.DataFrame(margin)
        if df.empty or "margin_balance" not in df.columns:
            return None

        latest = df.iloc[-1]
        return {
            "balance": int(latest.get("margin_balance", 0)),
            "ratio": round(float(latest.get("margin_short_ratio", 0)), 4),
            "change": int(latest.get("margin_balance", 0)) - int(df.iloc[0].get("margin_balance", 0)) if len(df) > 1 else 0,
        }

    def _calculate_score(self, stock_id, info, tech, foreign_consecutive, big_holder_pct, margin):
        """計算綜合評分"""
        score = 0

        # 技術面評分 (0-30)
        if tech and tech.get("trend") == "多頭排列":
            score += 30
        elif tech and tech.get("trend") == "短期震盪":
            score += 15

        # 籌碼面評分 (0-40)
        if big_holder_pct and big_holder_pct > 20:
            score += 40
        elif big_holder_pct and big_holder_pct > 15:
            score += 30
        elif big_holder_pct and big_holder_pct > 10:
            score += 20

        # 外資評分 (0-20)
        if foreign_consecutive:
            score += 20

        # 融資評分 (0-10)
        if margin and margin.get("ratio", 0) > 0.3:
            score += 10

        return score

    def screen_watchlist(self):
        """篩選自選清單"""
        watchlist_data = []
        for stock_id in WATCHLIST:
            info = self._get_stock_info(stock_id)
            if not info:
                continue
            close = info.get("close", 0)
            if close == 0 or close is None:
                continue
            tech = self._get_technical_analysis(stock_id)
            foreign_consecutive, foreign_net, foreign_detail = self.check_foreign_buy(stock_id)
            trust_consecutive, trust_net, trust_detail = self.check_trust_buy(stock_id)
            big_pct, big_change, big_threshold, big_detail = self.check_big_holder(stock_id)
            margin = self.check_margin(stock_id)
            score = self._calculate_score(stock_id, info, tech, foreign_consecutive, big_pct, margin)

            watchlist_data.append({
                "stock_id": stock_id,
                "stock_name": info.get("stock_name", ""),
                "close": close,
                "open": info.get("open", 0),
                "change_pct": round(info.get("change_pct", 0), 2),
                "foreign_consecutive_buy": foreign_consecutive,
                "foreign_net": foreign_net,
                "trust_consecutive_buy": trust_consecutive,
                "trust_net": trust_net,
                "big_holder_pct": round(big_pct, 2) if big_pct else 0,
                "big_holder_change": big_change if big_change else 0,
                "big_holder_threshold": big_threshold,
                "score": score,
                "technical": tech,
                "margin": margin,
                "shareholder": self.raw_data.get(stock_id, {}).get("shareholder", []),
            })

        # 主排序: score 降序, 次排序: 大戶門檻數字降序 (1000>400>200>100>1), 三排序: 大戶%降序
        def _watchlist_sort_key(x):
            th = x.get("big_holder_threshold", "") or "0"
            try:
                th_val = int(th)
            except:
                th_val = 0
            return (-x["score"], -th_val, -(x.get("big_holder_pct", 0) or 0))
        watchlist_data.sort(key=_watchlist_sort_key)
        return watchlist_data

    def screen_all(self):
        """執行所有篩選條件 (兼容單日數據)"""
        screened = []
        big_holder_rank = []

        for stock_id in self.raw_data.keys():
            info = self._get_stock_info(stock_id)
            if not info:
                continue

            close = info.get("close", 0)
            # 隱藏價格為 0 的股票
            if close == 0 or close is None:
                continue

            tech = self._get_technical_analysis(stock_id)
            foreign_consecutive, foreign_net, foreign_detail = self.check_foreign_buy(stock_id)
            trust_consecutive, trust_net, trust_detail = self.check_trust_buy(stock_id)
            big_pct, big_change, big_threshold, big_detail = self.check_big_holder(stock_id)
            margin = self.check_margin(stock_id)
            score = self._calculate_score(stock_id, info, tech, foreign_consecutive, big_pct, margin)

            stock_info = {
                "stock_id": stock_id,
                "stock_name": info.get("stock_name", ""),
                "close": close,
                "open": info.get("open", 0),
                "change_pct": round(info.get("change_pct", 0), 2),
                "foreign_consecutive_buy": foreign_consecutive,
                "foreign_net": foreign_net,
                "trust_consecutive_buy": trust_consecutive,
                "trust_net": trust_net,
                "big_holder_pct": round(big_pct, 2) if big_pct else 0,
                "big_holder_change": big_change if big_change else 0,
                "big_holder_threshold": big_threshold,
                "score": score,
                "technical": tech,
                "margin": margin,
                "dual_certified": self.check_dual_certified(stock_id, info, tech, big_pct, big_change, foreign_consecutive, trust_consecutive),
                "shareholder": self.raw_data.get(stock_id, {}).get("shareholder", []),
            }

            # 綜合篩選條件
            if score >= 40 or big_pct is not None or margin:
                screened.append(stock_info)

            # 大戶排名資料 (兼容無數據時用 0)
            big_holder_rank.append({
                "stock_id": stock_id,
                "stock_name": info.get("stock_name", ""),
                "big_holder_pct": round(big_pct, 2) if big_pct else 0,
                "big_holder_change": big_change if big_change else 0,
                "big_holder_threshold": big_threshold,
                "close": close,
                "change_pct": round(info.get("change_pct", 0), 2),
            })

        # 排序
        screened.sort(key=lambda x: x["score"], reverse=True)
        big_holder_rank.sort(key=lambda x: x["big_holder_pct"], reverse=True)

        # 生成子列表 (兼容 TWSE API 單日數據)
        foreign_buy = [s for s in screened if s.get("foreign_net", 0) > 0]
        trust_buy = [s for s in screened if s.get("trust_net", 0) > 0]
        bull_stocks = [s for s in screened if s.get("technical", {}).get("trend") in ["短多頭", "多頭排列"]]
        dual_certified = [s for s in screened if s.get("dual_certified", False)]

        self.results = {
            "screened": screened,
            "big_holder_rank": big_holder_rank,
            "foreign_buy": foreign_buy,
            "trust_buy": trust_buy,
            "bull_stocks": bull_stocks,
            "dual_certified": dual_certified,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total": len(screened),
        }

        return self.results

    def run_screening(self):
        """執行完整篩選流程"""
        if not self.raw_data:
            print("[ERROR] No raw data found. Run data_fetcher first.")
            return {}

        results = self.screen_all()
        watchlist = self.screen_watchlist()

        # 儲存結果
        output_path = os.path.join(DATA_DIR, "screened_data.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                **results,
                "watchlist": watchlist,
                "config": {
                    "foreign_buy_days": SCREEN_CONFIG["foreign_buy_days"],
                    "etf_00981a_holdings": list(ETF_00981A_HOLDINGS),
                },
            }, f, ensure_ascii=False, indent=2)

        print(f"[INFO] Screening complete. {results['total']} stocks screened.")
        print(f"  - Foreign buy: {len(results['foreign_buy'])}")
        print(f"  - Trust buy: {len(results['trust_buy'])}")
        print(f"  - Bull stocks: {len(results['bull_stocks'])}")
        print(f"  - Dual certified: {len(results['dual_certified'])}")
        print(f"  - Watchlist: {len(watchlist)}")

        return results


if __name__ == "__main__":
    screener = StockScreener()
    results = screener.run_screening()


def run_screening():
    """模組級入口：供 main.py 調用"""
    screener = StockScreener()
    return screener.run_screening()
