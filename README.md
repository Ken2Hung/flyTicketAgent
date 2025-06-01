# 虎航機票爬蟲 (Tigerair Flight Scraper)

這是一個專門爬取台灣虎航（Tigerair Taiwan）到日本航班資訊的Python爬蟲程式。能夠獲取航班的起飛、降落時間、票價以及座位狀況等資訊。

## 功能特色

- 🛫 支援台灣到日本主要航線
- 📅 可指定特定日期或日期範圍搜尋
- 🕐 按時間區間分類航班（早班/上午/下午/晚班）
- 💰 獲取即時票價資訊
- 💺 檢查座位是否可用
- 📊 多種輸出格式（CSV、JSON）
- 🌐 提供RESTful API介面
- 📝 詳細的日誌記錄

## 支援航線

| 航線代碼 | 航線名稱 |
|---------|---------|
| TPE_NRT | 台北-東京成田 |
| TPE_KIX | 台北-大阪關西 |
| TPE_FUK | 台北-福岡 |
| TPE_OKA | 台北-沖繩那霸 |
| KHH_NRT | 高雄-東京成田 |
| KHH_KIX | 高雄-大阪關西 |
| TSA_NRT | 台北松山-東京成田 |

## 🌟 新功能：日本最便宜機票查詢

專門針對日本旅遊需求，新增了最便宜機票查詢功能，能夠：

- 🗾 專門搜尋日本東京和沖繩航線
- 🏖️ 自動計算五天四夜旅行行程
- 💰 找出最便宜的來回機票組合
- 📊 按價格排序並顯示前10名選擇
- 📅 搜尋未來30天內的所有可能日期
- 💾 自動儲存結果為CSV和JSON格式

### 使用日本最便宜機票查詢

#### 基本使用
```bash
# 直接執行主程式
python japan_cheapest_flights.py

# 或使用範例程式
python example_japan_cheapest.py
```

#### 程式碼範例
```python
from japan_cheapest_flights import JapanCheapestFlightFinder

# 建立查詢器
finder = JapanCheapestFlightFinder(headless=True)

# 查詢未來30天最便宜的10個旅行組合
cheapest_trips = finder.find_cheapest_trips(
    days_ahead=30,      # 搜尋未來30天
    max_results=10      # 返回前10個最便宜的組合
)

# 顯示結果
finder.display_results(cheapest_trips)

# 儲存結果
finder.save_results(cheapest_trips)
```

#### 自訂搜尋範圍
```python
# 只搜尋東京航線
finder.target_routes = {
    "TPE_NRT": {"from": "TPE", "to": "NRT", "route_name": "台北-東京成田"}
}

# 搜尋未來14天的前5個最便宜組合
cheapest_trips = finder.find_cheapest_trips(days_ahead=14, max_results=5)
```

### 輸出範例

程式會顯示類似以下的結果：

```
🏆 找到 10 個最便宜的五天四夜旅行組合
================================================================================

【第 1 名】台北-東京成田
📅 旅行日期: 2024-03-20 ~ 2024-03-24
💰 總價格: NT$ 8,500 (平均每天 NT$ 1,700)
✈️  去程: IT200 08:25-12:30 NT$ 4,200
✈️  回程: IT201 13:45-17:15 NT$ 4,300
--------------------------------------------------

【第 2 名】台北-沖繩那霸
📅 旅行日期: 2024-03-22 ~ 2024-03-26
💰 總價格: NT$ 9,200 (平均每天 NT$ 1,840)
✈️  去程: IT254 09:15-11:45 NT$ 4,600
✈️  回程: IT255 12:30-15:00 NT$ 4,600
--------------------------------------------------
```

## 安裝說明

### 1. 克隆專案
```bash
git clone https://github.com/your-username/flyTicketAgent.git
cd flyTicketAgent
```

### 2. 安裝Python依賴
```bash
pip install -r requirements.txt
```

### 3. 安裝Chrome瀏覽器（強烈建議）
爬蟲使用Selenium控制瀏覽器，**強烈建議安裝Chrome瀏覽器**以獲得最佳兼容性：

**為什麼選擇Chrome？**
- ✅ 跨平台支援（Windows、Mac、Linux）
- ✅ 自動化支援最穩定
- ✅ 無頭模式完善
- ✅ 不需要額外權限設定

**安裝方式：**
```bash
# 方法1: 手動下載（推薦）
# 訪問 https://www.google.com/chrome/ 下載安裝

# 方法2: 使用Homebrew（Mac）
brew install --cask google-chrome

# 方法3: 使用apt（Ubuntu/Debian）
sudo apt-get install google-chrome-stable
```

