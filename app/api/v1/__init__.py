from fastapi import APIRouter
from .dragon_tiger import router as dragon_tiger_router

api_router = APIRouter()

# 注册龙虎榜路由
api_router.include_router(dragon_tiger_router)

__all__ = ["api_router"]