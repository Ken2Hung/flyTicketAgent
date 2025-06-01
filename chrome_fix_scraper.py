#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import logging
import os
import glob
import re
from typing import List, Optional, Dict, Tuple, Union
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

from config import TigerairConfig
from models import FlightInfo, FlightSearchResult

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FixedChromeScraper:
    """修復版Chrome爬蟲"""
    
    def __init__(self, headless: bool = True):
        """
        初始化修復版Chrome爬蟲
        
        Args:
            headless: 是否使用無頭模式運行瀏覽器
        """
        self.config = TigerairConfig()
        self.headless = headless
        self.driver = None
    
    def _find_chromedriver_path(self) -> str:
        """找到正確的chromedriver路徑"""
        # 搜尋可能的chromedriver位置
        possible_paths = [
            os.path.expanduser("~/.wdm/drivers/chromedriver/mac64/*/chromedriver-mac-arm64/chromedriver"),
            os.path.expanduser("~/.wdm/drivers/chromedriver/mac64/*/chromedriver"),
            "/usr/local/bin/chromedriver",
            "/opt/homebrew/bin/chromedriver",
            "/usr/bin/chromedriver"
        ]
        
        for pattern in possible_paths:
            matches = glob.glob(pattern)
            for path in matches:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    logger.info(f"找到有效的chromedriver: {path}")
                    return path
        
        raise Exception("找不到有效的chromedriver")
    
    def _setup_chrome_driver(self) -> webdriver.Chrome:
        """設定Chrome瀏覽器驅動"""
        try:
            # 設定Chrome選項
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 找到正確的chromedriver路徑
            chromedriver_path = self._find_chromedriver_path()
            service = Service(chromedriver_path)
            
            # 創建Chrome驅動
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.implicitly_wait(self.config.IMPLICIT_WAIT)
            
            logger.info("✅ Chrome瀏覽器啟動成功")
            return driver
            
        except Exception as e:
            raise Exception(f"Chrome啟動失敗: {str(e)}")
    
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
            self.driver = self._setup_chrome_driver()
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
        """填寫搜尋表單 - 針對虎航動態下拉選單優化"""
        try:
            logger.info(f"填寫搜尋表單: {departure} -> {arrival}, {departure_date}")
            
            # 等待頁面載入
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 等待更長時間確保JavaScript加載完成
            time.sleep(3)
            
            # 處理動態出發地選擇
            departure_success = self._select_dynamic_airport(departure, is_departure=True)
            if not departure_success:
                logger.warning(f"設定出發地失敗: {departure}")
            
            # 處理動態目的地選擇
            arrival_success = self._select_dynamic_airport(arrival, is_departure=False)
            if not arrival_success:
                logger.warning(f"設定目的地失敗: {arrival}")
            
            # 設定日期 - 使用動態日期選擇器
            date_success = self._set_dynamic_date(departure_date)
            if not date_success:
                logger.warning("設定日期失敗，但繼續執行")
            
            # 如果有回程日期，設定回程日期
            if return_date:
                return_date_success = self._set_dynamic_return_date(return_date)
                if not return_date_success:
                    logger.warning("設定回程日期失敗")
            
            # 等待一下讓頁面反應
            time.sleep(2)
            
            # 點擊搜尋按鈕
            search_success = self._click_search_button()
            return search_success
            
        except Exception as e:
            logger.error(f"填寫搜尋表單失敗: {str(e)}")
            return False

    def _select_dynamic_airport(self, airport_code: str, is_departure: bool = True) -> bool:
        """選擇動態機場下拉選單"""
        field_type = "出發地" if is_departure else "目的地"
        logger.info(f"正在設定{field_type}: {airport_code}")
        
        # 機場代碼對應的中文名稱
        airport_names = {
            'TPE': ['台北', '桃園', 'TPE', '台北(桃園)'],
            'NRT': ['東京', '成田', 'NRT', '東京成田'],
            'OKA': ['沖繩', 'OKA', '那霸', '沖繩(那霸)'],
            'KIX': ['大阪', '關西', 'KIX'],
            'NGO': ['名古屋', 'NGO', '中部']
        }
        
        # 不同類型的選擇器
        input_selectors = [
            "input[placeholder*='出發地']" if is_departure else "input[placeholder*='目的地']",
            "input[placeholder*='出發']" if is_departure else "input[placeholder*='抵達']", 
            f"input[name*='{'departure' if is_departure else 'arrival'}']",
            f"input[id*='{'departure' if is_departure else 'arrival'}']",
            ".departure-input" if is_departure else ".arrival-input",
            "#departure" if is_departure else "#arrival",
            "[data-testid*='origin']" if is_departure else "[data-testid*='destination']"
        ]
        
        for selector in input_selectors:
            try:
                # 找到輸入框
                input_element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                logger.info(f"找到{field_type}輸入框: {selector}")
                
                # 點擊輸入框激活下拉選單
                self.driver.execute_script("arguments[0].click();", input_element)
                time.sleep(1)
                
                # 清空並輸入機場代碼或名稱來過濾選項
                input_element.clear()
                time.sleep(0.5)
                
                # 嘗試輸入不同的搜尋詞
                search_terms = [airport_code] + airport_names.get(airport_code, [])
                
                for term in search_terms:
                    try:
                        input_element.clear()
                        input_element.send_keys(term)
                        time.sleep(1)
                        
                        # 嘗試從下拉選單中選擇
                        if self._select_from_dropdown(airport_code, term):
                            logger.info(f"{field_type}設定成功: {airport_code} (搜尋詞: {term})")
                            return True
                            
                    except Exception as e:
                        logger.debug(f"搜尋詞 {term} 失敗: {e}")
                        continue
                
            except Exception as e:
                logger.debug(f"{field_type}選擇器 {selector} 失敗: {e}")
                continue
        
        logger.warning(f"{field_type}設定失敗: {airport_code}")
        return False

    def _select_from_dropdown(self, airport_code: str, search_term: str) -> bool:
        """從下拉選單中選擇機場"""
        # 等待下拉選單出現
        dropdown_selectors = [
            ".dropdown-menu",
            ".airport-list", 
            ".suggestion-list",
            "[role='listbox']",
            ".autocomplete-results",
            ".airport-options",
            "ul[class*='dropdown']",
            "div[class*='dropdown']",
            ".menu-list"
        ]
        
        for dropdown_selector in dropdown_selectors:
            try:
                # 等待下拉選單出現
                dropdown = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, dropdown_selector))
                )
                
                # 尋找匹配的選項
                option_selectors = [
                    f"*[text()*='{airport_code}']",
                    f"*[contains(text(), '{airport_code}')]",
                    f"*[contains(text(), '{search_term}')]",
                    f"li:contains('{airport_code}')",
                    f"div:contains('{airport_code}')",
                    f"[data-code='{airport_code}']",
                    f"[data-iata='{airport_code}']",
                    f"[value='{airport_code}']"
                ]
                
                # 直接在下拉選單中尋找選項
                options = dropdown.find_elements(By.XPATH, f".//*[contains(text(), '{airport_code}') or contains(text(), '{search_term}')]")
                
                if options:
                    for option in options:
                        try:
                            self.driver.execute_script("arguments[0].click();", option)
                            logger.info(f"成功選擇機場選項: {option.text[:50]}")
                            time.sleep(1)
                            return True
                        except:
                            continue
                
            except Exception as e:
                logger.debug(f"下拉選單選擇器 {dropdown_selector} 失敗: {e}")
                continue
        
        return False

    def _set_dynamic_date(self, departure_date: str) -> bool:
        """設定動態日期選擇器"""
        logger.info(f"正在設定出發日期: {departure_date}")
        
        # 日期輸入框選擇器
        date_selectors = [
            "input[placeholder*='去程']",
            "input[placeholder*='出發日期']",
            "input[name*='departure']",
            "input[name*='outbound']",
            "#departure-date",
            "#departureDate",
            ".departure-date",
            "input[type='date']"
        ]
        
        # 解析日期
        try:
            from datetime import datetime
            date_obj = datetime.strptime(departure_date, '%Y-%m-%d')
            
            # 不同的日期格式
            date_formats = [
                departure_date,  # 2025-06-02
                date_obj.strftime('%Y/%m/%d'),  # 2025/06/02
                date_obj.strftime('%m/%d/%Y'),  # 06/02/2025
                date_obj.strftime('%d/%m/%Y'),  # 02/06/2025
                date_obj.strftime('%Y年%m月%d日'),  # 2025年06月02日
            ]
            
        except:
            date_formats = [departure_date]
        
        for selector in date_selectors:
            try:
                # 找到日期輸入框
                date_element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                logger.info(f"找到日期輸入框: {selector}")
                
                # 點擊激活日期選擇器
                self.driver.execute_script("arguments[0].click();", date_element)
                time.sleep(1)
                
                # 嘗試不同的日期格式
                for date_format in date_formats:
                    try:
                        date_element.clear()
                        time.sleep(0.5)
                        date_element.send_keys(date_format)
                        time.sleep(1)
                        
                        # 按下Tab確認
                        date_element.send_keys(Keys.TAB)
                        time.sleep(1)
                        
                        logger.info(f"日期設定成功: {date_format}")
                        return True
                        
                    except Exception as e:
                        logger.debug(f"日期格式 {date_format} 失敗: {e}")
                        continue
                
            except Exception as e:
                logger.debug(f"日期選擇器 {selector} 失敗: {e}")
                continue
        
        logger.warning(f"日期設定失敗: {departure_date}")
        return False

    def _set_dynamic_return_date(self, return_date: str) -> bool:
        """設定回程日期"""
        logger.info(f"正在設定回程日期: {return_date}")
        
        # 回程日期輸入框選擇器
        return_date_selectors = [
            "input[placeholder*='回程']",
            "input[placeholder*='回程日期']", 
            "input[name*='return']",
            "input[name*='inbound']",
            "#return-date",
            "#returnDate",
            ".return-date"
        ]
        
        # 使用類似的邏輯設定回程日期
        return self._set_date_with_selectors(return_date, return_date_selectors)
    
    def _set_date_with_selectors(self, date_str: str, selectors: list) -> bool:
        """用指定的選擇器設定日期"""
        for selector in selectors:
            try:
                date_element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                self.driver.execute_script("arguments[0].click();", date_element)
                time.sleep(1)
                
                date_element.clear()
                date_element.send_keys(date_str)
                date_element.send_keys(Keys.TAB)
                time.sleep(1)
                
                return True
                
            except:
                continue
        
        return False
    
    def _click_search_button(self) -> bool:
        """點擊搜尋按鈕 - 針對虎航網站優化"""
        logger.info("正在尋找並點擊搜尋按鈕...")
        
        search_selectors = [
            # 虎航常用的搜尋按鈕樣式
            "button:contains('搜尋')",
            "button:contains('Search')", 
            "button:contains('搜索')",
            "input[value*='搜尋']",
            "input[value*='Search']",
            ".search-btn",
            ".btn-search",
            "#search-btn",
            "#searchBtn",
            "button[type='submit']",
            "input[type='submit']",
            ".btn-primary",
            ".search-button",
            ".btn-orange",  # 虎航橘色按鈕
            ".submit-btn",
            "[data-testid*='search']",
            "button[class*='search']",
            "button[class*='submit']",
            ".flight-search-btn"
        ]
        
        for selector in search_selectors:
            try:
                # 特殊處理contains選擇器
                if ':contains(' in selector:
                    text = selector.split("'")[1]
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        if text in button.text:
                            # 確認按鈕可見且可點擊
                            if button.is_displayed() and button.is_enabled():
                                self.driver.execute_script("arguments[0].click();", button)
                                logger.info(f"點擊搜尋按鈕成功: {text}")
                                time.sleep(2)  # 等待搜尋開始
                                return True
                else:
                    search_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    if search_btn.is_displayed() and search_btn.is_enabled():
                        self.driver.execute_script("arguments[0].click();", search_btn)
                        logger.info(f"點擊搜尋按鈕成功: {selector}")
                        time.sleep(2)  # 等待搜尋開始
                        return True
                        
            except Exception as e:
                logger.debug(f"搜尋按鈕選擇器 {selector} 失敗: {e}")
                continue
        
        # 如果找不到按鈕，嘗試按Enter鍵觸發搜尋
        try:
            from selenium.webdriver.common.keys import Keys
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ENTER)
            logger.info("使用Enter鍵觸發搜尋")
            time.sleep(2)
            return True
        except:
            pass
        
        logger.warning("無法找到或點擊搜尋按鈕")
        return False
    
    def _parse_flight_results(self) -> List[FlightInfo]:
        """解析航班搜尋結果"""
        flights = []
        
        try:
            # 等待結果載入
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".flight-card, .flight-result, .flight-item, .price, [class*='flight'], [class*='itinerary']"))
            )
            
            # 取得頁面源碼並用BeautifulSoup解析
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 先嘗試解析具體的航班卡片
            flights = self._parse_flight_cards(soup)
            
            # 如果沒找到航班卡片，嘗試解析航班列表
            if not flights:
                flights = self._parse_flight_list(soup)
            
            # 如果還是沒找到，嘗試解析價格日曆作為備選
            if not flights:
                flights = self._parse_price_calendar(soup)
            
        except TimeoutException:
            logger.warning("等待航班結果載入超時，嘗試直接解析")
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            flights = self._parse_flight_cards(soup) or self._parse_flight_list(soup) or self._parse_price_calendar(soup)
        
        except Exception as e:
            logger.error(f"解析航班結果失敗: {str(e)}")
        
        return flights
    
    def _parse_flight_cards(self, soup) -> List[FlightInfo]:
        """解析航班卡片（最詳細的資訊）"""
        flights = []
        
        try:
            # 尋找航班卡片容器
            flight_cards = soup.find_all(['div', 'li'], class_=re.compile(r'flight.*card|card.*flight|itinerary|flight.*item'))
            
            for card in flight_cards:
                flight_info = self._extract_detailed_flight_info(card)
                if flight_info and flight_info.flight_number:
                    flights.append(flight_info)
            
            logger.info(f"從航班卡片解析出 {len(flights)} 筆航班")
            
        except Exception as e:
            logger.error(f"解析航班卡片失敗: {str(e)}")
        
        return flights
    
    def _parse_flight_list(self, soup) -> List[FlightInfo]:
        """解析航班列表"""
        flights = []
        
        try:
            # 尋找包含航班資訊的元素
            flight_elements = soup.find_all(text=re.compile(r'IT\s*\d+'))
            
            for element in flight_elements:
                parent = element.parent
                while parent and parent.name != 'body':
                    # 檢查父元素是否包含完整的航班資訊
                    if self._contains_flight_details(parent):
                        flight_info = self._extract_detailed_flight_info(parent)
                        if flight_info and flight_info.flight_number:
                            flights.append(flight_info)
                        break
                    parent = parent.parent
            
            # 去除重複
            unique_flights = []
            seen_flights = set()
            for flight in flights:
                flight_key = f"{flight.flight_number}-{flight.departure_time}-{flight.price}"
                if flight_key not in seen_flights:
                    unique_flights.append(flight)
                    seen_flights.add(flight_key)
            
            logger.info(f"從航班列表解析出 {len(unique_flights)} 筆航班")
            return unique_flights
            
        except Exception as e:
            logger.error(f"解析航班列表失敗: {str(e)}")
        
        return []
    
    def _contains_flight_details(self, element) -> bool:
        """檢查元素是否包含航班詳細資訊"""
        text = element.get_text().lower()
        has_flight_number = bool(re.search(r'it\s*\d+', text))
        has_time = bool(re.search(r'\d{1,2}:\d{2}', text))
        has_price = bool(re.search(r'twd|nt\$|\d{3,5}', text))
        
        return has_flight_number and (has_time or has_price)
    
    def _extract_detailed_flight_info(self, element) -> Optional[FlightInfo]:
        """從HTML元素中提取詳細航班資訊"""
        try:
            text = element.get_text()
            
            # 提取航班號碼
            flight_number_match = re.search(r'(IT\s*\d+|TT\s*\d+)', text)
            if not flight_number_match:
                return None
            
            flight_number = flight_number_match.group(1).replace(' ', '')
            
            # 提取時間資訊 - 更精確的時間匹配
            time_patterns = [
                r'(\d{1,2}:\d{2})',  # 基本時間格式
                r'起飛[：:]?\s*(\d{1,2}:\d{2})',  # 起飛時間
                r'降落[：:]?\s*(\d{1,2}:\d{2})',  # 降落時間
            ]
            
            all_times = []
            for pattern in time_patterns:
                times = re.findall(pattern, text)
                all_times.extend(times)
            
            # 去除重複並排序
            unique_times = list(dict.fromkeys(all_times))  # 保持順序去重
            
            # 提取價格資訊 - 更精確的價格匹配
            price_patterns = [
                r'TWD\s*([0-9,]+)',
                r'NT\$\s*([0-9,]+)', 
                r'(\d{1,5}(?:,\d{3})*)\s*(?:元|TWD|$)',
                r'價格[：:]\s*([0-9,]+)',
                r'依官方最終核准為準.*?(\d{1,5}(?:,\d{3})*)'  # 特殊情況
            ]
            
            price = None
            for pattern in price_patterns:
                price_match = re.search(pattern, text)
                if price_match:
                    price_str = price_match.group(1)
                    try:
                        potential_price = float(price_str.replace(',', ''))
                        # 確保價格在合理範圍內
                        if 1000 <= potential_price <= 50000:
                            price = potential_price
                            break
                    except:
                        continue
            
            # 檢查座位狀況
            seats_available = True
            unavailable_keywords = ['售完', '已滿', 'sold out', 'unavailable', '無座位', '額滿']
            if any(keyword in text.lower() for keyword in unavailable_keywords):
                seats_available = False
            
            # 生成更具體的來源網址
            source_url = self.driver.current_url
            if "tigerair.com" not in source_url:
                source_url = "https://www.tigerair.com/tw/zh/"
            
            # 建立航班資訊物件
            flight_info = FlightInfo(
                flight_number=flight_number,
                departure_time=unique_times[0] if len(unique_times) >= 1 else "",
                arrival_time=unique_times[1] if len(unique_times) >= 2 else "",
                price=price,
                seats_available=seats_available,
                source_url=source_url
            )
            
            # 設定時間區間
            if flight_info.departure_time:
                flight_info.time_slot = self._get_time_slot(flight_info.departure_time)
            
            # 記錄詳細資訊用於除錯
            if flight_info.flight_number and flight_info.price:
                logger.info(f"解析航班: {flight_info.flight_number}, 時間: {flight_info.departure_time}-{flight_info.arrival_time}, 價格: NT${flight_info.price}, 來源: {source_url}")
            
            return flight_info
            
        except Exception as e:
            logger.debug(f"提取航班資訊失敗: {str(e)}")
            return None
    
    def _parse_price_calendar(self, soup) -> List[FlightInfo]:
        """解析價格日曆（如果有的話）"""
        flights = []
        
        try:
            # 尋找價格元素 - 更精確的價格匹配
            price_patterns = [
                r'TWD\s*([0-9]{1,5}(?:,\d{3})*)',  # TWD 格式，限制數字長度
                r'NT\$?\s*([0-9]{1,5}(?:,\d{3})*)',  # NT$ 格式
                r'\b([1-9]\d{3}(?:,\d{3})*)\b',  # 一般數字格式，必須以非0開頭且至少4位數
            ]
            
            text = soup.get_text()
            all_prices = []
            
            for pattern in price_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    try:
                        price = float(match.replace(',', ''))
                        # 過濾合理的機票價格範圍
                        if 1000 <= price <= 50000:  # 機票價格通常在1,000-50,000之間
                            all_prices.append(price)
                    except:
                        continue
            
            # 去除重複並排序
            unique_prices = sorted(list(set(all_prices)))
            
            flight_counter = 1
            for price in unique_prices[:10]:  # 最多取10個價格
                flight_info = FlightInfo(
                    flight_number=f"IT{200 + flight_counter}",
                    departure_time="", 
                    arrival_time="",
                    price=price,
                    seats_available=True
                )
                
                flights.append(flight_info)
                flight_counter += 1
            
        except Exception as e:
            logger.error(f"解析價格日曆失敗: {str(e)}")
        
        return flights
    
    def _get_time_slot(self, time_str: str) -> str:
        """判斷時間屬於哪個時段"""
        try:
            hour = int(time_str.split(':')[0])
            if 6 <= hour < 12:
                return "上午"
            elif 12 <= hour < 18:
                return "下午"
            elif 18 <= hour < 24:
                return "晚班"
            else:
                return "早班"
        except:
            return "未知" 