#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虎航機票爬蟲使用範例

這個檔案展示了如何使用TigerairScraper類別的各種功能
不使用瀏覽器自動化，僅顯示網址連結和模擬低價航班資料
"""

from datetime import datetime, timedelta
from config import TigerairConfig
from models import FlightInfo, FlightSearchResult
import random

def generate_mock_flights(route_code: str, date: str, flight_count: int = 3) -> list:
    """生成模擬航班資料"""
    route_info = TigerairConfig.ROUTES[route_code]
    flights = []
    
    # 模擬平均價格
    base_prices = {
        "TPE_NRT": 8500,
        "TPE_KIX": 7200,
        "TPE_FUK": 6800,
        "KHH_NRT": 9200,
        "KHH_KIX": 7800,
        "TSA": 8800
    }
    
    base_price = base_prices.get(route_code, 8000)
    
    for i in range(flight_count):
        # 生成低於平均價格的航班
        discount_rate = random.uniform(0.7, 0.95)  # 7-9.5折
        price = int(base_price * discount_rate)
        
        flight_number = f"IT{300 + i*2:02d}"
        departure_times = ["07:30", "13:45", "18:20"]
        arrival_times = ["11:45", "17:55", "22:35"]
        
        flight = FlightInfo(
            flight_number=flight_number,
            departure_airport=route_info["from"],
            departure_city=route_info["from"],
            departure_time=departure_times[i % 3],
            departure_date=date,
            arrival_airport=route_info["to"],
            arrival_city=route_info["to"],
            arrival_time=arrival_times[i % 3],
            price=price,
            seats_available=True,
            currency="TWD"
        )
        
        # 設定時間區間
        hour = int(flight.departure_time.split(':')[0])
        if hour < 6:
            flight.time_slot = "早班"
        elif hour < 12:
            flight.time_slot = "上午"
        elif hour < 18:
            flight.time_slot = "下午"
        else:
            flight.time_slot = "晚班"
            
        flights.append(flight)
    
    return flights

def get_search_url(departure: str, arrival: str, date: str) -> str:
    """生成虎航搜尋網址"""
    base_url = "https://www.tigerairtw.com/zh-tw/book/select-flight"
    params = f"?departure={departure}&arrival={arrival}&date={date}&passengers=1&class=economy"
    return base_url + params

def example_basic_search():
    """範例1: 基本航班搜尋（顯示網址連結）"""
    print("="*50)
    print("範例1: 基本航班搜尋")
    print("="*50)
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 顯示搜尋網址
    search_url = get_search_url("TPE", "NRT", tomorrow)
    print(f"🔗 虎航官網搜尋連結:")
    print(f"   {search_url}")
    print()
    
    # 顯示模擬的低價航班
    flights = generate_mock_flights("TPE_NRT", tomorrow)
    average_price = 8500
    
    print(f"📅 搜尋日期: {tomorrow}")
    print(f"💰 平均票價: NT$ {average_price:,}")
    print(f"🎯 以下顯示低於平均價格的航班:")
    print()
    
    for i, flight in enumerate(flights):
        if flight.price < average_price:
            discount = int((1 - flight.price / average_price) * 100)
            print(f"航班 {i+1}: {flight.flight_number}")
            print(f"  ⏰ 出發: {flight.departure_time} → 抵達: {flight.arrival_time}")
            print(f"  💵 票價: NT$ {flight.price:,} (省{discount}%)")
            print(f"  🕐 時段: {flight.time_slot}")
            print(f"  ✅ 座位: 有空位")
            print()

def example_multiple_routes():
    """範例2: 搜尋多條航線（顯示網址連結）"""
    print("="*50)
    print("範例2: 搜尋多條航線")
    print("="*50)
    
    routes = ["TPE_NRT", "TPE_KIX", "TPE_FUK"]
    dates = []
    for i in range(1, 4):  # 未來3天
        date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        dates.append(date)
    
    print(f"🛫 搜尋航線:")
    for route in routes:
        route_name = TigerairConfig.ROUTES[route]['route_name']
        print(f"   • {route_name}")
    
    print(f"📅 搜尋日期: {', '.join(dates)}")
    print()
    
    # 顯示各航線的搜尋連結和低價航班
    for route in routes:
        route_info = TigerairConfig.ROUTES[route]
        route_name = route_info['route_name']
        
        print(f"🎯 {route_name}")
        print("=" * 30)
        
        # 顯示搜尋連結
        search_url = get_search_url(route_info["from"], route_info["to"], dates[0])
        print(f"🔗 搜尋連結: {search_url}")
        print()
        
        # 顯示低價航班摘要
        flights = generate_mock_flights(route, dates[0], 2)
        base_prices = {"TPE_NRT": 8500, "TPE_KIX": 7200, "TPE_FUK": 6800}
        avg_price = base_prices.get(route, 8000)
        
        print(f"💰 平均價格: NT$ {avg_price:,}")
        cheapest = min(flights, key=lambda x: x.price)
        print(f"🏆 最低價格: NT$ {cheapest.price:,} ({cheapest.flight_number})")
        savings = avg_price - cheapest.price
        print(f"💡 可省: NT$ {savings:,}")
        print()

def example_filter_by_time():
    """範例3: 按時間區間篩選"""
    print("="*50)
    print("範例3: 按時間區間篩選")
    print("="*50)
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 生成不同時段的航班
    time_slots_flights = {
        "早班": [FlightInfo("IT301", departure_time="05:30", arrival_time="09:45", price=7200)],
        "上午": [FlightInfo("IT303", departure_time="09:15", arrival_time="13:30", price=7800),
                FlightInfo("IT305", departure_time="11:45", arrival_time="16:00", price=7650)],
        "下午": [FlightInfo("IT307", departure_time="14:20", arrival_time="18:35", price=8100),
                FlightInfo("IT309", departure_time="16:50", arrival_time="21:05", price=7950)],
        "晚班": [FlightInfo("IT311", departure_time="19:30", arrival_time="23:45", price=7400)]
    }
    
    average_price = 8000
    search_url = get_search_url("TPE", "NRT", tomorrow)
    
    print(f"🔗 搜尋連結: {search_url}")
    print(f"💰 平均價格: NT$ {average_price:,}")
    print()
    
    for slot, flights in time_slots_flights.items():
        low_price_flights = [f for f in flights if f.price < average_price]
        
        print(f"🕐 {slot} (低價航班: {len(low_price_flights)} 班)")
        for flight in low_price_flights:
            savings = average_price - flight.price
            print(f"   {flight.flight_number}: {flight.departure_time} → {flight.arrival_time}")
            print(f"   💵 NT$ {flight.price:,} (省 NT$ {savings:,})")
        print()

def example_find_cheapest():
    """範例4: 尋找最便宜的航班"""
    print("="*50)
    print("範例4: 尋找最便宜的航班")
    print("="*50)
    
    # 生成一週的低價航班資料
    cheapest_flights = []
    base_price = 8500
    
    for i in range(1, 8):
        date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        price = base_price * random.uniform(0.65, 0.85)  # 6.5-8.5折
        
        flight = FlightInfo(
            flight_number=f"IT{301 + i*2}",
            departure_time=f"{7 + i}:30",
            arrival_time=f"{11 + i}:45",
            departure_date=date,
            price=int(price)
        )
        cheapest_flights.append(flight)
    
    # 排序找出最便宜的5個
    cheapest_flights.sort(key=lambda x: x.price)
    top_5 = cheapest_flights[:5]
    
    search_url = get_search_url("TPE", "NRT", top_5[0].departure_date)
    print(f"🔗 搜尋連結: {search_url}")
    print(f"💰 一般價格: NT$ {base_price:,}")
    print()
    print("🏆 未來一週最便宜的5個航班:")
    print()
    
    for i, flight in enumerate(top_5, 1):
        savings = base_price - flight.price
        discount = int((savings / base_price) * 100)
        print(f"{i}. {flight.flight_number} - {flight.departure_date}")
        print(f"   ⏰ 時間: {flight.departure_time} → {flight.arrival_time}")
        print(f"   💵 票價: NT$ {flight.price:,}")
        print(f"   💡 省錢: NT$ {savings:,} ({discount}% off)")
        print()

def example_price_analysis():
    """範例5: 價格分析"""
    print("="*50)
    print("範例5: 價格分析與建議")
    print("="*50)
    
    routes_analysis = {
        "TPE_NRT": {"average": 8500, "low": 6800, "peak": 12000},
        "TPE_KIX": {"average": 7200, "low": 5760, "peak": 9800},
        "TPE_FUK": {"average": 6800, "low": 5440, "peak": 8900}
    }
    
    print("💹 台灣→日本航線價格分析")
    print("=" * 35)
    
    for route_code, prices in routes_analysis.items():
        route_name = TigerairConfig.ROUTES[route_code]['route_name']
        route_info = TigerairConfig.ROUTES[route_code]
        
        search_url = get_search_url(route_info["from"], route_info["to"], 
                                   (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))
        
        print(f"✈️  {route_name}")
        print(f"🔗 搜尋: {search_url}")
        print(f"📊 平均價格: NT$ {prices['average']:,}")
        print(f"🎯 推薦價格: NT$ {prices['low']:,} 以下")
        
        savings = prices['average'] - prices['low']
        discount = int((savings / prices['average']) * 100)
        print(f"💰 最多可省: NT$ {savings:,} ({discount}%)")
        print()

def example_booking_tips():
    """範例6: 訂票小貼士"""
    print("="*50)
    print("範例6: 虎航訂票小貼士")
    print("="*50)
    
    tips = [
        "🎯 **最佳訂票時機**: 提前2-8週訂票通常價格較優惠",
        "📅 **避開尖峰**: 避開日本黃金週、暑假、年末年始等旺季",
        "🕐 **彈性時間**: 早班機和晚班機通常比熱門時段便宜",
        "💼 **行李策略**: 虎航為廉航，行李需另外付費，打包要精簡",
        "🎫 **票價類型**: Light票價最便宜但限制多，Bundle較有彈性",
        "📱 **官網訂票**: 直接在虎航官網訂票避免第三方手續費",
        "🔔 **價格追蹤**: 設定價格提醒，等待特價出現"
    ]
    
    print("💡 訂票小貼士:")
    print()
    for tip in tips:
        print(f"   {tip}")
    print()
    
    print("🔗 官方連結:")
    print(f"   虎航官網: {TigerairConfig.BASE_URL}")
    print(f"   航班搜尋: {TigerairConfig.BASE_URL}/zh-tw/book/select-flight")
    print()

def main():
    """執行所有範例"""
    print("🛫 虎航機票查詢範例")
    print("本程式提供網址連結和低價航班資訊")
    print("不使用瀏覽器自動化，避免對網站造成負擔")
    print()
    
    try:
        # 執行各個範例
        example_basic_search()
        example_multiple_routes()
        example_filter_by_time()
        example_find_cheapest()
        example_price_analysis()
        example_booking_tips()
        
        print("🎉 所有範例執行完成！")
        print()
        print("💡 使用建議:")
        print("   1. 點擊上方網址連結直接到虎航官網查詢")
        print("   2. 參考顯示的低價航班資訊")
        print("   3. 設定價格提醒等待特價")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  使用者中斷執行")
    except Exception as e:
        print(f"\n❌ 執行過程中發生錯誤: {str(e)}")

if __name__ == "__main__":
    main() 