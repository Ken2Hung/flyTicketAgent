import time
import re
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple, Union
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import json
import os

from config import TigerairConfig
from models import FlightInfo, FlightSearchResult

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tigerair_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TigerairScraper:
    """虎航機票爬蟲類別"""
    
    def __init__(self, headless: bool = True):
        """
        初始化爬蟲
        
        Args:
            headless: 是否使用無頭模式運行瀏覽器
        """
        self.config = TigerairConfig()
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update(self.config.HEADERS)
        
        # 建立輸出目錄
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
    
    def _setup_driver(self) -> Union[webdriver.Chrome, webdriver.Safari]:
        """設定瀏覽器驅動 - 優先使用Chrome"""
        try:
            # 首先嘗試使用Chrome（推薦，跨平台支援）
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.implicitly_wait(self.config.IMPLICIT_WAIT)
            logger.info("使用Chrome瀏覽器")
            return driver
            
        except Exception as chrome_error:
            logger.warning(f"Chrome啟動失敗: {chrome_error}")
            logger.info("嘗試使用Safari瀏覽器...")
            
            # 如果Chrome失敗，回退到Safari（僅Mac）
            try:
                import platform
                if platform.system() != 'Darwin':
                    raise Exception("Safari僅在Mac系統上可用")
                    
                safari_options = webdriver.SafariOptions()
                driver = webdriver.Safari(options=safari_options)
                driver.implicitly_wait(self.config.IMPLICIT_WAIT)
                logger.info("使用Safari瀏覽器")
                return driver
                
            except Exception as safari_error:
                logger.error(f"Safari也啟動失敗: {safari_error}")
                error_msg = f"""
無法啟動任何瀏覽器:
- Chrome錯誤: {chrome_error}
- Safari錯誤: {safari_error}

解決方案:
1. 安裝Chrome: https://www.google.com/chrome/
2. 或者在Mac上啟用Safari WebDriver: sudo safaridriver --enable
                """
                raise Exception(error_msg)
    
    def _setup_driver_chrome_only(self) -> webdriver.Chrome:
        """設定Chrome瀏覽器驅動"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.implicitly_wait(self.config.IMPLICIT_WAIT)
        
        return driver
    
    def _get_time_slot(self, time_str: str) -> str:
        """判斷時間屬於哪個時段"""
        try:
            hour = int(time_str.split(':')[0])
            time_slots = self.config.get_time_slots()
            
            for slot_name, (start, end) in time_slots.items():
                start_hour = int(start.split(':')[0])
                end_hour = int(end.split(':')[0])
                
                if start_hour <= hour < end_hour or (slot_name == "晚班" and hour >= start_hour):
                    return slot_name
            
            return "未知"
        except:
            return "未知"
    
    def search_flights(self, 
                      departure: str, 
                      arrival: str, 
                      departure_date: str,
                      return_date: Optional[str] = None) -> FlightSearchResult:
        """
        搜尋航班
        
        Args:
            departure: 出發機場代碼
            arrival: 抵達機場代碼  
            departure_date: 出發日期 (YYYY-MM-DD)
            return_date: 回程日期 (可選)
            
        Returns:
            FlightSearchResult: 搜尋結果
        """
        result = FlightSearchResult()
        result.search_params = {
            'departure': departure,
            'arrival': arrival,
            'departure_date': departure_date,
            'return_date': return_date
        }
        
        try:
            self.driver = self._setup_driver()
            logger.info(f"開始搜尋航班: {departure} -> {arrival}, 日期: {departure_date}")
            
            # 訪問虎航網站
            self.driver.get(self.config.BASE_URL)
            time.sleep(3)
            
            # 填寫搜尋表單
            success = self._fill_search_form(departure, arrival, departure_date, return_date)
            if not success:
                result.add_error("填寫搜尋表單失敗")
                return result
            
            # 等待搜尋結果載入
            time.sleep(5)
            
            # 解析航班資料
            flights = self._parse_flight_results()
            for flight in flights:
                result.add_flight(flight)
            
            logger.info(f"成功爬取 {len(flights)} 筆航班資料")
            
        except Exception as e:
            error_msg = f"搜尋航班時發生錯誤: {str(e)}"
            logger.error(error_msg)
            result.add_error(error_msg)
        
        finally:
            if self.driver:
                self.driver.quit()
        
        return result
    
    def _fill_search_form(self, departure: str, arrival: str, 
                         departure_date: str, return_date: Optional[str] = None) -> bool:
        """填寫搜尋表單"""
        try:
            # 點擊單程/來回選項
            if return_date:
                # 來回票
                round_trip_radio = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[value='return']"))
                )
                round_trip_radio.click()
            else:
                # 單程票
                one_way_radio = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[value='oneway']"))
                )
                one_way_radio.click()
            
            time.sleep(1)
            
            # 選擇出發地
            departure_input = self.driver.find_element(By.CSS_SELECTOR, "input[name*='origin'], input[placeholder*='出發地']")
            departure_input.clear()
            departure_input.send_keys(departure)
            time.sleep(1)
            
            # 選擇目的地
            arrival_input = self.driver.find_element(By.CSS_SELECTOR, "input[name*='destination'], input[placeholder*='目的地']")
            arrival_input.clear()
            arrival_input.send_keys(arrival)
            time.sleep(1)
            
            # 設定出發日期
            departure_date_input = self.driver.find_element(By.CSS_SELECTOR, "input[name*='departure'], input[placeholder*='出發']")
            departure_date_input.clear()
            departure_date_input.send_keys(departure_date)
            time.sleep(1)
            
            # 如果是來回票，設定回程日期
            if return_date:
                return_date_input = self.driver.find_element(By.CSS_SELECTOR, "input[name*='return'], input[placeholder*='回程']")
                return_date_input.clear()
                return_date_input.send_keys(return_date)
                time.sleep(1)
            
            # 點擊搜尋按鈕
            search_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .search-button, .btn-search")
            search_button.click()
            
            return True
            
        except Exception as e:
            logger.error(f"填寫搜尋表單失敗: {str(e)}")
            return False
    
    def _parse_flight_results(self) -> List[FlightInfo]:
        """解析航班搜尋結果"""
        flights = []
        
        try:
            # 等待結果載入
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".flight-card, .flight-result, .flight-item"))
            )
            
            # 取得頁面源碼並用BeautifulSoup解析
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 尋找航班卡片/項目
            flight_elements = soup.find_all(['div', 'li'], class_=re.compile(r'flight|result|card|item'))
            
            for element in flight_elements:
                flight_info = self._extract_flight_info(element)
                if flight_info and flight_info.flight_number:
                    flights.append(flight_info)
            
        except TimeoutException:
            logger.warning("等待航班結果載入超時，嘗試直接解析")
            # 如果等待超時，嘗試直接解析現有內容
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            flight_elements = soup.find_all(['div', 'li'])
            
            for element in flight_elements:
                if self._is_flight_element(element):
                    flight_info = self._extract_flight_info(element)
                    if flight_info and flight_info.flight_number:
                        flights.append(flight_info)
        
        except Exception as e:
            logger.error(f"解析航班結果失敗: {str(e)}")
        
        return flights
    
    def _is_flight_element(self, element) -> bool:
        """判斷元素是否為航班資訊元素"""
        text = element.get_text().lower()
        return any(keyword in text for keyword in ['flight', 'it', 'tit', '航班', '起飛', '降落', '票價'])
    
    def _extract_flight_info(self, element) -> Optional[FlightInfo]:
        """從HTML元素中提取航班資訊"""
        try:
            text = element.get_text()
            
            # 提取航班號碼
            flight_number_match = re.search(r'(IT\d+|TT\d+)', text)
            if not flight_number_match:
                return None
            
            flight_number = flight_number_match.group(1)
            
            # 提取時間資訊
            time_pattern = r'(\d{1,2}:\d{2})'
            times = re.findall(time_pattern, text)
            
            # 提取價格資訊
            price_pattern = r'NT\$?\s*([0-9,]+)|TWD\s*([0-9,]+)|(\d{1,3}(?:,\d{3})*)'
            price_match = re.search(price_pattern, text)
            price = None
            if price_match:
                price_str = price_match.group(1) or price_match.group(2) or price_match.group(3)
                try:
                    price = float(price_str.replace(',', ''))
                except:
                    pass
            
            # 檢查座位狀況
            seats_available = True
            if any(keyword in text for keyword in ['售完', '已滿', 'sold out', 'unavailable']):
                seats_available = False
            
            # 建立航班資訊物件
            flight_info = FlightInfo(
                flight_number=flight_number,
                departure_time=times[0] if len(times) >= 1 else "",
                arrival_time=times[1] if len(times) >= 2 else "",
                price=price,
                seats_available=seats_available,
                source_url=self.driver.current_url
            )
            
            # 設定時間區間
            if flight_info.departure_time:
                flight_info.time_slot = self._get_time_slot(flight_info.departure_time)
            
            return flight_info
            
        except Exception as e:
            logger.debug(f"提取航班資訊失敗: {str(e)}")
            return None
    
    def search_multiple_routes(self, 
                             routes: List[str], 
                             dates: List[str]) -> Dict[str, FlightSearchResult]:
        """
        搜尋多條航線的航班
        
        Args:
            routes: 航線列表 (如 ['TPE_NRT', 'TPE_KIX'])
            dates: 日期列表
            
        Returns:
            Dict[str, FlightSearchResult]: 各航線的搜尋結果
        """
        results = {}
        
        for route in routes:
            if route not in self.config.ROUTES:
                logger.warning(f"未知航線: {route}")
                continue
            
            route_info = self.config.ROUTES[route]
            departure = route_info["from"]
            arrival = route_info["to"]
            route_name = route_info["route_name"]
            
            logger.info(f"開始搜尋航線: {route_name}")
            
            route_results = FlightSearchResult()
            route_results.search_params['route'] = route_name
            
            for date in dates:
                try:
                    daily_result = self.search_flights(departure, arrival, date)
                    
                    # 合併結果
                    for flight in daily_result.flights:
                        flight.departure_date = date
                        route_results.add_flight(flight)
                    
                    # 合併錯誤
                    for error in daily_result.errors:
                        route_results.add_error(f"{date}: {error}")
                    
                    # 延遲避免被封鎖
                    time.sleep(2)
                    
                except Exception as e:
                    error_msg = f"搜尋 {route_name} {date} 失敗: {str(e)}"
                    logger.error(error_msg)
                    route_results.add_error(error_msg)
            
            results[route] = route_results
            logger.info(f"完成搜尋航線: {route_name}, 共 {route_results.success_count} 筆資料")
        
        return results
    
    def save_results(self, results: Dict[str, FlightSearchResult], 
                    output_format: str = 'both') -> Dict[str, str]:
        """
        儲存搜尋結果
        
        Args:
            results: 搜尋結果
            output_format: 輸出格式 ('csv', 'json', 'both')
            
        Returns:
            Dict[str, str]: 輸出檔案路徑
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_paths = {}
        
        try:
            # 合併所有結果
            all_flights = []
            for route, result in results.items():
                for flight in result.flights:
                    flight_dict = flight.to_dict()
                    flight_dict['route'] = route
                    all_flights.append(flight_dict)
            
            if not all_flights:
                logger.warning("沒有航班資料可儲存")
                return file_paths
            
            # 儲存為CSV
            if output_format in ['csv', 'both']:
                csv_filename = f"tigerair_flights_{timestamp}.csv"
                csv_path = os.path.join(self.config.OUTPUT_DIR, csv_filename)
                
                df = pd.DataFrame(all_flights)
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                file_paths['csv'] = csv_path
                logger.info(f"CSV檔案已儲存: {csv_path}")
            
            # 儲存為JSON
            if output_format in ['json', 'both']:
                json_filename = f"tigerair_flights_{timestamp}.json"
                json_path = os.path.join(self.config.OUTPUT_DIR, json_filename)
                
                output_data = {
                    'timestamp': timestamp,
                    'total_flights': len(all_flights),
                    'routes': {route: result.to_dict() for route, result in results.items()},
                    'summary': {
                        'total_routes': len(results),
                        'total_flights': len(all_flights),
                        'routes_summary': {
                            route: {
                                'flight_count': result.success_count,
                                'error_count': result.error_count
                            } for route, result in results.items()
                        }
                    }
                }
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)
                
                file_paths['json'] = json_path
                logger.info(f"JSON檔案已儲存: {json_path}")
        
        except Exception as e:
            logger.error(f"儲存結果失敗: {str(e)}")
        
        return file_paths 