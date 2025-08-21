import asyncio
import time
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from loguru import logger
from datetime import datetime, timedelta

from app.models import Stock, StockBasic, StockDaily
from app.core.config import settings
from app.services.data_sources import TushareDataSource
# from app.services.data_sources import AkshareDataSource  # 暂时注释掉

class CrawlerService:
    """数据爬取服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.tushare_source = TushareDataSource() if settings.TUSHARE_TOKEN else None
        # self.akshare_source = AkshareDataSource() if settings.AKSHARE_ENABLED else None  # 暂时注释掉
        self.akshare_source = None
        
    async def crawl_stock_basic(self):
        """爬取股票基本信息"""
        logger.info("开始爬取股票基本信息")
        
        try:
            # 优先使用Tushare，备用AKShare
            if self.tushare_source:
                basic_data = await self.tushare_source.get_stock_basic()
            elif self.akshare_source:
                basic_data = await self.akshare_source.get_stock_basic()
            else:
                logger.error("没有可用的数据源")
                return
            
            if not basic_data:
                logger.warning("未获取到股票基本信息")
                return
            
            # 批量插入或更新数据
            updated_count = 0
            for data in basic_data:
                try:
                    # 检查是否已存在
                    existing = self.db.query(StockBasic).filter(
                        StockBasic.ts_code == data['ts_code']
                    ).first()
                    
                    if existing:
                        # 更新现有记录
                        for key, value in data.items():
                            if hasattr(existing, key):
                                setattr(existing, key, value)
                    else:
                        # 创建新记录
                        stock_basic = StockBasic(**data)
                        self.db.add(stock_basic)
                    
                    # 同时更新或创建Stock表记录
                    stock = self.db.query(Stock).filter(
                        Stock.ts_code == data['ts_code']
                    ).first()
                    
                    if not stock:
                        stock = Stock(
                            ts_code=data['ts_code'],
                            symbol=data.get('symbol', ''),
                            name=data.get('name', ''),
                            industry=data.get('industry'),
                            area=data.get('area'),
                            market=data.get('market'),
                            exchange=data.get('exchange'),
                            list_date=data.get('list_date'),
                            is_active=data.get('list_status') == 'L'
                        )
                        self.db.add(stock)
                    else:
                        # 更新基本信息
                        stock.name = data.get('name', stock.name)
                        stock.industry = data.get('industry', stock.industry)
                        stock.area = data.get('area', stock.area)
                        stock.market = data.get('market', stock.market)
                        stock.is_active = data.get('list_status') == 'L'
                    
                    updated_count += 1
                    
                    # 每100条提交一次
                    if updated_count % 100 == 0:
                        self.db.commit()
                        logger.info(f"已处理 {updated_count} 条股票基本信息")
                        
                except Exception as e:
                    logger.error(f"处理股票 {data.get('ts_code')} 基本信息时出错: {e}")
                    continue
            
            self.db.commit()
            logger.info(f"股票基本信息爬取完成，共处理 {updated_count} 条记录")
            
        except Exception as e:
            logger.error(f"爬取股票基本信息失败: {e}")
            self.db.rollback()
    
    async def crawl_stock_daily_single(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """爬取单个股票的日线数据"""
        logger.info(f"开始爬取股票 {ts_code} 的日线数据")
        
        try:
            # 更新股票状态
            stock = self.db.query(Stock).filter(Stock.ts_code == ts_code).first()
            if stock:
                stock.crawl_status = 'crawling'
                self.db.commit()
            
            # 如果没有指定开始日期，获取最后一次数据的日期
            if not start_date:
                last_data = self.db.query(StockDaily).filter(
                    StockDaily.ts_code == ts_code
                ).order_by(StockDaily.trade_date.desc()).first()
                
                if last_data:
                    # 从最后一次数据的下一天开始
                    last_date = datetime.strptime(last_data.trade_date, '%Y%m%d')
                    start_date = (last_date + timedelta(days=1)).strftime('%Y%m%d')
                else:
                    # 如果没有历史数据，从上市日期开始
                    if stock and stock.list_date:
                        start_date = stock.list_date
                    else:
                        start_date = '20100101'  # 默认开始日期
            
            # 获取日线数据
            if self.tushare_source:
                daily_data = await self.tushare_source.get_stock_daily(
                    ts_code, start_date, end_date
                )
            elif self.akshare_source:
                daily_data = await self.akshare_source.get_stock_daily(
                    ts_code, start_date, end_date
                )
            else:
                logger.error("没有可用的数据源")
                return
            
            if not daily_data:
                logger.info(f"股票 {ts_code} 没有新的日线数据")
                if stock:
                    stock.crawl_status = 'completed'
                    stock.last_crawl_date = datetime.now().strftime('%Y%m%d')
                    self.db.commit()
                return
            
            # 批量插入数据
            inserted_count = 0
            for data in daily_data:
                try:
                    # 检查是否已存在
                    existing = self.db.query(StockDaily).filter(
                        and_(
                            StockDaily.ts_code == data['ts_code'],
                            StockDaily.trade_date == data['trade_date']
                        )
                    ).first()
                    
                    if not existing:
                        stock_daily = StockDaily(**data)
                        self.db.add(stock_daily)
                        inserted_count += 1
                    
                    # 每500条提交一次
                    if inserted_count % 500 == 0 and inserted_count > 0:
                        self.db.commit()
                        logger.info(f"股票 {ts_code} 已插入 {inserted_count} 条日线数据")
                        
                except Exception as e:
                    logger.error(f"处理股票 {ts_code} 日期 {data.get('trade_date')} 的数据时出错: {e}")
                    continue
            
            self.db.commit()
            
            # 更新股票状态和最新价格
            if stock and daily_data:
                latest_data = max(daily_data, key=lambda x: x['trade_date'])
                stock.latest_price = latest_data.get('close')
                stock.latest_date = latest_data.get('trade_date')
                stock.crawl_status = 'completed'
                stock.last_crawl_date = datetime.now().strftime('%Y%m%d')
                stock.error_message = None
                self.db.commit()
            
            logger.info(f"股票 {ts_code} 日线数据爬取完成，新增 {inserted_count} 条记录")
            
        except Exception as e:
            logger.error(f"爬取股票 {ts_code} 日线数据失败: {e}")
            # 更新错误状态
            if stock:
                stock.crawl_status = 'error'
                stock.error_message = str(e)
                self.db.commit()
    
    async def crawl_stock_daily_all(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """爬取所有股票的日线数据"""
        logger.info("开始爬取所有股票的日线数据")
        
        # 获取所有活跃股票
        stocks = self.db.query(Stock).filter(Stock.is_active == True).all()
        total_stocks = len(stocks)
        
        logger.info(f"共需要爬取 {total_stocks} 只股票的数据")
        
        for i, stock in enumerate(stocks, 1):
            try:
                logger.info(f"正在爬取第 {i}/{total_stocks} 只股票: {stock.ts_code} {stock.name}")
                
                await self.crawl_stock_daily_single(
                    stock.ts_code, start_date, end_date
                )
                
                # 添加延迟避免请求过于频繁
                await asyncio.sleep(settings.CRAWLER_DELAY)
                
            except Exception as e:
                logger.error(f"爬取股票 {stock.ts_code} 时出错: {e}")
                continue
        
        logger.info("所有股票日线数据爬取完成")
    
    async def crawl_all_data(self):
        """全量数据爬取"""
        logger.info("开始全量数据爬取")
        
        # 1. 先爬取股票基本信息
        await self.crawl_stock_basic()
        
        # 2. 再爬取所有日线数据
        await self.crawl_stock_daily_all()
        
        logger.info("全量数据爬取完成")
    
    async def update_stock_basic(self, ts_code: str):
        """更新单个股票基本信息"""
        logger.info(f"更新股票 {ts_code} 基本信息")
        
        try:
            if self.tushare_source:
                basic_data = await self.tushare_source.get_stock_basic(ts_code)
            elif self.akshare_source:
                basic_data = await self.akshare_source.get_stock_basic(ts_code)
            else:
                logger.error("没有可用的数据源")
                return
            
            if basic_data:
                data = basic_data[0]  # 单个股票数据
                
                # 更新StockBasic表
                existing = self.db.query(StockBasic).filter(
                    StockBasic.ts_code == ts_code
                ).first()
                
                if existing:
                    for key, value in data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                else:
                    stock_basic = StockBasic(**data)
                    self.db.add(stock_basic)
                
                # 更新Stock表
                stock = self.db.query(Stock).filter(Stock.ts_code == ts_code).first()
                if stock:
                    stock.name = data.get('name', stock.name)
                    stock.industry = data.get('industry', stock.industry)
                    stock.area = data.get('area', stock.area)
                    stock.is_active = data.get('list_status') == 'L'
                
                self.db.commit()
                logger.info(f"股票 {ts_code} 基本信息更新完成")
            
        except Exception as e:
            logger.error(f"更新股票 {ts_code} 基本信息失败: {e}")
            self.db.rollback()
    
    async def update_stock_all(self, ts_code: str):
        """更新单个股票的所有数据"""
        await self.update_stock_basic(ts_code)
        await self.crawl_stock_daily_single(ts_code)