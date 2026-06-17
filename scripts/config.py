"""
台股籌碼監控選股站 - 配置文件 (智董專屬版)
"""

# === 資料源配置 ===
import os
FINMIND_API_TOKEN = os.environ.get("FINMIND_API_TOKEN", "")
# 本地開發可覆蓋： export FINMIND_API_TOKEN="your_token"

# === 選股條件 ===
SCREEN_CONFIG = {
    "foreign_buy_days": 3,           # 外資連買 N 天
    "big_holder_min_shares": 400,    # 大戶持股門檻：400張 (1張=1000股)
    "big_holder_rank_default": 50,   # 大戶排名預設顯示前50名
    "margin_ratio_threshold": 0.5,   # 券資比建議值 (融券餘額/融資餘額)
    "margin_spike_pct": 20,          # 融資/融券單日變化超過20%視為異常
}

# === 技術指標 ===
TECH_CONFIG = {
    "ma_short": 20,    # 短期均線
    "ma_long": 60,     # 長期均線
    "rsi_period": 14,  # RSI週期
    "volume_ma": 5,    # 成交量均線
}

# === 智董持倉股 (9檔) ===
MY_HOLDINGS = [
    "2327",  # 國巨 (7張)
    "3006",  # 晶豪科 (32張)
    "6213",  # 聯茂 (6張)
    "1815",  # 富喬 (11張)
    "2409",  # 友達 (223張)
    "6239",  # 力成 (1張)
    "4967",  # 十銓 (1張)
    "2377",  # 微星 (13張)
    "2313",  # 華通 (5張)
]

# === 觀察清單 ===
WATCHLIST = [
    # --- 智董持倉股 ---
    "2327",  # 國巨
    "3006",  # 晶豪科
    "6213",  # 聯茂
    "1815",  # 富喬
    "2409",  # 友達
    "6239",  # 力成
    "4967",  # 十銓
    "2377",  # 微星
    "2313",  # 華通
    # --- 族群核心 ---
    "2408",  # 南亞科 (DRAM)
    "2344",  # 華邦電 (DRAM)
    "2330",  # 台積電 (AI)
    "3661",  # 世芯 (AI)
    "2376",  # 技嘉 (AI)
    "2382",  # 廣達 (AI)
    "3443",  # 創意 (AI)
    "2324",  # 仁寶 (AI)
    "3037",  # 欣興 (PCB)
    "2355",  # 敬鵬 (PCB)
    "2301",  # 光寶科 (BBU)
    "2356",  # 英業達 (BBU)
    "4919",  # 新唐 (BBU)
    "4961",  # 天鈺 (BBU)
    "2428",  # 興勤 (BBU)
    "6271",  # 同欣電 (BBU)
    # --- 大戶漏網之魚 ---
    "6182",  # 合晶 (半導體材料#1)
    "8042",  # 金山電 (被動元件#2)
    "3481",  # 群創 (面板#3)
    "8150",  # 南茂 (封測#7)
    "6173",  # 信昌電 (被動元件#8)
    "3680",  # 家登 (半導體設備#10)
    "8358",  # 金居 (被動元件#11)
    "2492",  # 華新科 (被動元件#13)
    "6261",  # 久元 (半導體測試#16)
    "6770",  # 力積電 (DRAM#23)
    "3450",  # 聯鈞 (矽光#15)
    # --- 00981A 前20大 (部分已在上面) ---
    "2383",  # 台光電
    "2454",  # 聯發科
    "2345",  # 智邦
    "2308",  # 台達電
    "6669",  # 緯穎
    "3665",  # 貿聯-KY
    "2368",  # 金像電
    "8046",  # 南電
    "6223",  # 旺矽
    "3017",  # 奇鋐
    "3711",  # 日月光投控
    "5274",  # 信驊
    "3653",  # 健策
    "6274",  # 台燿
    "6515",  # 穎崴
    "6510",  # 精測
    "8210",  # 勤誠
    "6805",  # 富世達
    "2449",  # 京元電子
    "3264",  # 欣銓
    "5439",  # 高技
    "2357",  # 華碩
    "6187",  # 萬潤
    "2404",  # 漢唐
    "8996",  # 高力
    "4966",  # 譜瑞-KY
    "1590",  # 亞德客-KY
    "6415",  # 矽力*-KY
    "2481",  # 強茂
    "6191",  # 精成科
    "3376",  # 新日興
    "3036",  # 文曄
    "2317",  # 鴻海
    "3661",  # 世芯-KY
    "2002",  # 中鋼
    "3217",  # 優群
    "1319",  # 東陽
    "2439",  # 美律
    "2337",  # 旺宏
    "5347",  # 世界
# === 大戶增持熱門 — fortune-fred Top 25 (2026-05-23) ===
    "6485",  # 點序
    "6127",  # 九豪
    "5425",  # 台半
    "5291",  # 邑昇
    "5328",  # 華容
    "8043",  # 蜜望實
    "6207",  # 雷科
    "3675",  # 德微
    "3236",  # 千如
    "8096",  # 擎亞
    "8040",  # 九暘
    "3624",  # 光頡
    "3537",  # 堡達
    "6284",  # 佳邦
    "6727",  # 亞泰金屬
    "6462",  # 神盾
    "3663",  # 鑫科
    "3357",  # 臺慶科
    "3709",  # 鑫聯大投控
    "8289",  # 泰藝
    "3498",  # 陽程
    "8091",  # 翔名
    # --- 金融股 ---
    "2882",  # 國泰金
    "2890",  # 永豐金
    "2881",  # 富邦金
    "2892",  # 第一金
    "2850",  # 新產
    "2885",  # 元大金
    "2880",  # 華南金
    "2883",  # 凱基金
    "2886",  # 兆豐金
    "2887",  # 台新金
    # --- 00981A ETF ---
    "00981A",
]

