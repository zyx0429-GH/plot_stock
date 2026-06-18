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
    "ic-design": "IC設計",
    "foundry": "晶圓代工",
    "packaging": "封測",
    "memory": "記憶體",
    "semi-equip": "半導體設備/材料",
    "ai-server": "AI伺服器",
    "pcb": "PCB",
    "passive-component": "被動元件",
    "thermal": "散熱/電源/機殼",
    "opto": "光電/光通訊",
    "display": "面板",
    "connector": "連接器/網通",
    "brand": "品牌/組裝",
    "financial": "金融",
    "steel-chemical": "鋼鐵/塑化/傳產",
    "auto": "汽車零組件",
    "others": "其他",
}

# 個股→族群對照（key: stock_id, value: sector_key）
# 注意：每檔股票只歸一類，後面覆蓋前面
STOCK_SECTOR = {
    # === IC設計 ===
    "2454": "ic-design",   # 聯發科
    "3661": "ic-design",   # 世芯-KY
    "3443": "ic-design",   # 創意
    "5274": "ic-design",   # 信驊
    "4966": "ic-design",   # 譜瑞-KY
    "4961": "ic-design",   # 天鈺
    "6415": "ic-design",   # 矽力*-KY
    "6104": "ic-design",   # 創惟
    "6462": "ic-design",   # 神盾
    "6485": "ic-design",   # 點序
    "4919": "ic-design",   # 新唐
    "3663": "ic-design",   # 鑫科
    "3675": "ic-design",   # 德微

    # === 晶圓代工 ===
    "2330": "foundry",     # 台積電
    "2303": "foundry",     # 聯電
    "5347": "foundry",     # 世界
    "6770": "foundry",     # 力積電

    # === 封測 ===
    "3711": "packaging",   # 日月光投控
    "2449": "packaging",   # 京元電子
    "8150": "packaging",   # 南茂
    "3264": "packaging",   # 欣銓
    "6147": "packaging",   # 頎邦
    "6257": "packaging",   # 矽格
    "6239": "packaging",   # 力成
    "6191": "packaging",   # 精成科
    "6261": "packaging",   # 久元

    # === 記憶體 ===
    "2408": "memory",      # 南亞科
    "2344": "memory",      # 華邦電
    "2337": "memory",      # 旺宏
    "3006": "memory",      # 晶豪科
    "4967": "memory",      # 十銓

    # === 半導體設備/材料 ===
    "3680": "semi-equip",  # 家登
    "6187": "semi-equip",  # 萬潤
    "6223": "semi-equip",  # 旺矽
    "2404": "semi-equip",  # 漢唐
    "6510": "semi-equip",  # 精測
    "6515": "semi-equip",  # 穎崴
    "3016": "semi-equip",  # 嘉晶
    "6182": "semi-equip",  # 合晶

    # === AI伺服器 ===
    "2382": "ai-server",   # 廣達
    "6669": "ai-server",   # 緯穎
    "2376": "ai-server",   # 技嘉
    "2356": "ai-server",   # 英業達
    "2324": "ai-server",   # 仁寶

    # === PCB ===
    "2313": "pcb",         # 華通
    "2368": "pcb",         # 金像電
    "2383": "pcb",         # 台光電
    "3037": "pcb",         # 欣興
    "6213": "pcb",         # 聯茂
    "6274": "pcb",         # 台燿
    "8046": "pcb",         # 南電
    "5439": "pcb",         # 高技
    "2355": "pcb",         # 敬鵬

    # === 被動元件 ===
    "2327": "passive-component",  # 國巨
    "2492": "passive-component",  # 華新科
    "6173": "passive-component",  # 信昌電
    "8042": "passive-component",  # 金山電
    "8043": "passive-component",  # 蜜望實
    "1815": "passive-component",  # 富喬
    "3026": "passive-component",  # 禾伸堂
    "2375": "passive-component",  # 凱美
    "3090": "passive-component",  # 日電貿
    "6207": "passive-component",  # 雷科
    "8358": "passive-component",  # 金居
    "3236": "passive-component",  # 千如
    "3624": "passive-component",  # 光頡

    # === 散熱/電源/機殼 ===
    "3017": "thermal",     # 奇鋐
    "6805": "thermal",     # 富世達
    "8210": "thermal",     # 勤誠
    "8996": "thermal",     # 高力
    "2301": "thermal",     # 光寶科
    "2308": "thermal",     # 台達電
    "6271": "thermal",     # 同欣電
    "2428": "thermal",     # 興勤
    "3653": "thermal",     # 健策

    # === 光電/光通訊 ===
    "3450": "opto",        # 聯鈞
    "3008": "opto",        # 大立光
    "2439": "opto",        # 美律

    # === 面板 ===
    "2409": "display",     # 友達
    "3481": "display",     # 群創

    # === 連接器/網通 ===
    "3665": "connector",   # 貿聯-KY
    "3376": "connector",   # 新日興
    "3217": "connector",   # 優群
    "2345": "connector",   # 智邦
    "3533": "connector",   # 嘉澤
    "6284": "connector",   # 佳邦

    # === 品牌/組裝 ===
    "2357": "brand",       # 華碩
    "2377": "brand",       # 微星
    "2317": "brand",       # 鴻海

    # === 金融 ===
    "2881": "financial",   # 富邦金
    "2882": "financial",   # 國泰金
    "2883": "financial",   # 凱基金
    "2885": "financial",   # 元大金
    "2886": "financial",   # 兆豐金
    "2887": "financial",   # 台新新光金
    "2890": "financial",   # 永豐金
    "2892": "financial",   # 第一金
    "2880": "financial",   # 華南金
    "2850": "financial",   # 新產

    # === 鋼鐵/塑化/傳產 ===
    "2002": "steel-chemical",  # 中鋼
    "1301": "steel-chemical",  # 台塑
    "1605": "steel-chemical",  # 華新
    "1216": "steel-chemical",  # 統一
    "2023": "steel-chemical",  # 燁輝
    "2030": "steel-chemical",  # 彰源
    "2031": "steel-chemical",  # 新光鋼
    "2032": "steel-chemical",  # 新鋼
    "2033": "steel-chemical",  # 佳大
    "2034": "steel-chemical",  # 允強
    "2025": "steel-chemical",  # 千興

    # === 汽車零組件 ===
    "1319": "auto",        # 東陽
    "1590": "auto",        # 亞德客-KY
    "2351": "auto",        # 順德

    # === 其他（電子零組件、小股、ETF、生技等）===
    "3036": "others",      # 文曄
    "3537": "others",      # 堡達
    "3285": "others",      # 微端
    "8289": "others",      # 泰藝
    "8040": "others",      # 九暘
    "8096": "others",      # 擎亞
    "8091": "others",      # 翔名
    "3498": "others",      # 陽程
    "3357": "others",      # 臺慶科
    "3709": "others",      # 鑫聯大投控
    "4556": "others",      # 旭然
    "5291": "others",      # 邑昇
    "5328": "others",      # 華容
    "5425": "others",      # 台半
    "6127": "others",      # 九豪
    "6727": "others",      # 亞泰金屬
    "2491": "others",      # 吉祥全
    "3042": "others",      # 晶技
    "3005": "others",      # 神基
    "6177": "others",      # 達麗
    "2497": "others",      # 怡利電
    "7738": "others",      # 東聯互動
    "8472": "others",      # 夠麻吉
    "5871": "others",      # 中租-KY
    "8454": "others",      # 富邦媒
    "2501": "others",      # 國建
    "8473": "others",      # 山林水
    "5534": "others",      # 長虹
    "8476": "others",      # 台境*
    "6890": "others",      # 來億-KY
    "6924": "others",      # 榮惠-KY創
    "2597": "others",      # 潤弘
    "6550": "others",      # 北極星藥業-KY
    "2481": "others",      # 強茂
    "0050": "others",      # 元大台灣50
    "0056": "others",      # 元大高股息
    "00981A": "others",    # 群益台灣精選高息
    "6831": "others",      # 邁科
    "3356": "others",      # 奇偶
    "2352": "others",      # 佳世達
    "8182": "others",      # 加高
    "9941": "others",      # 裕融
}

# === 輸出路徑 ===
DATA_DIR = "data"
DOCS_DIR = "docs"
