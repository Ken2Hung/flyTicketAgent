#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pandas as pd
import json

from tigerair_scraper import TigerairScraper
from safari_scraper import SafariTigerairScraper
from chrome_fix_scraper import FixedChromeScraper
from config import TigerairConfig
from models import FlightInfo, FlightSearchResult

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JapanCheapestFlightFinder:
    """日本最便宜機票查詢器"""
    
    def __init__(self, headless: bool = True, prefer_safari: bool = False):
        """
        初始化查詢器
        
        Args:
            headless: 是否使用無頭模式運行瀏覽器
            prefer_safari: 是否強制使用Safari（僅當Chrome不可用時使用）
        """
        # 嘗試使用修復版Chrome，如果失敗則回退到Safari
        import platform
        
        try:
            # 先嘗試使用修復版Chrome
            self.scraper = FixedChromeScraper(headless=headless)
            logger.info("🚀 使用修復版Chrome瀏覽器")
        except Exception as chrome_error:
            if platform.system() == 'Darwin':
                # 在Mac上回退到Safari
                try:
                    self.scraper = SafariTigerairScraper(headless=headless)
                    logger.info("🍎 Chrome不可用，回退到Safari瀏覽器")
                except Exception as safari_error:
                    error_msg = f"""
無法啟動任何瀏覽器:
- Chrome錯誤: {chrome_error}
- Safari錯誤: {safari_error}

解決方案:
1. 重新安裝Chrome: brew reinstall --cask google-chrome
2. 或啟用Safari WebDriver: 
   - 打開Safari > 偏好設定 > 進階 > 勾選「在選單列中顯示開發選單」
   - 開發 > 允許遠端自動化
                    """
                    raise Exception(error_msg)
            else:
                # 非Mac系統，只能使用Chrome
                raise chrome_error
        
        # 定義目標航線
        self.target_routes = {
            "TPE_NRT": {"from": "TPE", "to": "NRT", "route_name": "台北-東京成田"},
            "TPE_OKA": {"from": "TPE", "to": "OKA", "route_name": "台北-沖繩那霸"}
        }
        
        # 五天四夜行程天數
        self.trip_duration = 5
    
    def get_search_dates(self, days_ahead: int = 30) -> List[str]:
        """
        取得搜尋日期範圍
        
        Args:
            days_ahead: 未來多少天內
            
        Returns:
            List[str]: 日期字串列表
        """
        today = datetime.now().date()
        dates = []
        for i in range(1, days_ahead + 1):
            search_date = today + timedelta(days=i)
            dates.append(search_date.strftime("%Y-%m-%d"))
        return dates
    
    def calculate_return_date(self, departure_date: str) -> str:
        """
        根據出發日期計算回程日期（五天四夜）
        
        Args:
            departure_date: 出發日期 (YYYY-MM-DD)
            
        Returns:
            str: 回程日期 (YYYY-MM-DD)
        """
        departure = datetime.strptime(departure_date, "%Y-%m-%d").date()
        return_date = departure + timedelta(days=self.trip_duration - 1)
        return return_date.strftime("%Y-%m-%d")
    
    def search_round_trip_flights(self, route: str, departure_date: str) -> Tuple[Optional[FlightInfo], Optional[FlightInfo], Optional[float]]:
        """
        搜尋來回機票
        
        Args:
            route: 航線代碼
            departure_date: 出發日期
            
        Returns:
            Tuple[出發航班, 回程航班, 總價格]
        """
        try:
            route_info = self.target_routes[route]
            return_date = self.calculate_return_date(departure_date)
            
            logger.info(f"搜尋 {route_info['route_name']} - 出發: {departure_date}, 回程: {return_date}")
            
            # 搜尋去程航班
            outbound_result = self.scraper.search_flights(
                departure=route_info["from"],
                arrival=route_info["to"],
                departure_date=departure_date
            )
            
            # 搜尋回程航班
            inbound_result = self.scraper.search_flights(
                departure=route_info["to"],
                arrival=route_info["from"],
                departure_date=return_date
            )
            
            # 取得有空位且有價格的航班
            outbound_flights = [f for f in outbound_result.get_available_flights() if f.price is not None]
            inbound_flights = [f for f in inbound_result.get_available_flights() if f.price is not None]
            
            if not outbound_flights or not inbound_flights:
                logger.warning(f"沒有找到可用的來回航班組合: {route_info['route_name']} {departure_date}")
                return None, None, None
            
            # 找到最便宜的組合
            cheapest_outbound = min(outbound_flights, key=lambda x: x.price)
            cheapest_inbound = min(inbound_flights, key=lambda x: x.price)
            total_price = cheapest_outbound.price + cheapest_inbound.price
            
            logger.info(f"找到最便宜組合: 去程 NT${cheapest_outbound.price:,.0f} + 回程 NT${cheapest_inbound.price:,.0f} = 總計 NT${total_price:,.0f}")
            
            return cheapest_outbound, cheapest_inbound, total_price
            
        except Exception as e:
            logger.error(f"搜尋來回航班時發生錯誤: {str(e)}")
            return None, None, None
    
    def find_cheapest_trips(self, days_ahead: int = 30, max_results: int = 10) -> List[Dict]:
        """
        查詢最便宜的旅行組合
        
        Args:
            days_ahead: 搜尋未來多少天
            max_results: 最多返回幾個結果
            
        Returns:
            List[Dict]: 最便宜旅行組合列表
        """
        all_trips = []
        search_dates = self.get_search_dates(days_ahead)
        
        print("="*80)
        print("🛫 開始搜尋日本最便宜五天四夜來回機票")
        print("="*80)
        print(f"搜尋航線: {', '.join([info['route_name'] for info in self.target_routes.values()])}")
        print(f"搜尋期間: 未來 {days_ahead} 天")
        print(f"行程天數: {self.trip_duration} 天 {self.trip_duration-1} 夜")
        print("="*80)
        
        try:
            for route in self.target_routes.keys():
                route_name = self.target_routes[route]['route_name']
                print(f"\n🔍 正在搜尋 {route_name}...")
                
                for departure_date in search_dates:
                    outbound, inbound, total_price = self.search_round_trip_flights(route, departure_date)
                    
                    if outbound and inbound and total_price:
                        trip_info = {
                            'route': route,
                            'route_name': route_name,
                            'departure_date': departure_date,
                            'return_date': self.calculate_return_date(departure_date),
                            'outbound_flight': {
                                'flight_number': outbound.flight_number,
                                'departure_time': outbound.departure_time,
                                'arrival_time': outbound.arrival_time,
                                'price': outbound.price
                            },
                            'inbound_flight': {
                                'flight_number': inbound.flight_number,
                                'departure_time': inbound.departure_time,
                                'arrival_time': inbound.arrival_time,
                                'price': inbound.price
                            },
                            'total_price': total_price,
                            'price_per_day': total_price / self.trip_duration
                        }
                        all_trips.append(trip_info)
                        
                        print(f"  ✅ {departure_date}: NT$ {total_price:,.0f}")
                    else:
                        print(f"  ❌ {departure_date}: 無可用航班")
        
        except KeyboardInterrupt:
            print("\n\n⏹️  搜尋被使用者中斷")
        
        except Exception as e:
            logger.error(f"搜尋過程中發生錯誤: {str(e)}")
        
        finally:
            # 關閉瀏覽器
            if self.scraper.driver:
                self.scraper.driver.quit()
        
        # 按總價格排序
        all_trips.sort(key=lambda x: x['total_price'])
        
        return all_trips[:max_results]
    
    def display_results(self, trips: List[Dict]):
        """
        顯示搜尋結果
        
        Args:
            trips: 旅行組合列表
        """
        if not trips:
            print("\n❌ 沒有找到任何可用的航班組合")
            return
        
        print(f"\n🏆 找到 {len(trips)} 個最便宜的五天四夜旅行組合")
        print("="*80)
        
        for i, trip in enumerate(trips, 1):
            print(f"\n【第 {i} 名】{trip['route_name']}")
            print(f"📅 旅行日期: {trip['departure_date']} ~ {trip['return_date']}")
            print(f"💰 總價格: NT$ {trip['total_price']:,.0f} (平均每天 NT$ {trip['price_per_day']:,.0f})")
            print(f"✈️  去程: {trip['outbound_flight']['flight_number']} "
                  f"{trip['outbound_flight']['departure_time']}-{trip['outbound_flight']['arrival_time']} "
                  f"NT$ {trip['outbound_flight']['price']:,.0f}")
            print(f"✈️  回程: {trip['inbound_flight']['flight_number']} "
                  f"{trip['inbound_flight']['departure_time']}-{trip['inbound_flight']['arrival_time']} "
                  f"NT$ {trip['inbound_flight']['price']:,.0f}")
            print("-" * 50)
    
    def save_results(self, trips: List[Dict], filename_prefix: str = "japan_cheapest_trips"):
        """
        儲存搜尋結果
        
        Args:
            trips: 旅行組合列表
            filename_prefix: 檔案名稱前綴
        """
        if not trips:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 儲存為CSV
        csv_filename = f"{filename_prefix}_{timestamp}.csv"
        df_data = []
        
        for trip in trips:
            df_data.append({
                '排名': trips.index(trip) + 1,
                '航線': trip['route_name'],
                '出發日期': trip['departure_date'],
                '回程日期': trip['return_date'],
                '總價格': trip['total_price'],
                '平均每日費用': trip['price_per_day'],
                '去程航班': trip['outbound_flight']['flight_number'],
                '去程時間': f"{trip['outbound_flight']['departure_time']}-{trip['outbound_flight']['arrival_time']}",
                '去程價格': trip['outbound_flight']['price'],
                '回程航班': trip['inbound_flight']['flight_number'],
                '回程時間': f"{trip['inbound_flight']['departure_time']}-{trip['inbound_flight']['arrival_time']}",
                '回程價格': trip['inbound_flight']['price']
            })
        
        df = pd.DataFrame(df_data)
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        # 儲存為JSON
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(trips, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 搜尋結果已儲存:")
        print(f"   📊 CSV檔案: {csv_filename}")
        print(f"   📋 JSON檔案: {json_filename}")

def main():
    """主程式入口"""
    try:
        # 初始化查詢器
        finder = JapanCheapestFlightFinder(headless=True)
        
        # 查詢最便宜的旅行組合
        cheapest_trips = finder.find_cheapest_trips(days_ahead=30, max_results=10)
        
        # 顯示結果
        finder.display_results(cheapest_trips)
        
        # 儲存結果
        finder.save_results(cheapest_trips)
        
        print("\n🎉 搜尋完成！")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  程式被使用者中斷")
    except Exception as e:
        logger.error(f"程式執行時發生錯誤: {str(e)}")
        print(f"\n❌ 錯誤: {str(e)}")

if __name__ == "__main__":
    main() 