from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Stock
from datetime import datetime

router = APIRouter()

@router.get("/")
async def health_check():
    """基础健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "A股数据爬取系统"
    }

@router.get("/database")
async def database_health(db: Session = Depends(get_db)):
    """数据库连接健康检查"""
    try:
        # 尝试查询股票数量
        stock_count = db.query(Stock).count()
        return {
            "status": "healthy",
            "database": "connected",
            "stock_count": stock_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/detailed")
async def detailed_health(db: Session = Depends(get_db)):
    """详细健康检查"""
    try:
        # 检查各个表的数据量
        from app.models import StockBasic, StockDaily
        
        stock_count = db.query(Stock).count()
        basic_count = db.query(StockBasic).count()
        daily_count = db.query(StockDaily).count()
        
        # 获取最新数据日期
        latest_daily = db.query(StockDaily.trade_date).order_by(StockDaily.trade_date.desc()).first()
        latest_date = latest_daily[0] if latest_daily else None
        
        return {
            "status": "healthy",
            "database": "connected",
            "data_summary": {
                "stocks": stock_count,
                "stock_basic": basic_count,
                "stock_daily": daily_count,
                "latest_data_date": latest_date
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }