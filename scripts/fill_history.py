"""
補充過去5天外資/投信/融資歷史數據到 raw_data.json
從 TWSE + TPEX API 抓取
"""
import json
import requests
import os
import time

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RAW_PATH = os.path.join(DATA_DIR, "raw_data.json")

session = requests.Session()
session.verify = False

# 需要補充的日期 (最近5個交易日)
# 2026-06-26(五), 06-29(一), 06-30(二), 07-01(三), 07-02(四)
DATES = ["20260626", "20260629", "20260630", "20260701", "20260702"]


def twse_get(endpoint, params):
    url = f"https://www.twse.com.tw/{endpoint}"
    try:
        resp = session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("stat") == "OK":
            return data
    except Exception as e:
        print(f"[ERR] TWSE {endpoint} {params}: {e}")
    return {}


def tpex_get(endpoint, params):
    url = f"https://www.tpex.org.tw/{endpoint}"
    try:
        resp = session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERR] TPEX {endpoint} {params}: {e}")
    return {}


def fetch_twse_t86(date_str):
    """抓取上市三大法人"""
    t86 = twse_get("fund/T86", {"response": "json", "date": date_str, "selectType": "ALLBUT0999"})
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
    return foreign_map, trust_map


def fetch_tpex_t86(date_str):
    """抓取上櫃三大法人"""
    roc_year = int(date_str[:4]) - 1911
    roc_date = f"{roc_year}/{date_str[4:6]}/{date_str[6:8]}"
    data = tpex_get("web/stock/3insti/daily_trade/3insti_result.php", {
        "l": "zh-tw", "o": "htm", "se": "EW", "t": "D", "d": roc_date, "s": "0,asc"
    })
    foreign_map = {}
    trust_map = {}
    if data.get("aaData"):
        for row in data["aaData"]:
            if len(row) < 10:
                continue
            sid = str(row[0]).strip()
            try:
                f_buy = int(str(row[4]).replace(",", ""))
                f_sell = int(str(row[5]).replace(",", ""))
                f_net = int(str(row[6]).replace(",", ""))
                foreign_map[sid] = {"buy": f_buy, "sell": f_sell, "net": f_net}
                t_buy = int(str(row[7]).replace(",", ""))
                t_sell = int(str(row[8]).replace(",", ""))
                t_net = int(str(row[9]).replace(",", ""))
                trust_map[sid] = {"buy": t_buy, "sell": t_sell, "net": t_net}
            except Exception:
                pass
    return foreign_map, trust_map


def fetch_twse_margin(date_str):
    """抓取上市融資融券"""
    margn = twse_get("exchangeReport/MI_MARGN", {"response": "json", "date": date_str, "selectType": "ALL"})
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
                        "ratio": round(ratio, 4),
                    }
                except Exception:
                    pass
    return margin_map


def fetch_tpex_margin(date_str):
    """抓取上櫃融資融券"""
    roc_year = int(date_str[:4]) - 1911
    roc_date = f"{roc_year}/{date_str[4:6]}/{date_str[6:8]}"
    data = tpex_get("web/stock/margin_trading/margin_balance/margin_bal_result.php", {
        "l": "zh-tw", "o": "htm", "se": "AL", "t": "D", "d": roc_date, "s": "0,asc"
    })
    margin_map = {}
    if data.get("aaData"):
        for row in data["aaData"]:
            if len(row) < 10:
                continue
            sid = str(row[0]).strip()
            try:
                margin_balance = int(str(row[6]).replace(",", ""))
                short_balance = int(str(row[9]).replace(",", ""))
                prev_margin = int(str(row[5]).replace(",", ""))
                prev_short = int(str(row[8]).replace(",", ""))
                ratio = short_balance / margin_balance if margin_balance > 0 else 0
                margin_map[sid] = {
                    "margin_balance": margin_balance,
                    "short_balance": short_balance,
                    "margin_prev": prev_margin,
                    "short_prev": prev_short,
                    "margin_change": margin_balance - prev_margin,
                    "short_change": short_balance - prev_short,
                    "ratio": round(ratio, 4),
                }
            except Exception:
                pass
    return margin_map


