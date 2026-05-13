# 🔥 智董籌碼選股站

> 自動化台股籌碼監控 + 選股儀表板，零伺服器成本，每日自動更新

## 📊 功能特色

| 功能 | 說明 |
|------|------|
| **籌碼散點圖** | 大戶持股% vs 週增減，一眼看出主力動向 |
| **外資連買榜** | 連續 3 天淨買超個股清單 |
| **大戶排名** | 400張以上大戶持股排名，可調整顯示數量與門檻 |
| **技術面篩選** | 20MA / 60MA / RSI / 多頭排列判斷 |
| **融資融券監控** | 券資比 + 融資券異常變化警示 |
| **自選清單** | 自選股獨立監控頁面 |
| **00981A 持股** | 富邦台灣半導體 ETF 成分股籌碼監控 |
| **個股看板** | 每檔個股獨立頁面，含價格走勢 + 外資趨勢圖 |

## 🎯 選股條件

- ✅ 外資連買 **3 天**
- 👑 大戶持股 **400張以上** 排名（可切換顯示數量 + 調整%數值門檻）
- 💰 券資比建議值 **0.5**
- 📈 技術指標：**20MA / 60MA / RSI(14)**

## 🚀 快速開始

### 1. Fork 本專案

點擊右上角 `Fork` 按鈕，複製到你的 GitHub 帳號 `zyx0429-GH`

### 2. 設定 FinMind API Token

1. 到 [FinMind](https://finmindtrade.com/) 申請免費 API Key
2. 在專案 Settings → Secrets and variables → Actions → New repository secret
3. Name: `FINMIND_API_TOKEN`，Value: 你的 API Key

### 3. 啟用 GitHub Pages

1. Settings → Pages → Source: GitHub Actions
2. 系統會自動部署 `docs/` 資料夾到 Pages

### 4. 手動觸發第一次更新

1. Actions → Daily Stock Update → Run workflow
2. 等待約 5-10 分鐘（抓取約 100 檔個股資料）
3. 完成後訪問 `https://zyx0429-GH.github.io/plot_stock/`

### 5. 自動排程

已設定週一至週五早上 6:00 (UTC) 自動更新，無需人工介入。

## 📁 專案結構

```
plot_stock/
├── .github/workflows/daily_update.yml   # GitHub Actions 排程
├── scripts/
│   ├── config.py                         # 設定檔（選股條件、清單）
│   ├── data_fetcher.py                   # 資料抓取（FinMind + Yahoo）
│   ├── stock_screener.py                 # 選股邏輯引擎
│   └── generate_html.py                  # 靜態頁面生成器
├── docs/                                 # 輸出網站（GitHub Pages 來源）
│   ├── index.html                        # 首頁儀表板
│   ├── watchlist.html                    # 自選清單
│   ├── etf_00981a.html                   # 00981A 持股明細
│   ├── stock_XXXX.html                   # 個股看板（自動生成）
│   ├── css/style.css                     # 主題樣式
│   └── js/app.js                         # 前端互動
├── data/                                 # 原始資料 JSON
│   ├── raw_data.json
│   └── screened_data.json
├── main.py                               # 本地執行入口
└── requirements.txt                      # Python 依賴
```

## 🛠️ 本地開發

```bash
# 1. Clone 專案
git clone https://github.com/zyx0429-GH/plot_stock.git
cd plot_stock

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 設定 API Token（可選，沒有則技術指標仍可用）
export FINMIND_API_TOKEN="your_token_here"

# 4. 執行完整流程
python main.py

# 5. 預覽網頁
open docs/index.html
```

## ⚙️ 自訂設定

修改 `scripts/config.py`：

```python
# 選股條件
SCREEN_CONFIG = {
    "foreign_buy_days": 3,        # 外資連買天數
    "big_holder_min_shares": 400,  # 大戶門檻（張）
    "margin_ratio_threshold": 0.5,  # 券資比建議值
}

# 自選清單
WATCHLIST = ["2330", "2317", ...]

# 00981A 成分股
ETF_00981A_HOLDINGS = ["2330", "2454", ...]
```

## 📡 資料來源

| 來源 | 資料類型 |
|------|----------|
| [FinMind](https://finmindtrade.com/) | 外資買賣超、融資融券、股權分散表 |
| [Yahoo Finance](https://finance.yahoo.com/) | 股價、技術指標（MA、RSI） |
| 台灣證交所 | 開放資料補充 |

## ⚠️ 免責聲明

本專案僅供研究參考，不構成任何投資建議。股市有風險，投資需謹慎。

## 📜 License

MIT License
