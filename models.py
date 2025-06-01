from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import json

@dataclass
class FlightInfo:
    """航班資訊資料模型"""
    
    # 基本航班資訊
    flight_number: str              # 航班號碼
    airline: str = "Tigerair Taiwan"  # 航空公司
    
    # 出發資訊
    departure_airport: str = ""     # 出發機場代碼
    departure_city: str = ""        # 出發城市
    departure_time: str = ""        # 出發時間
    departure_date: str = ""        # 出發日期
    
    # 抵達資訊  
    arrival_airport: str = ""       # 抵達機場代碼
    arrival_city: str = ""          # 抵達城市
    arrival_time: str = ""          # 抵達時間
    arrival_date: str = ""          # 抵達日期
    
    # 票價資訊
    price: Optional[float] = None   # 票價
    currency: str = "TWD"           # 幣別
    fare_type: str = ""             # 票價類型（經濟艙、商務艙等）
    
    # 座位資訊
    seats_available: Optional[bool] = None  # 是否有空位
    seats_count: Optional[int] = None       # 剩餘座位數
    
    # 其他資訊
    flight_duration: str = ""       # 飛行時間
    aircraft_type: str = ""         # 機型
    time_slot: str = ""             # 時間區間（早班/上午/下午/晚班）
    
    # 爬取資訊
    crawl_timestamp: str = ""       # 爬取時間戳記
    source_url: str = ""            # 來源網址
    
    def __post_init__(self):
        """初始化後處理"""
        if not self.crawl_timestamp:
            self.crawl_timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'flight_number': self.flight_number,
            'airline': self.airline,
            'departure_airport': self.departure_airport,
            'departure_city': self.departure_city,
            'departure_time': self.departure_time,
            'departure_date': self.departure_date,
            'arrival_airport': self.arrival_airport,
            'arrival_city': self.arrival_city,
            'arrival_time': self.arrival_time,
            'arrival_date': self.arrival_date,
            'price': self.price,
            'currency': self.currency,
            'fare_type': self.fare_type,
            'seats_available': self.seats_available,
            'seats_count': self.seats_count,
            'flight_duration': self.flight_duration,
            'aircraft_type': self.aircraft_type,
            'time_slot': self.time_slot,
            'crawl_timestamp': self.crawl_timestamp,
            'source_url': self.source_url
        }
    
    def to_json(self) -> str:
        """轉換為JSON格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

class FlightSearchResult:
    """航班搜尋結果集合"""
    
    def __init__(self):
        self.flights: List[FlightInfo] = []
        self.search_params = {}
        self.total_count = 0
        self.success_count = 0
        self.error_count = 0
        self.errors: List[str] = []
    
    def add_flight(self, flight: FlightInfo):
        """新增航班資訊"""
        self.flights.append(flight)
        self.total_count += 1
        self.success_count += 1
    
    def add_error(self, error_msg: str):
        """新增錯誤訊息"""
        self.errors.append(error_msg)
        self.error_count += 1
    
    def get_flights_by_time_slot(self, time_slot: str) -> List[FlightInfo]:
        """根據時間區間篩選航班"""
        return [flight for flight in self.flights if flight.time_slot == time_slot]
    
    def get_available_flights(self) -> List[FlightInfo]:
        """取得有空位的航班"""
        return [flight for flight in self.flights if flight.seats_available]
    
    def get_cheapest_flights(self, limit: int = 5) -> List[FlightInfo]:
        """取得最便宜的航班"""
        available_flights = [f for f in self.flights if f.price is not None and f.seats_available]
        return sorted(available_flights, key=lambda x: x.price)[:limit]
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'flights': [flight.to_dict() for flight in self.flights],
            'search_params': self.search_params,
            'summary': {
                'total_count': self.total_count,
                'success_count': self.success_count,
                'error_count': self.error_count,
                'errors': self.errors
            }
        }
    
    def to_json(self) -> str:
        """轉換為JSON格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) 