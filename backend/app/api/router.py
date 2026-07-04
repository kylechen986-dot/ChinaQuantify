from fastapi import APIRouter

from app.api.routes import backtests, indicators, market, reports, stocks, strategies, system

api_router = APIRouter()
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(indicators.router, prefix="/indicators", tags=["indicators"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(backtests.router, prefix="/backtests", tags=["backtests"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
