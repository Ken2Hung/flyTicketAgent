import os
from datetime import datetime, timedelta

class TigerairConfig:
    """虎航爬蟲配置類別"""
    
    # 虎航官網基本URL
    BASE_URL = "https://www.tigerairtw.com"
    SEARCH_URL = "https://www.tigerairtw.com/zh-tw/book/select-flight"
    
    # 台灣到日本的主要航線
    ROUTES = {
        "TPE_NRT": {"from": "TPE", "to": "NRT", "route_name": "台北-東京成田"},
        "TPE_KIX": {"from": "TPE", "to": "KIX", "route_name": "台北-大阪關西"},
        "TPE_FUK": {"from": "TPE", "to": "FUK", "route_name": "台北-福岡"},
        "TPE_OKA": {"from": "TPE", "to": "OKA", "route_name": "台北-沖繩那霸"},
        "KHH_NRT": {"from": "KHH", "to": "NRT", "route_name": "高雄-東京成田"},
        "KHH_KIX": {"from": "KHH", "to": "KIX", "route_name": "高雄-大阪關西"},
        "TSA": {"from": "TSA", "to": "NRT", "route_name": "台北松山-東京成田"}
    }
    
    # 請求頭設定
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Selenium配置
    SELENIUM_TIMEOUT = 10
    IMPLICIT_WAIT = 5
    
    # 重試設定
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    # 資料儲存設定
    OUTPUT_DIR = "flight_data"
    CSV_FILENAME = "tigerair_flights_{date}.csv"
    JSON_FILENAME = "tigerair_flights_{date}.json"
    
    @staticmethod
    def get_default_search_dates():
        """取得預設搜尋日期範圍（未來30天）"""
        today = datetime.now().date()
        dates = []
        for i in range(1, 31):  # 未來30天
            search_date = today + timedelta(days=i)
            dates.append(search_date.strftime("%Y-%m-%d"))
        return dates
    
    @staticmethod
    def get_time_slots():
        """定義時間區間"""
        return {
            "早班": ("00:00", "06:00"),
            "上午": ("06:00", "12:00"), 
            "下午": ("12:00", "18:00"),
            "晚班": ("18:00", "23:59")
        } 