# 去重並排序
WATCHLIST = sorted(list(set(WATCHLIST)))

# === 00981A 成分股 (群益台灣精選高息) ===
# 資料來源: https://www.pocket.tw/etf/tw/00981A/fundholding
# 資料日: 2026-05-12
ETF_00981A_HOLDINGS = [
    "2330",  # 台積電 9.63%
    "2383",  # 台光電 8.27%
    "2454",  # 聯發科 6.05%
    "2345",  # 智邦 5.76%
    "2308",  # 台達電 5.29%
    "6669",  # 緯穎 4.87%
    "3665",  # 貿聯-KY 4.78%
    "2368",  # 金像電 4.21%
    "8046",  # 南電 4.17%
    "6223",  # 旺矽 4.18%
    "3017",  # 奇鋐 4.13%
    "3037",  # 欣興 3.47%
    "3653",  # 健策 3.26%
    "5274",  # 信驊 3.19%
    "3711",  # 日月光投控 3.05%
    "2327",  # 國巨 2.65%
    "6274",  # 台燿 2.21%
    "2303",  # 聯電 1.78%
    "6515",  # 穎崴 1.61%
    "3443",  # 創意 1.56%
    "6510",  # 精測 1.32%
    "6805",  # 富世達 1.19%
    "8210",  # 勤誠 1.12%
    "2449",  # 京元電子 1.42%
    "3264",  # 欣銓 0.76%
    "5439",  # 高技 0.45%
    "2357",  # 華碩 0.49%
    "6187",  # 萬潤 0.55%
    "2404",  # 漢唐 0.51%
    "8996",  # 高力 0.40%
    "4966",  # 譜瑞-KY 0.29%
    "1590",  # 亞德客-KY 0.30%
    "6415",  # 矽力*-KY 0.16%
    "3008",  # 大立光 0.16%
    "2481",  # 強茂 0.15%
    "6191",  # 精成科 0.14%
    "3376",  # 新日興 0.13%
    "3036",  # 文曄 0.12%
    "8358",  # 金居 0.35%
    "2313",  # 華通 0.39%
    "2317",  # 鴻海 0.33%
    "3661",  # 世芯-KY 0.58%
    "8150",  # 南茂 0.36%
    "2002",  # 中鋼 0.03%
    "3217",  # 優群 0.06%
    "1319",  # 東陽 0.01%
    "1815",  # 富喬 0.00%
    "2439",  # 美律 0.00%
    "2337",  # 旺宏 0.00%
    "5347",  # 世界 0.00%
    "6147",  # 頎邦 0.00%
]

# === 大戶漏網之魚清單 (動態載入) ===
BIG_HOLDER_MISSED = []

