from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import asyncio
import uvicorn

from tigerair_scraper import TigerairScraper
from config import TigerairConfig
from models import FlightInfo, FlightSearchResult

app = FastAPI(
    title="虎航機票爬蟲 API",
    description="台灣虎航到日本航班資訊查詢API",
    version="1.0.0"
)

# 允許跨域請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 請求模型
class FlightSearchRequest(BaseModel):
    departure: str
    arrival: str
    departure_date: str
    return_date: Optional[str] = None

class MultipleRoutesRequest(BaseModel):
    routes: List[str]
    dates: List[str]

# 回應模型
class FlightInfoResponse(BaseModel):
    flight_number: str
    departure_time: str
    arrival_time: str
    departure_date: str
    price: Optional[float]
    seats_available: Optional[bool]
    time_slot: str

@app.get("/")
async def root():
    """API根路徑"""
    return {
        "message": "虎航機票爬蟲 API",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/routes")
async def get_routes():
    """取得支援的航線"""
    return {"routes": TigerairConfig.ROUTES}

@app.post("/search")
async def search_flights(request: FlightSearchRequest):
    """搜尋單一航線航班"""
    try:
        scraper = TigerairScraper(headless=True)
        result = scraper.search_flights(
            departure=request.departure,
            arrival=request.arrival,
            departure_date=request.departure_date,
            return_date=request.return_date
        )
        
        flights = [
            FlightInfoResponse(
                flight_number=flight.flight_number,
                departure_time=flight.departure_time,
                arrival_time=flight.arrival_time,
                departure_date=flight.departure_date,
                price=flight.price,
                seats_available=flight.seats_available,
                time_slot=flight.time_slot
            ) for flight in result.flights
        ]
        
        return {
            "success": True,
            "flights": flights,
            "total_count": len(flights),
            "search_params": result.search_params
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/multiple")
async def search_multiple_routes(request: MultipleRoutesRequest):
    """搜尋多條航線"""
    try:
        scraper = TigerairScraper(headless=True)
        results = scraper.search_multiple_routes(
            routes=request.routes,
            dates=request.dates
        )
        
        response_data = {}
        for route, result in results.items():
            flights = [
                FlightInfoResponse(
                    flight_number=flight.flight_number,
                    departure_time=flight.departure_time,
                    arrival_time=flight.arrival_time,
                    departure_date=flight.departure_date,
                    price=flight.price,
                    seats_available=flight.seats_available,
                    time_slot=flight.time_slot
                ) for flight in result.flights
            ]
            
            response_data[route] = {
                "route_name": TigerairConfig.ROUTES[route]["route_name"],
                "flights": flights,
                "total_count": len(flights),
                "available_count": len(result.get_available_flights())
            }
        
        return {
            "success": True,
            "results": response_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 