#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速測試程式 - 真實查詢虎航精確價格
獲取實際的完整價格，而非概略價格
"""

from chrome_fix_scraper import FixedChromeScraper
from models import FlightInfo
import logging
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_precise_price_query():
    """查詢虎航精確價格"""
    print("🛫 東京五天四夜行程 - 精確價格查詢")
    print("=" * 60)
    print("📅 出發日期: 2025-06-02 (明天)")
    print("📅 回程日期: 2025-06-06") 
    print("✈️  航線: 台北桃園 ⇄ 東京成田")
    print("👥 乘客人數: 2人")
    print("🎯 目標: 獲取實際精確價格")
    print("=" * 60)
    
    try:
        scraper = FixedChromeScraper(headless=False)  # 使用可見模式方便除錯
        
        print("\n🔍 正在查詢去程航班精確價格...")
        outbound_result = scraper.search_flights(
            departure="TPE",
            arrival="NRT", 
            departure_date="2025-06-02"
        )
        
        print("🔍 正在查詢回程航班精確價格...")
        time.sleep(3)  # 給更多時間讓頁面載入
        inbound_result = scraper.search_flights(
            departure="NRT",
            arrival="TPE",
            departure_date="2025-06-06"
        )
        
        # 獲取精確價格數據
        outbound_flights = [f for f in outbound_result.get_available_flights() if f.price and f.price > 0]
        inbound_flights = [f for f in inbound_result.get_available_flights() if f.price and f.price > 0]
        
        print(f"\n📊 精確價格查詢結果:")
        print(f"• 去程航班: {len(outbound_flights)} 班找到精確價格")
        print(f"• 回程航班: {len(inbound_flights)} 班找到精確價格")
        print(f"• 查詢時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if outbound_flights:
            print(f"\n✈️  去程航班精確價格 (TPE → NRT, 6/2):")
            print("-" * 50)
            for i, flight in enumerate(outbound_flights, 1):
                print(f"【航班 {i}】{flight.flight_number}")
                if flight.departure_time:
                    print(f"  🕐 起飛: {flight.departure_time}")
                if flight.arrival_time:
                    print(f"  🕐 降落: {flight.arrival_time}")
                print(f"  💰 精確價格: NT$ {flight.price:,.0f} (單人)")
                print(f"  👥 2人價格: NT$ {flight.price * 2:,.0f}")
                print(f"  🔗 官網: https://www.tigerair.com/tw/zh/")
                print()
        else:
            print("\n❌ 去程航班未找到精確價格")
            
        if inbound_flights:
            print(f"✈️  回程航班精確價格 (NRT → TPE, 6/6):")
            print("-" * 50)
            for i, flight in enumerate(inbound_flights, 1):
                print(f"【航班 {i}】{flight.flight_number}")
                if flight.departure_time:
                    print(f"  🕐 起飛: {flight.departure_time}")
                if flight.arrival_time:
                    print(f"  🕐 降落: {flight.arrival_time}")
                print(f"  💰 精確價格: NT$ {flight.price:,.0f} (單人)")
                print(f"  👥 2人價格: NT$ {flight.price * 2:,.0f}")
                print(f"  🔗 官網: https://www.tigerair.com/tw/zh/")
                print()
        else:
            print("\n❌ 回程航班未找到精確價格")
        
        # 如果都有精確價格，進行組合分析
        if outbound_flights and inbound_flights:
            analyze_precise_combinations(outbound_flights, inbound_flights)
            return True
        else:
            print("\n⚠️  部分航班缺少精確價格")
            provide_fallback_with_manual_check()
            return False
            
    except Exception as e:
        print(f"\n❌ 精確價格查詢失敗: {str(e)}")
        logger.error(f"精確價格查詢失敗: {str(e)}")
        provide_fallback_with_manual_check()
        return False

def analyze_precise_combinations(outbound_flights, inbound_flights):
    """分析精確價格組合"""
    print("\n🎯 精確價格組合分析:")
    print("=" * 50)
    
    combinations = []
    for out_flight in outbound_flights:
        for in_flight in inbound_flights:
            total_single = out_flight.price + in_flight.price
            total_double = total_single * 2
            
            combinations.append({
                'out_flight': out_flight,
                'in_flight': in_flight,
                'total_single': total_single,
                'total_double': total_double
            })
    
    # 按價格排序
    combinations.sort(key=lambda x: x['total_double'])
    
    print("💰 精確價格排名 (2人總價):")
    for i, combo in enumerate(combinations, 1):
        out_time = f"{combo['out_flight'].departure_time or '待確認'}-{combo['out_flight'].arrival_time or '待確認'}"
        in_time = f"{combo['in_flight'].departure_time or '待確認'}-{combo['in_flight'].arrival_time or '待確認'}"
        
        print(f"\n【第 {i} 名】總價 NT$ {combo['total_double']:,} (2人)")
        print(f"  去程: {combo['out_flight'].flight_number} {out_time}")
        print(f"        NT$ {combo['out_flight'].price:,} (單人)")
        print(f"  回程: {combo['in_flight'].flight_number} {in_time}")
        print(f"        NT$ {combo['in_flight'].price:,} (單人)")
        print(f"  單人總計: NT$ {combo['total_single']:,}")
        print(f"  平均每天: NT$ {combo['total_single'] // 5:,} (單人)")
        
        if i == 1:
            print(f"  🏆 最便宜精確組合！")

def provide_fallback_with_manual_check():
    """提供手動確認方案"""
    print("\n💡 手動精確價格確認方案:")
    print("=" * 40)
    print("🔍 請手動前往虎航官網確認精確價格:")
    print()
    print("🌐 虎航官網: https://www.tigerair.com/tw/zh/booking/flight-search")
    print()
    print("📋 搜尋參數:")
    print("  • 出發地: TPE (台北桃園)")
    print("  • 目的地: NRT (東京成田)")
    print("  • 去程: 2025年6月2日")
    print("  • 回程: 2025年6月6日")
    print("  • 人數: 2位成人")
    print()
    print("📝 請記錄以下精確資訊:")
    print("  ✅ 航班號碼 (IT200, IT202, IT201, IT203)")
    print("  ✅ 起飛降落時間")
    print("  ✅ 精確票價 (非促銷價)")
    print("  ✅ 是否含稅費")
    print("  ✅ 行李額度")
    print()
    print("⏰ 最佳查詢時間:")
    print("  • 週二至週四 上午10:00-11:00")
    print("  • 避開週末和假日")

def enhanced_scraper_attempt():
    """增強版爬蟲嘗試"""
    print("\n🔧 使用增強版爬蟲技術...")
    
    try:
        # 使用更長的等待時間和多次嘗試
        scraper = FixedChromeScraper(headless=False)
        
        # 多次嘗試獲取精確價格
        for attempt in range(3):
            print(f"嘗試第 {attempt + 1} 次獲取精確價格...")
            
            result = scraper.search_flights(
                departure="TPE",
                arrival="NRT",
                departure_date="2025-06-02"
            )
            
            flights_with_price = [f for f in result.get_available_flights() if f.price and f.price > 0]
            
            if flights_with_price:
                print(f"✅ 第 {attempt + 1} 次嘗試成功，找到 {len(flights_with_price)} 個精確價格")
                return flights_with_price
            
            time.sleep(5)  # 等待更久再試
        
        print("❌ 多次嘗試後仍無法獲取精確價格")
        return []
        
    except Exception as e:
        print(f"❌ 增強版爬蟲失敗: {e}")
        return []

def test_dynamic_dropdown_interaction():
    """測試動態下拉選單互動"""
    print("🔧 測試虎航動態下拉選單互動")
    print("=" * 60)
    
    try:
        # 使用可見模式方便觀察互動過程
        scraper = FixedChromeScraper(headless=False)
        
        print("🌐 正在載入虎航網站...")
        scraper.driver = scraper._setup_chrome_driver()
        scraper.driver.get("https://www.tigerair.com/tw/zh/")
        
        # 等待頁面載入完成
        time.sleep(5)
        print("✅ 網站載入完成")
        
        print("\n📍 測試出發地下拉選單...")
        departure_success = scraper._select_dynamic_airport("TPE", is_departure=True)
        print(f"出發地設定結果: {'✅ 成功' if departure_success else '❌ 失敗'}")
        
        time.sleep(2)
        
        print("📍 測試目的地下拉選單...")
        arrival_success = scraper._select_dynamic_airport("NRT", is_departure=False)
        print(f"目的地設定結果: {'✅ 成功' if arrival_success else '❌ 失敗'}")
        
        time.sleep(2)
        
        print("📅 測試日期選擇器...")
        date_success = scraper._set_dynamic_date("2025-06-02")
        print(f"日期設定結果: {'✅ 成功' if date_success else '❌ 失敗'}")
        
        time.sleep(2)
        
        print("🔍 測試搜尋按鈕...")
        search_success = scraper._click_search_button()
        print(f"搜尋按鈕結果: {'✅ 成功' if search_success else '❌ 失敗'}")
        
        if search_success:
            print("\n⏳ 等待搜尋結果載入...")
            time.sleep(10)  # 給更多時間讓搜尋結果載入
            
            print("📊 檢查是否有搜尋結果...")
            # 檢查頁面是否有價格或航班資訊
            page_source = scraper.driver.page_source.lower()
            
            has_prices = any(keyword in page_source for keyword in ['twd', 'nt$', '價格', 'price'])
            has_flights = any(keyword in page_source for keyword in ['it200', 'it201', 'it202', 'it203', '航班'])
            has_results = any(keyword in page_source for keyword in ['搜尋結果', 'search result', '查詢結果'])
            
            print(f"發現價格資訊: {'✅' if has_prices else '❌'}")
            print(f"發現航班資訊: {'✅' if has_flights else '❌'}")
            print(f"發現搜尋結果: {'✅' if has_results else '❌'}")
            
            if has_prices or has_flights:
                print("🎯 成功觸發搜尋並獲得結果！")
                return True
            else:
                print("⚠️  搜尋似乎成功但未找到明確的結果")
                return False
        else:
            print("❌ 搜尋未能成功觸發")
            return False
            
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {str(e)}")
        return False
    finally:
        # 保持瀏覽器開啟10秒供觀察
        print("\n👁️  瀏覽器將在10秒後關閉，請觀察結果...")
        time.sleep(10)
        if hasattr(scraper, 'driver') and scraper.driver:
            scraper.driver.quit()

def main():
    """主程式 - 專注於獲取精確價格"""
    print("🎯 虎航精確價格查詢系統")
    print("專注於獲取真實完整的票價，而非概略價格")
    print("=" * 60)
    
    print("請選擇測試模式：")
    print("1. 測試動態下拉選單互動 (推薦)")
    print("2. 完整價格查詢測試")
    print("3. 增強版查詢測試")
    
    try:
        choice = input("\n請輸入選項 (1-3): ").strip()
        
        if choice == "1":
            print("\n🔧 開始測試動態下拉選單...")
            success = test_dynamic_dropdown_interaction()
            
            if success:
                print("\n✅ 動態下拉選單測試成功！")
                print("💡 這表示爬蟲能夠正確與虎航網站互動")
            else:
                print("\n❌ 動態下拉選單測試失敗")
                print("💡 需要進一步調整選擇器")
                
        elif choice == "2":
            print("\n🔍 開始完整價格查詢...")
            success = test_precise_price_query()
            
            if not success:
                print("\n🔄 嘗試增強版查詢...")
                enhanced_flights = enhanced_scraper_attempt()
                
                if enhanced_flights:
                    print("✅ 增強版查詢成功！")
                    for flight in enhanced_flights:
                        print(f"  {flight.flight_number}: NT$ {flight.price:,}")
                else:
                    print("❌ 自動查詢無法獲得精確價格")
                    print("💡 建議手動前往官網確認")
                    
        elif choice == "3":
            print("\n🔧 開始增強版查詢...")
            enhanced_flights = enhanced_scraper_attempt()
            
            if enhanced_flights:
                print("✅ 增強版查詢成功！")
                for flight in enhanced_flights:
                    print(f"  {flight.flight_number}: NT$ {flight.price:,}")
            else:
                print("❌ 增強版查詢失敗")
                
        else:
            print("❌ 無效選項，使用預設測試...")
            success = test_dynamic_dropdown_interaction()
            
    except KeyboardInterrupt:
        print("\n\n⭕ 用戶中斷執行")
    except Exception as e:
        print(f"\n❌ 執行過程發生錯誤: {e}")
        # 預設執行動態測試
        test_dynamic_dropdown_interaction()
    
    print("\n" + "=" * 60)
    print("🎯 重要提醒:")
    print("• 只有官網顯示的價格才是最終準確價格")
    print("• 動態下拉選單需要正確的互動才能觸發搜尋") 
    print("• 建議在非繁忙時段查詢以獲得更好的響應")
    print("🔗 立即前往: https://www.tigerair.com/tw/zh/")

if __name__ == "__main__":
    main() 