def load_big_holder_missed():
    """從最新 fortune-fred 週排名載入大戶漏網之魚"""
    import json, os
    
    weekly_path = os.path.join(os.path.dirname(__file__), "..", "data", "weekly_ranking.json")
    if not os.path.exists(weekly_path):
        return []
    
    try:
        with open(weekly_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    
    # 從 thresholds 提取所有股票
    all_stocks = []
    for th_data in data.get("thresholds", {}).values():
        for s in th_data.get("stocks", []):
            all_stocks.append(s)
    
    if not all_stocks:
        return []
    
    # 去重
    seen = set()
    unique = []
    for s in all_stocks:
        code = str(s.get("code", "")).lstrip("0") or "0"
        if code not in seen:
            seen.add(code)
            # 解析 big_holder_pct (可能是字符串如 "50.96%")
            pct_str = str(s.get("big_holder_pct", "0%")).replace("%", "")
            try:
                pct = float(pct_str)
            except:
                pct = 0.0
            unique.append({"code": code, "name": s.get("name", ""), "pct": pct})
    
    # 過濾掉已在 WATCHLIST 的，按大戶%排序取前 15
    watchlist_set = set(WATCHLIST)
    candidates = [s for s in unique if s["code"] not in watchlist_set]
    candidates.sort(key=lambda x: x["pct"], reverse=True)
    return [s["code"] for s in candidates[:15]]

BIG_HOLDER_MISSED = load_big_holder_missed()

# === 00981A 成分股 (動態載入) ===
ETF_00981A_HOLDINGS = []

def load_etf_00981a():
    """嘗試從 pocket.tw 抓取 00981A 最新成分股"""
    import urllib.request, re, ssl
    
    url = "https://www.pocket.tw/etf/tw/00981A/fundholding"
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
            html = response.read().decode("utf-8")
        
        # 提取股票代號 (4-6 位數字)
        tickers = re.findall(r'>(\d{4,6})<', html)
        return list(dict.fromkeys(tickers))  # 去重
    except Exception as e:
        print(f"[WARN] Failed to fetch 00981A holdings: {e}")
        return []

# 嘗試動態載入，失敗則用備份列表
_etf_dynamic = load_etf_00981a()
if _etf_dynamic:
    ETF_00981A_HOLDINGS = _etf_dynamic
    print(f"[INFO] 00981A loaded dynamically: {len(ETF_00981A_HOLDINGS)} stocks")
else:
    # 備份列表 (2026-05-12)
    ETF_00981A_HOLDINGS = [
        "2330", "2383", "2454", "2345", "2308", "6669", "3665", "2368", "8046", "6223",
        "3017", "3037", "3653", "5274", "3711", "2327", "6274", "2303", "6515", "3443",
        "6510", "6805", "8210", "2449", "3264", "5439", "2357", "6187", "2404", "8996",
        "4966", "1590", "6415", "3008", "2481", "6191", "3376", "3036", "8358", "2313",
        "2317", "3661", "8150", "2002", "3217", "1319", "1815", "2439", "2337", "5347",
        "6147",
    ]
    print(f"[INFO] 00981A using fallback list: {len(ETF_00981A_HOLDINGS)} stocks")

# === 被動元件族群 ===
PASSIVE_COMPONENT = [
    "2327",  # 國巨
    "2478",  # 大毅
    "2492",  # 華新科
    "2472",  # 立隆電
    "6173",  # 信昌電
    "8043",  # 蜜望實
    "3090",  # 日電貿
    "3026",  # 禾伸堂
    "2375",  # 凱美
    "6207",  # 雷科
]

# === 金融股族群 ===
FINANCIAL_STOCKS = [
    "2882",  # 國泰金
    "2890",  # 永豐金
    "2881",  # 富邦金
    "2892",  # 第一金
    "2850",  # 新產
    "2885",  # 元大金
    "2880",  # 華南金
    "2883",  # 凱基金
    "2886",  # 兆豐金
    "2887",  # 台新金
]

# === 每周大戶400 TOP25（動態載入）===
def load_big_holder_top25():
    """從 weekly_ranking.json 載入最新大戶 TOP25"""
    import json
    import os
    
    weekly_path = os.path.join(os.path.dirname(__file__), "..", "data", "weekly_ranking.json")
    if not os.path.exists(weekly_path):
        return []
    
    try:
        with open(weekly_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    
    # 從 thresholds 提取所有股票
    all_stocks = []
    for th_data in data.get("thresholds", {}).values():
        for s in th_data.get("stocks", []):
            all_stocks.append(s)
    
    if not all_stocks:
        return []
    
    # 去重
    seen = set()
    unique = []
    for s in all_stocks:
        code = str(s.get("code", "")).lstrip("0") or "0"
        if code not in seen:
            seen.add(code)
            pct_str = str(s.get("big_holder_pct", "0%")).replace("%", "")
            try:
                pct = float(pct_str)
            except:
                pct = 0.0
            unique.append({"code": code, "pct": pct})
    
    # 按大戶%排序取前25
    sorted_stocks = sorted(unique, key=lambda x: x["pct"], reverse=True)
    return [s["code"] for s in sorted_stocks[:25]]

BIG_HOLDER_TOP25 = load_big_holder_top25()
print(f"[INFO] Big holder TOP25 loaded: {len(BIG_HOLDER_TOP25)} stocks")

# 將 TOP25 自動合併到 WATCHLIST
WATCHLIST = list(dict.fromkeys(WATCHLIST + BIG_HOLDER_TOP25))
print(f"[INFO] Watchlist after TOP25 merge: {len(WATCHLIST)} stocks")

# === 族群映射（供前端計算各族群情緒）===
SECTOR_MAP = {
    "semiconductor": "半導體",
    "ai-server": "AI伺服器",
    "passive-component": "被動元件",
    "pcb": "PCB",
    "memory": "記憶體",
    "display": "面板",
    "financial": "金融",
    "sic-power": "SiC功率",
    "biotech": "生技",
    "aerospace-defense": "航太軍工",
    "satellite": "衛星",
}

# 個股→族群對照（key: stock_id, value: sector_key）
STOCK_SECTOR = {
    # 半導體
    "2330": "semiconductor", "2317": "semiconductor", "2454": "semiconductor",
    "2303": "semiconductor", "2337": "semiconductor", "2344": "semiconductor",
    "2345": "semiconductor", "2357": "semiconductor", "2404": "semiconductor",
    "2428": "semiconductor", "2439": "semiconductor", "2449": "semiconductor",
    "2481": "semiconductor", "3006": "semiconductor", "3036": "semiconductor",
    "3231": "semiconductor", "3264": "semiconductor", "3443": "semiconductor",
    "3535": "semiconductor", "3653": "semiconductor", "3661": "semiconductor",
    "3665": "semiconductor", "3680": "semiconductor", "3711": "semiconductor",
    "4919": "semiconductor", "4961": "semiconductor", "4966": "semiconductor",
    "4967": "semiconductor", "5347": "semiconductor", "5439": "semiconductor",
    "6104": "semiconductor", "6155": "semiconductor", "6182": "semiconductor",
    "6187": "semiconductor", "6191": "semiconductor", "6207": "semiconductor",
    "6223": "semiconductor", "6239": "semiconductor", "6261": "semiconductor",
    "6271": "semiconductor", "6415": "semiconductor", "6510": "semiconductor",
    "6515": "semiconductor", "6669": "semiconductor", "6770": "semiconductor",
    "6805": "semiconductor", "8040": "semiconductor", "8042": "semiconductor",
    "8091": "semiconductor", "8150": "semiconductor", "8210": "semiconductor",
    "8289": "semiconductor", "8358": "semiconductor", "8996": "semiconductor",
    "1590": "semiconductor", "1727": "semiconductor", "2002": "semiconductor",
    "2301": "semiconductor", "2308": "semiconductor", "2313": "semiconductor",
    "2324": "semiconductor", "2327": "semiconductor", "2377": "semiconductor",
    "2382": "semiconductor", "2383": "semiconductor", "2408": "semiconductor",
    "2409": "semiconductor", "3016": "semiconductor", "3017": "semiconductor",
    "3037": "semiconductor", "3376": "semiconductor", "3450": "semiconductor",
    "3481": "semiconductor", "5274": "semiconductor",
    # AI伺服器
    "2324": "ai-server", "2356": "ai-server", "2376": "ai-server",
    "2382": "ai-server", "3231": "ai-server", "3661": "ai-server",
    "6669": "ai-server",
    # 被動元件
    "2327": "passive-component", "2472": "passive-component", "2478": "passive-component",
    "2492": "passive-component", "6173": "passive-component", "8042": "passive-component",
    "8043": "passive-component", "1815": "passive-component", "3026": "passive-component",
    "2375": "passive-component", "3090": "passive-component", "6207": "passive-component",
    "6173": "passive-component", "8358": "passive-component",
    # PCB
    "2313": "pcb", "2355": "pcb", "2368": "pcb", "2383": "pcb",
    "3037": "pcb", "6213": "pcb", "6274": "pcb", "8046": "pcb",
    # 記憶體
    "2344": "memory", "2408": "memory", "3006": "memory", "6770": "memory",
    # 面板
    "2409": "display", "3481": "display",
    # 金融
    "2881": "financial", "2882": "financial", "2850": "financial",
    "2880": "financial", "2883": "financial", "2885": "financial",
    "2886": "financial", "2887": "financial", "2890": "financial",
    "2892": "financial",
    # SiC功率
    "3707": "sic-power", "8261": "sic-power",
    # 航太軍工
    "2634": "aerospace-defense",
    # 衛星
    "6821": "satellite",
}

# === 輸出路徑 ===
DATA_DIR = "data"
DOCS_DIR = "docs"
