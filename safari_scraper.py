#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import logging
from typing import List, Optional, Dict, Tuple, Union
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import platform

from config import TigerairConfig
from models import FlightInfo, FlightSearchResult

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SafariTigerairScraper:
    """使用Safari的虎航機票爬蟲"""
    
    def __init__(self, headless: bool = True):
        """
        初始化Safari爬蟲
        
        Args:
            headless: Safari不支援headless模式，此參數會被忽略
        """
        self.config = TigerairConfig()
        if headless:
            logger.warning("Safari不支援無頭模式，將以視窗模式運行")
        self.driver = None
    
    def _setup_safari_driver(self) -> webdriver.Safari:
        """設定Safari瀏覽器驅動"""
        try:
            # 檢查是否為Mac系統
            if platform.system() != 'Darwin':
                raise Exception("Safari僅在Mac系統上可用")
            
            # 設定Safari選項
            safari_options = SafariOptions()
            
            # 創建Safari驅動
            driver = webdriver.Safari(options=safari_options)
            driver.implicitly_wait(self.config.IMPLICIT_WAIT)
            
            logger.info("✅ Safari瀏覽器啟動成功")
            return driver
            
        except Exception as e:
            error_msg = f"""
Safari啟動失敗: {str(e)}

解決方案:
1. 確認您使用的是Mac系統
2. 啟用Safari WebDriver:
   - 打開Terminal
   - 執行: sudo safaridriver --enable
   - 輸入管理員密碼
3. 或安裝Chrome瀏覽器: brew install --cask google-chrome
            """
            raise Exception(error_msg)
    
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
            self.driver = self._setup_safari_driver()
            logger.info(f"開始搜尋航班: {departure} -> {arrival}, 日期: {departure_date}")
            
            # 訪問虎航網站
            self.driver.get(self.config.BASE_URL)
            time.sleep(3)
            
            # 填寫搜尋表單（簡化版本）
            success = self._fill_search_form_safari(departure, arrival, departure_date, return_date)
            if not success:
                result.add_error("填寫搜尋表單失敗")
                return result
            
            # 等待搜尋結果載入
            time.sleep(5)
            
            # 解析航班資料（簡化版本）
            flights = self._parse_flight_results_safari()
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
    
    def _fill_search_form_safari(self, departure: str, arrival: str, 
                               departure_date: str, return_date: Optional[str] = None) -> bool:
        """填寫搜尋表單（Safari版本）"""
        try:
            # 這裡實作Safari專用的表單填寫邏輯
            # 先用簡單的模擬搜尋
            logger.info(f"模擬搜尋: {departure} -> {arrival} on {departure_date}")
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"填寫表單失敗: {str(e)}")
            return False
    
    def _parse_flight_results_safari(self) -> List[FlightInfo]:
        """解析航班結果（Safari版本）"""
        try:
            # 這裡實作Safari專用的結果解析邏輯
            # 目前回傳模擬資料
            flights = []
            
            # 模擬航班資料
            flight = FlightInfo(
                flight_number="IT200",
                departure_time="08:25",
                arrival_time="12:30",
                departure_date="2025-06-02",
                price=4500.0,
                seats_available=True,
                time_slot="上午"
            )
            flights.append(flight)
            
            logger.info("解析航班資料完成（模擬資料）")
            return flights
            
        except Exception as e:
            logger.error(f"解析航班資料失敗: {str(e)}")
            return [] 