def main():
    # 載入現有 raw_data.json
    if os.path.exists(RAW_PATH):
        with open(RAW_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    else:
        print("[ERR] raw_data.json not found")
        return

    # 收集所有需要補充的股票代號
    all_stock_ids = set(raw_data.keys())

    # 按日期抓取並合併
    for date_str in DATES:
        print(f"\n[INFO] Fetching {date_str}...")

        # TWSE 外資/投信
        twse_f, twse_t = fetch_twse_t86(date_str)
        print(f"  TWSE foreign: {len(twse_f)}, trust: {len(twse_t)}")

        # TPEX 外資/投信
        tpex_f, tpex_t = fetch_tpex_t86(date_str)
        print(f"  TPEX foreign: {len(tpex_f)}, trust: {len(tpex_t)}")

        # TWSE 融資
        twse_m = fetch_twse_margin(date_str)
        print(f"  TWSE margin: {len(twse_m)}")

        # TPEX 融資
        tpex_m = fetch_tpex_margin(date_str)
        print(f"  TPEX margin: {len(tpex_m)}")

        # 合併到 raw_data
        for sid in all_stock_ids:
            record = raw_data[sid]

            # 外資: 以上市為主，上櫃補缺
            f_data = twse_f.get(sid)
            if not f_data:
                f_data = tpex_f.get(sid)

            if f_data:
                foreign_list = record.get("foreign", [])
                # 檢查是否已有該日期
                existing_dates = {f.get("date") for f in foreign_list}
                if date_str not in existing_dates:
                    foreign_list.append({
                        "date": date_str,
                        "buy": f_data["buy"],
                        "sell": f_data["sell"],
                        "net": f_data["net"],
                    })
                    foreign_list.sort(key=lambda x: x.get("date", ""))
                    record["foreign"] = foreign_list

            # 投信
            t_data = twse_t.get(sid)
            if not t_data:
                t_data = tpex_t.get(sid)

            if t_data:
                trust_list = record.get("trust", [])
                existing_dates = {t.get("date") for t in trust_list}
                if date_str not in existing_dates:
                    trust_list.append({
                        "date": date_str,
                        "buy": t_data["buy"],
                        "sell": t_data["sell"],
                        "net": t_data["net"],
                    })
                    trust_list.sort(key=lambda x: x.get("date", ""))
                    record["trust"] = trust_list

            # 融資
            m_data = twse_m.get(sid)
            if not m_data:
                m_data = tpex_m.get(sid)

            if m_data:
                margin_list = record.get("margin", [])
                existing_dates = {m.get("date") for m in margin_list}
                if date_str not in existing_dates:
                    margin_list.append({
                        "date": date_str,
                        "margin_balance": m_data["margin_balance"],
                        "short_balance": m_data["short_balance"],
                        "margin_prev": m_data.get("margin_prev", 0),
                        "short_prev": m_data.get("short_prev", 0),
                        "margin_change": m_data["margin_change"],
                        "short_change": m_data["short_change"],
                        "margin_short_ratio": m_data["ratio"],
                    })
                    margin_list.sort(key=lambda x: x.get("date", ""))
                    record["margin"] = margin_list

        time.sleep(1)  # 禮貌延遲

    # 儲存
    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    # 驗證
    print("\n[INFO] Verification:")
    for sid in list(all_stock_ids)[:3]:
        foreign = raw_data[sid].get("foreign", [])
        trust = raw_data[sid].get("trust", [])
        margin = raw_data[sid].get("margin", [])
        print(f"  {sid}: foreign={len(foreign)} days, trust={len(trust)} days, margin={len(margin)} days")
        if foreign:
            print(f"    foreign dates: {[f['date'] for f in foreign]}")

    print(f"\n[OK] Saved to {RAW_PATH}")


if __name__ == "__main__":
    main()
