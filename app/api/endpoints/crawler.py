from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.crawler_service import CrawlerService
from app.models import Stock
from datetime import datetime

router = APIRouter()

@router.post("/start")
async def start_crawler(
    background_tasks: BackgroundTasks,
    crawler_type: str = "basic",  # basic, daily, all
    ts_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """启动数据爬取任务"""
    crawler_service = CrawlerService(db)
    
    if crawler_type == "basic":
        # 爬取股票基本信息
        background_tasks.add_task(crawler_service.crawl_stock_basic)
        return {"message": "股票基本信息爬取任务已启动", "type": "basic"}
    
    elif crawler_type == "daily":
        # 爬取日线数据
        if ts_code:
            background_tasks.add_task(
                crawler_service.crawl_stock_daily_single, 
                ts_code, start_date, end_date
            )
            return {
                "message": f"股票 {ts_code} 日线数据爬取任务已启动", 
                "type": "daily",
                "ts_code": ts_code
            }
        else:
            background_tasks.add_task(
                crawler_service.crawl_stock_daily_all, 
                start_date, end_date
            )
            return {"message": "全市场日线数据爬取任务已启动", "type": "daily"}
    
    elif crawler_type == "all":
        # 全量爬取
        background_tasks.add_task(crawler_service.crawl_all_data)
        return {"message": "全量数据爬取任务已启动", "type": "all"}
    
    else:
        raise HTTPException(status_code=400, detail="不支持的爬取类型")

@router.get("/status")
async def get_crawler_status(db: Session = Depends(get_db)):
    """获取爬虫状态"""
    # 统计各种状态的股票数量
    from sqlalchemy import func
    
    status_stats = db.query(
        Stock.crawl_status,
        func.count(Stock.id).label('count')
    ).group_by(Stock.crawl_status).all()
    
    # 获取最近更新的股票
    recent_updates = db.query(Stock).filter(
        Stock.last_crawl_date.isnot(None)
    ).order_by(Stock.updated_at.desc()).limit(10).all()
    
    # 获取有错误的股票
    error_stocks = db.query(Stock).filter(
        Stock.crawl_status == 'error'
    ).limit(10).all()
    
    return {
        "status_distribution": [
            {"status": status, "count": count} 
            for status, count in status_stats
        ],
        "recent_updates": [
            {
                "ts_code": stock.ts_code,
                "name": stock.name,
                "last_crawl_date": stock.last_crawl_date,
                "status": stock.crawl_status
            }
            for stock in recent_updates
        ],
        "error_stocks": [
            {
                "ts_code": stock.ts_code,
                "name": stock.name,
                "error_message": stock.error_message,
                "updated_at": stock.updated_at.isoformat() if stock.updated_at else None
            }
            for stock in error_stocks
        ],
        "timestamp": datetime.now().isoformat()
    }

@router.post("/update/{ts_code}")
async def update_single_stock(
    ts_code: str,
    background_tasks: BackgroundTasks,
    update_type: str = "daily",  # basic, daily, all
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """更新单个股票数据"""
    # 检查股票是否存在
    stock = db.query(Stock).filter(Stock.ts_code == ts_code).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")
    
    crawler_service = CrawlerService(db)
    
    if update_type == "basic":
        background_tasks.add_task(crawler_service.update_stock_basic, ts_code)
    elif update_type == "daily":
        background_tasks.add_task(
            crawler_service.crawl_stock_daily_single, 
            ts_code, start_date, end_date
        )
    elif update_type == "all":
        background_tasks.add_task(crawler_service.update_stock_all, ts_code)
    else:
        raise HTTPException(status_code=400, detail="不支持的更新类型")
    
    return {
        "message": f"股票 {ts_code} 的 {update_type} 数据更新任务已启动",
        "ts_code": ts_code,
        "update_type": update_type
    }

@router.delete("/reset/{ts_code}")
async def reset_stock_status(
    ts_code: str,
    db: Session = Depends(get_db)
):
    """重置股票爬取状态"""
    stock = db.query(Stock).filter(Stock.ts_code == ts_code).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")
    
    stock.crawl_status = "pending"
    stock.error_message = None
    db.commit()
    
    return {
        "message": f"股票 {ts_code} 的爬取状态已重置",
        "ts_code": ts_code
    }

@router.get("/progress")
async def get_crawl_progress(db: Session = Depends(get_db)):
    """获取爬取进度"""
    from sqlalchemy import func
    
    total_stocks = db.query(Stock).count()
    completed_stocks = db.query(Stock).filter(
        Stock.crawl_status == 'completed'
    ).count()
    error_stocks = db.query(Stock).filter(
        Stock.crawl_status == 'error'
    ).count()
    pending_stocks = db.query(Stock).filter(
        Stock.crawl_status == 'pending'
    ).count()
    
    progress_percentage = (completed_stocks / total_stocks * 100) if total_stocks > 0 else 0
    
    return {
        "total_stocks": total_stocks,
        "completed": completed_stocks,
        "error": error_stocks,
        "pending": pending_stocks,
        "progress_percentage": round(progress_percentage, 2),
        "timestamp": datetime.now().isoformat()
    }