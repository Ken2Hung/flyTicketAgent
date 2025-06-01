#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from datetime import datetime, timedelta
import logging

from tigerair_scraper import TigerairScraper
from config import TigerairConfig
from models import FlightSearchResult

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(
        description='虎航機票爬蟲 - 爬取台灣虎航到日本的航班資訊',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
    # 搜尋特定航線和日期
    python main.py --route TPE_NRT --date 2024-03-15
    
    # 搜尋多條航線，未來7天
    python main.py --route TPE_NRT TPE_KIX --days 7
    
    # 搜尋所有航線，未來30天
    python main.py --all-routes --days 30
    
    # 只輸出JSON格式
    python main.py --route TPE_NRT --date 2024-03-15 --format json
        """
    )
    
    # 航線參數
    parser.add_argument(
        '--route', 
        nargs='+',
        choices=list(TigerairConfig.ROUTES.keys()),
        help='要搜尋的航線代碼'
    )
    
    parser.add_argument(
        '--all-routes',
        action='store_true',
        help='搜尋所有支援的航線'
    )
    
    # 日期參數
    parser.add_argument(
        '--date',
        nargs='+',
        help='搜尋日期 (YYYY-MM-DD格式)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='搜尋未來幾天的航班 (預設: 7天)'
    )
    
    # 輸出參數
    parser.add_argument(
        '--format',
        choices=['csv', 'json', 'both'],
        default='both',
        help='輸出格式 (預設: both)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='使用無頭模式運行瀏覽器 (預設: True)'
    )
    
    parser.add_argument(
        '--show-browser',
        action='store_true',
        help='顯示瀏覽器視窗 (除錯用)'
    )
    
    args = parser.parse_args()
    
    # 參數檢查
    if not args.route and not args.all_routes:
        parser.error("請指定 --route 或 --all-routes")
    
    # 決定要搜尋的航線
    if args.all_routes:
        routes = list(TigerairConfig.ROUTES.keys())
    else:
        routes = args.route
    
    # 決定要搜尋的日期
    if args.date:
        dates = args.date
    else:
        # 產生未來N天的日期
        today = datetime.now().date()
        dates = []
        for i in range(1, args.days + 1):
            search_date = today + timedelta(days=i)
            dates.append(search_date.strftime("%Y-%m-%d"))
    
    # 決定瀏覽器模式
    headless = args.headless and not args.show_browser
    
    # 顯示搜尋資訊
    print("="*60)
    print("🛫 虎航機票爬蟲開始執行")
    print("="*60)
    print(f"搜尋航線: {', '.join([TigerairConfig.ROUTES[r]['route_name'] for r in routes])}")
    print(f"搜尋日期: {', '.join(dates[:5])}" + ("..." if len(dates) > 5 else ""))
    print(f"瀏覽器模式: {'無頭模式' if headless else '顯示視窗'}")
    print(f"輸出格式: {args.format}")
    print("="*60)
    
    try:
        # 初始化爬蟲
        scraper = TigerairScraper(headless=headless)
        
        # 執行搜尋
        logger.info("開始搜尋航班...")
        results = scraper.search_multiple_routes(routes, dates)
        
        # 統計結果
        total_flights = sum(result.success_count for result in results.values())
        total_errors = sum(result.error_count for result in results.values())
        
        print("\n" + "="*60)
        print("📊 搜尋結果統計")
        print("="*60)
        
        for route, result in results.items():
            route_name = TigerairConfig.ROUTES[route]['route_name']
            print(f"{route_name}: {result.success_count} 筆航班, {result.error_count} 個錯誤")
            
            # 顯示可用航班摘要
            available_flights = result.get_available_flights()
            if available_flights:
                cheapest = min(available_flights, key=lambda x: x.price or float('inf'))
                print(f"  ✅ 有空位航班: {len(available_flights)} 筆")
                if cheapest.price:
                    print(f"  💰 最低價格: NT$ {cheapest.price:,.0f}")
            else:
                print(f"  ❌ 無可用航班")
        
        print(f"\n總計: {total_flights} 筆航班資料, {total_errors} 個錯誤")
        
        # 儲存結果
        if total_flights > 0:
            logger.info("儲存搜尋結果...")
            file_paths = scraper.save_results(results, args.format)
            
            print("\n" + "="*60)
            print("💾 檔案輸出")
            print("="*60)
            for format_type, path in file_paths.items():
                print(f"{format_type.upper()} 檔案: {path}")
        else:
            print("\n⚠️  沒有找到任何航班資料，不輸出檔案")
        
        print("\n🎉 爬蟲執行完成！")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  使用者中斷執行")
        sys.exit(1)
    except Exception as e:
        logger.error(f"執行過程中發生錯誤: {str(e)}")
        print(f"\n❌ 錯誤: {str(e)}")
        sys.exit(1)

def show_routes():
    """顯示支援的航線"""
    print("支援的航線:")
    print("-" * 40)
    for code, info in TigerairConfig.ROUTES.items():
        print(f"{code}: {info['route_name']}")

def show_example():
    """顯示使用範例"""
    print("使用範例:")
    print("-" * 40)
    print("# 搜尋台北到東京，明天的航班")
    print("python main.py --route TPE_NRT --days 1")
    print()
    print("# 搜尋所有航線，未來一週")
    print("python main.py --all-routes --days 7")
    print()
    print("# 搜尋特定日期")
    print("python main.py --route TPE_NRT --date 2024-03-15 2024-03-16")

if __name__ == "__main__":
    main() 