#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日本最便宜機票查詢範例
使用範例：查詢未來30天到日本東京和沖繩最便宜的五天四夜來回機票
"""

from japan_cheapest_flights import JapanCheapestFlightFinder

def example_basic_search():
    """基本搜尋範例"""
    print("🔍 基本搜尋範例 - 查詢未來30天最便宜的10個旅行組合")
    print("="*60)
    
    # 建立查詢器（使用無頭模式）
    finder = JapanCheapestFlightFinder(headless=True)
    
    # 查詢最便宜的旅行組合
    cheapest_trips = finder.find_cheapest_trips(
        days_ahead=30,      # 搜尋未來30天
        max_results=10      # 返回前10個最便宜的組合
    )
    
    # 顯示結果
    finder.display_results(cheapest_trips)
    
    # 儲存結果
    finder.save_results(cheapest_trips)

def example_short_term_search():
    """短期搜尋範例"""
    print("\n\n🔍 短期搜尋範例 - 查詢未來7天最便宜的5個旅行組合")
    print("="*60)
    
    # 建立查詢器（顯示瀏覽器視窗，方便除錯）
    finder = JapanCheapestFlightFinder(headless=False)
    
    # 查詢最便宜的旅行組合
    cheapest_trips = finder.find_cheapest_trips(
        days_ahead=7,       # 搜尋未來7天
        max_results=5       # 返回前5個最便宜的組合
    )
    
    # 顯示結果
    finder.display_results(cheapest_trips)

def example_specific_route():
    """特定航線搜尋範例"""
    print("\n\n🔍 特定航線搜尋範例 - 只搜尋東京航線")
    print("="*60)
    
    # 建立查詢器
    finder = JapanCheapestFlightFinder(headless=True)
    
    # 修改目標航線，只搜尋東京
    finder.target_routes = {
        "TPE_NRT": {"from": "TPE", "to": "NRT", "route_name": "台北-東京成田"}
    }
    
    # 查詢最便宜的旅行組合
    cheapest_trips = finder.find_cheapest_trips(
        days_ahead=14,      # 搜尋未來14天
        max_results=5       # 返回前5個最便宜的組合
    )
    
    # 顯示結果
    finder.display_results(cheapest_trips)

if __name__ == "__main__":
    print("🛫 日本最便宜機票查詢範例")
    print("此程式會搜尋台灣虎航到日本東京和沖繩的最便宜五天四夜來回機票")
    print("="*80)
    
    try:
        # 執行基本搜尋範例
        example_basic_search()
        
        # 如果要執行其他範例，請取消下面的註解
        # example_short_term_search()
        # example_specific_route()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  程式被使用者中斷")
    except Exception as e:
        print(f"\n❌ 程式執行時發生錯誤: {str(e)}")
        print("請檢查網路連線和瀏覽器設定") 