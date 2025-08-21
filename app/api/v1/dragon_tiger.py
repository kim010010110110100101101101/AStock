from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.dragon_tiger import DragonTiger, DragonTigerSummary
from app.schemas.dragon_tiger import (
    DragonTigerListResponse,
    DragonTigerSummaryListResponse,
    DragonTigerResponse,
    DragonTigerSummaryResponse,
    DragonTigerStatsResponse
)
from app.services.data_sources.tonghuashun import crawl_today_dragon_tiger

logger = get_logger('api')
router = APIRouter(prefix="/dragon-tiger", tags=["龙虎榜"])


@router.get("/summary", response_model=DragonTigerSummaryListResponse, summary="获取龙虎榜汇总数据")
async def get_dragon_tiger_summary(
    trade_date: Optional[str] = Query(None, description="交易日期，格式YYYY-MM-DD，默认为最新交易日"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    reason: Optional[str] = Query(None, description="上榜原因关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取龙虎榜汇总数据"""
    try:
        query = db.query(DragonTigerSummary)
        
        # 筛选条件
        if trade_date:
            try:
                date_obj = datetime.strptime(trade_date, '%Y-%m-%d').date()
                query = query.filter(DragonTigerSummary.trade_date == date_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
        
        if stock_code:
            query = query.filter(DragonTigerSummary.stock_code == stock_code)
        
        if reason:
            query = query.filter(DragonTigerSummary.reason.contains(reason))
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        offset = (page - 1) * page_size
        items = query.order_by(desc(DragonTigerSummary.trade_date), desc(DragonTigerSummary.net_buy_amount)).offset(offset).limit(page_size).all()
        
        return DragonTigerSummaryListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取龙虎榜汇总数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取数据失败")


@router.get("/detail", response_model=DragonTigerListResponse, summary="获取龙虎榜详细数据")
async def get_dragon_tiger_detail(
    stock_code: str = Query(..., description="股票代码"),
    trade_date: Optional[str] = Query(None, description="交易日期，格式YYYY-MM-DD"),
    trade_type: Optional[str] = Query(None, description="交易类型：buy/sell"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取龙虎榜详细数据"""
    try:
        query = db.query(DragonTiger).filter(DragonTiger.stock_code == stock_code)
        
        # 筛选条件
        if trade_date:
            try:
                date_obj = datetime.strptime(trade_date, '%Y-%m-%d').date()
                query = query.filter(DragonTiger.trade_date == date_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
        
        if trade_type:
            if trade_type not in ['buy', 'sell']:
                raise HTTPException(status_code=400, detail="交易类型只能是buy或sell")
            query = query.filter(DragonTiger.trade_type == trade_type)
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        offset = (page - 1) * page_size
        items = query.order_by(
            desc(DragonTiger.trade_date),
            DragonTiger.trade_type,
            DragonTiger.rank
        ).offset(offset).limit(page_size).all()
        
        return DragonTigerListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取龙虎榜详细数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取数据失败")


@router.get("/stats", response_model=DragonTigerStatsResponse, summary="获取龙虎榜统计数据")
async def get_dragon_tiger_stats(
    start_date: Optional[str] = Query(None, description="开始日期，格式YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """获取龙虎榜统计数据"""
    try:
        # 构建基础查询
        summary_query = db.query(DragonTigerSummary)
        detail_query = db.query(DragonTiger)
        
        # 日期筛选
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                summary_query = summary_query.filter(DragonTigerSummary.trade_date >= start_date_obj)
                detail_query = detail_query.filter(DragonTiger.trade_date >= start_date_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="开始日期格式错误")
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                summary_query = summary_query.filter(DragonTigerSummary.trade_date <= end_date_obj)
                detail_query = detail_query.filter(DragonTiger.trade_date <= end_date_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="结束日期格式错误")
        
        # 统计数据
        total_stocks = summary_query.count()
        total_records = detail_query.count()
        
        # 按日期统计
        daily_stats = summary_query.with_entities(
            DragonTigerSummary.trade_date,
            func.count(DragonTigerSummary.id).label('count'),
            func.sum(DragonTigerSummary.net_buy_amount).label('total_net_buy')
        ).group_by(DragonTigerSummary.trade_date).order_by(desc(DragonTigerSummary.trade_date)).limit(10).all()
        
        # 按上榜原因统计
        reason_stats = summary_query.with_entities(
            DragonTigerSummary.reason,
            func.count(DragonTigerSummary.id).label('count')
        ).group_by(DragonTigerSummary.reason).order_by(desc(func.count(DragonTigerSummary.id))).limit(10).all()
        
        # 最新交易日
        latest_date = summary_query.with_entities(
            func.max(DragonTigerSummary.trade_date)
        ).scalar()
        
        return DragonTigerStatsResponse(
            total_stocks=total_stocks,
            total_records=total_records,
            latest_date=latest_date.strftime('%Y-%m-%d') if latest_date else None,
            daily_stats=[
                {
                    'date': stat.trade_date.strftime('%Y-%m-%d'),
                    'count': stat.count,
                    'total_net_buy': float(stat.total_net_buy) if stat.total_net_buy else 0
                }
                for stat in daily_stats
            ],
            reason_stats=[
                {
                    'reason': stat.reason,
                    'count': stat.count
                }
                for stat in reason_stats
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取龙虎榜统计数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计数据失败")


@router.post("/crawl", summary="手动爬取龙虎榜数据")
async def manual_crawl_dragon_tiger():
    """手动触发爬取今日龙虎榜数据"""
    try:
        logger.info("手动触发龙虎榜数据爬取")
        result = await crawl_today_dragon_tiger()
        
        if result['success']:
            return {
                'success': True,
                'message': result['message'],
                'data': {
                    'trade_date': result['trade_date'],
                    'summary_count': result['summary_count'],
                    'detail_count': result['detail_count']
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动爬取龙虎榜数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}")


@router.get("/latest", response_model=DragonTigerSummaryListResponse, summary="获取最新龙虎榜数据")
async def get_latest_dragon_tiger(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取最新龙虎榜数据"""
    try:
        # 获取最新交易日
        latest_date = db.query(func.max(DragonTigerSummary.trade_date)).scalar()
        
        if not latest_date:
            return DragonTigerSummaryListResponse(
                items=[],
                total=0,
                page=1,
                page_size=limit,
                pages=0
            )
        
        # 获取最新交易日的数据
        items = db.query(DragonTigerSummary).filter(
            DragonTigerSummary.trade_date == latest_date
        ).order_by(desc(DragonTigerSummary.net_buy_amount)).limit(limit).all()
        
        total = db.query(DragonTigerSummary).filter(
            DragonTigerSummary.trade_date == latest_date
        ).count()
        
        return DragonTigerSummaryListResponse(
            items=items,
            total=total,
            page=1,
            page_size=limit,
            pages=1
        )
        
    except Exception as e:
        logger.error(f"获取最新龙虎榜数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取数据失败")


@router.get("/stock/{stock_code}", response_model=DragonTigerSummaryListResponse, summary="获取个股龙虎榜历史")
async def get_stock_dragon_tiger_history(
    stock_code: str,
    days: int = Query(30, ge=1, le=365, description="查询天数"),
    db: Session = Depends(get_db)
):
    """获取个股龙虎榜历史数据"""
    try:
        # 计算开始日期
        end_date = datetime.now().date()
        start_date = end_date - datetime.timedelta(days=days)
        
        items = db.query(DragonTigerSummary).filter(
            and_(
                DragonTigerSummary.stock_code == stock_code,
                DragonTigerSummary.trade_date >= start_date,
                DragonTigerSummary.trade_date <= end_date
            )
        ).order_by(desc(DragonTigerSummary.trade_date)).all()
        
        total = len(items)
        
        return DragonTigerSummaryListResponse(
            items=items,
            total=total,
            page=1,
            page_size=total,
            pages=1
        )
        
    except Exception as e:
        logger.error(f"获取个股龙虎榜历史失败: {e}")
        raise HTTPException(status_code=500, detail="获取数据失败")