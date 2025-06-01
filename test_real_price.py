#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
真實價格測試程式
測試是否能從虎航網站獲取真實的機票價格
"""

from chrome_fix_scraper import FixedChromeScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_real_prices():
    """測試真實價格爬取"""
    print("🧪 開始測試真實價格爬取...")
    print("="*60)
    
    try:
        # 創建修復版爬蟲（不使用headless模式，可以看到過程）
        scraper = FixedChromeScraper(headless=False)
        
        # 搜尋台北到東京的航班
        result = scraper.search_flights(
            departure="TPE",
            arrival="NRT",
            departure_date="2025-06-07"  # 使用圖片中的日期
        )
        
        if result.flights:
            print("✅ 成功獲取真實航班資料！")
            print(f"找到 {len(result.flights)} 筆航班:")
            
            for i, flight in enumerate(result.flights, 1):
                print(f"\n  【航班 {i}】")
                print(f"  航班號碼: {flight.flight_number}")
                print(f"  出發時間: {flight.departure_time}")
                print(f"  抵達時間: {flight.arrival_time}")
                print(f"  價格: NT$ {flight.price:,.0f}" if flight.price else "價格: 未知")
                print(f"  有空位: {'是' if flight.seats_available else '否'}")
                print(f"  時段: {flight.time_slot}")
                print("-" * 40)
            
            # 檢查是否有合理的價格
            real_prices = [f.price for f in result.flights if f.price and f.price != 4200]
            if real_prices:
                print(f"\n🎉 發現真實價格! 價格範圍: NT$ {min(real_prices):,.0f} - NT$ {max(real_prices):,.0f}")
            else:
                print("\n⚠️  所有價格都是4200，可能還在使用模擬資料")
                
        else:
            print("❌ 沒有找到任何航班資料")
            if result.errors:
                print("錯誤訊息:")
                for error in result.errors:
                    print(f"  - {error}")
        
        return len(result.flights) > 0
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        return False

if __name__ == "__main__":
    print("🛫 虎航真實價格測試")
    print("此程式會打開瀏覽器視窗，讓您看到爬取過程")
    print("="*60)
    
    success = test_real_prices()
    
    if success:
        print("\n🎉 測試完成！請檢查上方顯示的價格是否與網站一致")
    else:
        print("\n💡 如果測試失敗，可能的原因:")
        print("1. 網站結構發生變化")
        print("2. 需要調整選擇器")
        print("3. 網站有反爬蟲機制") 