from fastapi import APIRouter
from .endpoints import stocks, crawler, health

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(health.router, prefix="/health", tags=["健康检查"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["股票数据"])
api_router.include_router(crawler.router, prefix="/crawler", tags=["数据爬取"])

# 保持向后兼容
router = api_router