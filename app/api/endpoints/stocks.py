from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from app.core.database import get_db
from app.models import Stock, StockBasic, StockDaily
from app.schemas.stock import StockResponse, StockDailyResponse, StockBasicResponse
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/", response_model=List[StockResponse])
async def get_stocks(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    market: Optional[str] = Query(None, description="市场类型筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    is_active: Optional[bool] = Query(True, description="是否只返回活跃股票"),
    db: Session = Depends(get_db)
):
    """获取股票列表"""
    query = db.query(Stock)
    
    if is_active is not None:
        query = query.filter(Stock.is_active == is_active)
    if market:
        query = query.filter(Stock.market == market)
    if industry:
        query = query.filter(Stock.industry == industry)
    
    stocks = query.offset(skip).limit(limit).all()
    return stocks

@router.get("/{ts_code}", response_model=StockResponse)
async def get_stock(ts_code: str, db: Session = Depends(get_db)):
    """获取单个股票信息"""
    stock = db.query(Stock).filter(Stock.ts_code == ts_code).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")
    return stock

@router.get("/{ts_code}/basic", response_model=StockBasicResponse)
async def get_stock_basic(ts_code: str, db: Session = Depends(get_db)):
    """获取股票基本信息"""
    basic = db.query(StockBasic).filter(StockBasic.ts_code == ts_code).first()
    if not basic:
        raise HTTPException(status_code=404, detail="股票基本信息不存在")
    return basic

@router.get("/{ts_code}/daily", response_model=List[StockDailyResponse])
async def get_stock_daily(
    ts_code: str,
    start_date: Optional[str] = Query(None, description="开始日期(YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="结束日期(YYYYMMDD)"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    db: Session = Depends(get_db)
):
    """获取股票日线数据"""
    query = db.query(StockDaily).filter(StockDaily.ts_code == ts_code)
    
    if start_date:
        query = query.filter(StockDaily.trade_date >= start_date)
    if end_date:
        query = query.filter(StockDaily.trade_date <= end_date)
    
    daily_data = query.order_by(desc(StockDaily.trade_date)).limit(limit).all()
    return daily_data

@router.get("/{ts_code}/latest")
async def get_stock_latest(ts_code: str, db: Session = Depends(get_db)):
    """获取股票最新数据"""
    # 获取最新日线数据
    latest_daily = db.query(StockDaily).filter(
        StockDaily.ts_code == ts_code
    ).order_by(desc(StockDaily.trade_date)).first()
    
    if not latest_daily:
        raise HTTPException(status_code=404, detail="未找到该股票的数据")
    
    # 获取基本信息
    basic = db.query(StockBasic).filter(StockBasic.ts_code == ts_code).first()
    
    return {
        "ts_code": ts_code,
        "name": basic.name if basic else None,
        "industry": basic.industry if basic else None,
        "latest_data": {
            "trade_date": latest_daily.trade_date,
            "close": latest_daily.close,
            "change": latest_daily.change,
            "pct_chg": latest_daily.pct_chg,
            "vol": latest_daily.vol,
            "amount": latest_daily.amount,
            "turnover_rate": latest_daily.turnover_rate,
            "pe": latest_daily.pe,
            "pb": latest_daily.pb
        }
    }

@router.get("/market/summary")
async def get_market_summary(db: Session = Depends(get_db)):
    """获取市场概况"""
    # 统计各市场股票数量
    from sqlalchemy import func
    
    market_stats = db.query(
        StockBasic.market,
        func.count(StockBasic.ts_code).label('count')
    ).group_by(StockBasic.market).all()
    
    # 统计行业分布
    industry_stats = db.query(
        StockBasic.industry,
        func.count(StockBasic.ts_code).label('count')
    ).group_by(StockBasic.industry).order_by(desc('count')).limit(10).all()
    
    # 获取最新交易日期
    latest_date = db.query(StockDaily.trade_date).order_by(
        desc(StockDaily.trade_date)
    ).first()
    
    return {
        "market_distribution": [
            {"market": market, "count": count} 
            for market, count in market_stats
        ],
        "top_industries": [
            {"industry": industry, "count": count} 
            for industry, count in industry_stats
        ],
        "latest_trade_date": latest_date[0] if latest_date else None,
        "total_stocks": db.query(StockBasic).count()
    }