#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Safari瀏覽器測試程式
用來驗證Safari WebDriver是否正常工作
"""

from safari_scraper import SafariTigerairScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_safari():
    """測試Safari瀏覽器是否正常工作"""
    print("🧪 開始測試Safari瀏覽器...")
    
    try:
        # 創建Safari爬蟲
        scraper = SafariTigerairScraper()
        
        # 嘗試搜尋一個簡單的航班
        result = scraper.search_flights(
            departure="TPE",
            arrival="NRT",
            departure_date="2025-06-10"
        )
        
        if result.flights:
            print("✅ Safari測試成功！")
            print(f"找到 {len(result.flights)} 筆航班資料")
            for flight in result.flights:
                print(f"  - {flight.flight_number}: {flight.departure_time} -> {flight.arrival_time}, NT$ {flight.price}")
        else:
            print("⚠️  Safari啟動成功，但沒有找到航班資料")
        
        return True
        
    except Exception as e:
        print(f"❌ Safari測試失敗: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_safari()
    if success:
        print("\n🎉 Safari已準備就緒，您可以執行日本機票查詢了！")
        print("執行指令: python japan_cheapest_flights.py")
    else:
        print("\n💡 建議安裝Chrome瀏覽器:")
        print("brew install --cask google-chrome") 