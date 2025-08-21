"""MCP工具实现

提供各种数据查询和管理工具的MCP接口实现。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models import Stock, StockBasic, StockDaily
from app.models.dragon_tiger import DragonTiger, DragonTigerSummary
from app.services.crawler_service import CrawlerService
from app.core.logging import get_logger

logger = get_logger('mcp.tools')


class StockDataTool:
    """股票数据工具
    
    提供股票基础数据查询功能的MCP工具实现。
    """
    
    async def get_stocks(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        market: Optional[str] = None,
        industry: Optional[str] = None,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """获取股票列表
        
        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            market: 市场类型筛选
            industry: 行业筛选
            is_active: 是否只返回活跃股票
            
        Returns:
            包含股票列表和统计信息的字典
        """
        try:
            query = db.query(Stock)
            
            if is_active is not None:
                query = query.filter(Stock.is_active == is_active)
            if market:
                query = query.filter(Stock.market == market)
            if industry:
                query = query.filter(Stock.industry == industry)
            
            total = query.count()
            stocks = query.offset(skip).limit(limit).all()
            
            return {
                "stocks": [
                    {
                        "ts_code": stock.ts_code,
                        "symbol": stock.symbol,
                        "name": stock.name,
                        "area": stock.area,
                        "industry": stock.industry,
                        "market": stock.market,
                        "list_date": stock.list_date.isoformat() if stock.list_date else None,
                        "is_active": stock.is_active
                    }
                    for stock in stocks
                ],
                "total": total,
                "skip": skip,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise
    
    async def get_stock_detail(
        self,
        db: Session,
        ts_code: str
    ) -> Dict[str, Any]:
        """获取股票详细信息
        
        Args:
            db: 数据库会话
            ts_code: 股票代码
            
        Returns:
            股票详细信息字典
        """
        try:
            # 获取基本信息
            stock = db.query(Stock).filter(Stock.ts_code == ts_code).first()
            if not stock:
                raise ValueError(f"股票 {ts_code} 不存在")
            
            # 获取基础数据
            basic = db.query(StockBasic).filter(StockBasic.ts_code == ts_code).first()
            
            # 获取最新日线数据
            latest_daily = db.query(StockDaily).filter(
                StockDaily.ts_code == ts_code
            ).order_by(desc(StockDaily.trade_date)).first()
            
            result = {
                "basic_info": {
                    "ts_code": stock.ts_code,
                    "symbol": stock.symbol,
                    "name": stock.name,
                    "area": stock.area,
                    "industry": stock.industry,
                    "market": stock.market,
                    "list_date": stock.list_date.isoformat() if stock.list_date else None,
                    "is_active": stock.is_active
                }
            }
            
            if basic:
                result["financial_info"] = {
                    "total_share": basic.total_share,
                    "float_share": basic.float_share,
                    "free_share": basic.free_share,
                    "total_assets": basic.total_assets,
                    "liquid_assets": basic.liquid_assets,
                    "fixed_assets": basic.fixed_assets,
                    "reserved": basic.reserved,
                    "reserved_pershare": basic.reserved_pershare,
                    "eps": basic.eps,
                    "bvps": basic.bvps,
                    "pb": basic.pb,
                    "pe": basic.pe,
                    "pe_ttm": basic.pe_ttm,
                    "updated_at": basic.updated_at.isoformat() if basic.updated_at else None
                }
            
            if latest_daily:
                result["latest_price"] = {
                    "trade_date": latest_daily.trade_date.isoformat(),
                    "open": latest_daily.open,
                    "high": latest_daily.high,
                    "low": latest_daily.low,
                    "close": latest_daily.close,
                    "pre_close": latest_daily.pre_close,
                    "change": latest_daily.change,
                    "pct_chg": latest_daily.pct_chg,
                    "vol": latest_daily.vol,
                    "amount": latest_daily.amount
                }
            
            return result
            
        except Exception as e:
            logger.error(f"获取股票详细信息失败: {e}")
            raise


class DragonTigerTool:
    """龙虎榜数据工具
    
    提供龙虎榜数据查询功能的MCP工具实现。
    """
    
    async def get_summary(
        self,
        db: Session,
        trade_date: Optional[str] = None,
        stock_code: Optional[str] = None,
        reason: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取龙虎榜汇总数据
        
        Args:
            db: 数据库会话
            trade_date: 交易日期
            stock_code: 股票代码
            reason: 上榜原因关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            龙虎榜汇总数据字典
        """
        try:
            query = db.query(DragonTigerSummary)
            
            # 筛选条件
            if trade_date:
                try:
                    date_obj = datetime.strptime(trade_date, '%Y-%m-%d').date()
                    query = query.filter(DragonTigerSummary.trade_date == date_obj)
                except ValueError:
                    raise ValueError("日期格式错误，请使用YYYY-MM-DD格式")
            
            if stock_code:
                query = query.filter(DragonTigerSummary.stock_code == stock_code)
            
            if reason:
                query = query.filter(DragonTigerSummary.reason.contains(reason))
            
            # 获取总数
            total = query.count()
            
            # 分页和排序
            offset = (page - 1) * page_size
            items = query.order_by(
                desc(DragonTigerSummary.trade_date),
                desc(DragonTigerSummary.net_buy_amount)
            ).offset(offset).limit(page_size).all()
            
            return {
                "items": [
                    {
                        "trade_date": item.trade_date.isoformat(),
                        "stock_code": item.stock_code,
                        "stock_name": item.stock_name,
                        "close_price": item.close_price,
                        "change_percent": item.change_percent,
                        "turnover_rate": item.turnover_rate,
                        "net_buy_amount": item.net_buy_amount,
                        "buy_amount": item.buy_amount,
                        "sell_amount": item.sell_amount,
                        "total_amount": item.total_amount,
                        "reason": item.reason,
                        "buy_count": item.buy_count,
                        "sell_count": item.sell_count,
                        "institution_buy_count": item.institution_buy_count,
                        "institution_sell_count": item.institution_sell_count
                    }
                    for item in items
                ],
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"获取龙虎榜汇总数据失败: {e}")
            raise
    
    async def get_detail(
        self,
        db: Session,
        stock_code: str,
        trade_date: Optional[str] = None,
        trade_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取龙虎榜详细数据
        
        Args:
            db: 数据库会话
            stock_code: 股票代码
            trade_date: 交易日期
            trade_type: 交易类型
            page: 页码
            page_size: 每页数量
            
        Returns:
            龙虎榜详细数据字典
        """
        try:
            query = db.query(DragonTiger).filter(DragonTiger.stock_code == stock_code)
            
            # 筛选条件
            if trade_date:
                try:
                    date_obj = datetime.strptime(trade_date, '%Y-%m-%d').date()
                    query = query.filter(DragonTiger.trade_date == date_obj)
                except ValueError:
                    raise ValueError("日期格式错误，请使用YYYY-MM-DD格式")
            
            if trade_type:
                if trade_type not in ['buy', 'sell']:
                    raise ValueError("交易类型只能是buy或sell")
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
            
            return {
                "items": [
                    {
                        "trade_date": item.trade_date.isoformat(),
                        "stock_code": item.stock_code,
                        "stock_name": item.stock_name,
                        "close_price": item.close_price,
                        "change_percent": item.change_percent,
                        "turnover_rate": item.turnover_rate,
                        "reason": item.reason,
                        "trade_type": item.trade_type,
                        "rank": item.rank,
                        "department": item.department,
                        "buy_amount": item.buy_amount,
                        "buy_percent": item.buy_percent,
                        "sell_amount": item.sell_amount,
                        "sell_percent": item.sell_percent,
                        "net_buy_amount": item.net_buy_amount,
                        "is_institution": item.is_institution
                    }
                    for item in items
                ],
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"获取龙虎榜详细数据失败: {e}")
            raise


class CrawlerTool:
    """爬虫管理工具
    
    提供数据爬取任务管理功能的MCP工具实现。
    """
    
    async def start_crawler(
        self,
        db: Session,
        crawler_type: str = "basic",
        ts_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """启动数据爬取任务
        
        Args:
            db: 数据库会话
            crawler_type: 爬虫类型
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            任务启动结果字典
        """
        try:
            crawler_service = CrawlerService(db)
            
            if crawler_type == "basic":
                # 爬取股票基本信息
                await crawler_service.crawl_stock_basic()
                return {
                    "message": "股票基本信息爬取任务已完成",
                    "type": "basic",
                    "status": "success"
                }
            
            elif crawler_type == "daily":
                # 爬取日线数据
                if ts_code:
                    await crawler_service.crawl_stock_daily_single(ts_code, start_date, end_date)
                    return {
                        "message": f"股票 {ts_code} 日线数据爬取任务已完成",
                        "type": "daily",
                        "ts_code": ts_code,
                        "status": "success"
                    }
                else:
                    await crawler_service.crawl_stock_daily_all(start_date, end_date)
                    return {
                        "message": "全市场日线数据爬取任务已完成",
                        "type": "daily",
                        "status": "success"
                    }
            
            elif crawler_type == "all":
                # 全量爬取
                await crawler_service.crawl_all_data()
                return {
                    "message": "全量数据爬取任务已完成",
                    "type": "all",
                    "status": "success"
                }
            
            else:
                raise ValueError(f"不支持的爬虫类型: {crawler_type}")
                
        except Exception as e:
            logger.error(f"启动爬虫任务失败: {e}")
            return {
                "message": f"爬虫任务启动失败: {str(e)}",
                "type": crawler_type,
                "status": "error"
            }