**備選方案（僅Mac）：**
如果無法安裝Chrome，可啟用Safari WebDriver：
```bash
sudo safaridriver --enable
```

## 使用方法

### 命令列介面

#### 基本用法
```bash
# 搜尋台北到東京，未來7天的航班
python main.py --route TPE_NRT --days 7

# 搜尋特定日期
python main.py --route TPE_NRT --date 2024-03-15

# 搜尋多條航線
python main.py --route TPE_NRT TPE_KIX --days 3

# 搜尋所有航線
python main.py --all-routes --days 30
```

#### 參數說明
- `--route`: 指定航線代碼
- `--all-routes`: 搜尋所有支援的航線
- `--date`: 指定搜尋日期（YYYY-MM-DD格式）
- `--days`: 搜尋未來幾天的航班
- `--format`: 輸出格式（csv/json/both）
- `--show-browser`: 顯示瀏覽器視窗（除錯用）

### API介面

#### 啟動API服務
```bash
python api.py
```

API將在 http://localhost:8000 運行，可以訪問 http://localhost:8000/docs 查看API文檔。

#### API端點

**1. 取得支援的航線**
```http
GET /routes
```

**2. 搜尋單一航線**
```http
POST /search
Content-Type: application/json

{
    "departure": "TPE",
    "arrival": "NRT", 
    "departure_date": "2024-03-15"
}
```

**3. 搜尋多條航線**
```http
POST /search/multiple
Content-Type: application/json

{
    "routes": ["TPE_NRT", "TPE_KIX"],
    "dates": ["2024-03-15", "2024-03-16"]
}
```

### 程式碼範例

```python
from tigerair_scraper import TigerairScraper
from config import TigerairConfig

# 初始化爬蟲
scraper = TigerairScraper(headless=True)

# 搜尋單一航線
result = scraper.search_flights(
    departure="TPE",
    arrival="NRT", 
    departure_date="2024-03-15"
)

# 顯示結果
for flight in result.flights:
    print(f"航班: {flight.flight_number}")
    print(f"出發: {flight.departure_time}")
    print(f"票價: NT$ {flight.price}")
    print(f"有空位: {flight.seats_available}")
    print("-" * 30)

# 搜尋多條航線
routes = ["TPE_NRT", "TPE_KIX"]
dates = ["2024-03-15", "2024-03-16"]
results = scraper.search_multiple_routes(routes, dates)

# 儲存結果
file_paths = scraper.save_results(results, output_format='both')
print(f"結果已儲存至: {file_paths}")
```

## 輸出格式

### CSV格式
輸出檔案包含以下欄位：
- flight_number: 航班號碼
- departure_time: 出發時間
- arrival_time: 抵達時間
- departure_date: 出發日期
- price: 票價
- seats_available: 是否有空位
- time_slot: 時間區間
- route: 航線代碼

### JSON格式
```json
{
    "timestamp": "20240315_143025",
    "total_flights": 12,
    "routes": {
        "TPE_NRT": {
            "flights": [...],
            "search_params": {...},
            "summary": {...}
        }
    }
}
```

## 專案結構

```
flyTicketAgent/
├── main.py              # 主程式入口
├── tigerair_scraper.py  # 爬蟲核心程式
├── config.py            # 配置檔案
├── models.py            # 資料模型
├── api.py               # FastAPI後端服務
├── requirements.txt     # Python依賴套件
├── README.md            # 專案說明
├── flight_data/         # 輸出資料目錄
└── tigerair_scraper.log # 日誌檔案
```

## 注意事項

1. **合法使用**: 請遵守網站的robots.txt和使用條款
2. **頻率限制**: 程式已內建延遲機制，避免對網站造成過大負擔
3. **資料準確性**: 爬蟲資料僅供參考，實際價格以官網為準
4. **網站變更**: 若網站結構改變，可能需要更新爬蟲程式

## 故障排除

### 常見問題

**1. Chrome瀏覽器相關錯誤**
```bash
# 解決方案：安裝Chrome瀏覽器
# macOS
brew install --cask google-chrome

# Ubuntu
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo apt-get install google-chrome-stable
```

**2. 權限錯誤**
```bash
# 確保Chrome驅動程式有執行權限
chmod +x chromedriver
```

**3. 網頁載入超時**
- 檢查網路連線
- 嘗試增加等待時間
- 使用 `--show-browser` 參數除錯

## 授權條款

此專案採用 MIT 授權條款，詳見 LICENSE 檔案。

## 貢獻指南

歡迎提交Issue和Pull Request來改善這個專案！

## 聯絡資訊

如有問題或建議，請透過以下方式聯絡：
- 提交GitHub Issue
- Email: your-email@example.com