import asyncio
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.crawler_service import CrawlerService
from app.services.data_sources.tonghuashun import crawl_today_dragon_tiger

class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        # 配置调度器
        self.scheduler.configure(
            timezone='Asia/Shanghai',
            job_defaults={
                'coalesce': True,  # 合并错过的任务
                'max_instances': 1,  # 同一任务最多同时运行1个实例
                'misfire_grace_time': 300  # 错过任务的宽限时间(秒)
            }
        )
        
        logger.info("任务调度器初始化完成")
    
    def start(self):
        """启动调度器"""
        if not settings.SCHEDULER_ENABLED:
            logger.info("定时任务调度器已禁用")
            return
        
        if self.is_running:
            logger.warning("调度器已在运行中")
            return
        
        try:
            # 添加定时任务
            self._add_jobs()
            
            # 启动调度器
            self.scheduler.start()
            self.is_running = True
            
            logger.info("任务调度器启动成功")
            
        except Exception as e:
            logger.error(f"启动任务调度器失败: {e}")
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("任务调度器已停止")
            
        except Exception as e:
            logger.error(f"停止任务调度器失败: {e}")
    
    def _add_jobs(self):
        """添加定时任务"""
        # 1. 每日股票基本信息更新 - 每天早上8点
        self.scheduler.add_job(
            func=self._update_stock_basic_job,
            trigger=CronTrigger(hour=8, minute=0),
            id='daily_stock_basic_update',
            name='每日股票基本信息更新',
            replace_existing=True
        )
        
        # 2. 每日股票数据更新 - 根据配置时间
        update_time = settings.DAILY_UPDATE_TIME.split(':')
        hour = int(update_time[0])
        minute = int(update_time[1]) if len(update_time) > 1 else 0
        
        self.scheduler.add_job(
            func=self._update_daily_data_job,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_stock_data_update',
            name='每日股票数据更新',
            replace_existing=True
        )
        
        # 3. 增量数据更新 - 交易时间内每30分钟
        self.scheduler.add_job(
            func=self._incremental_update_job,
            trigger=CronTrigger(
                day_of_week='mon-fri',  # 工作日
                hour='9-11,13-15',      # 交易时间
                minute='*/30'           # 每30分钟
            ),
            id='incremental_data_update',
            name='增量数据更新',
            replace_existing=True
        )
        
        # 4. 数据库清理任务 - 每周日凌晨2点
        self.scheduler.add_job(
            func=self._database_cleanup_job,
            trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
            id='database_cleanup',
            name='数据库清理任务',
            replace_existing=True
        )
        
        # 5. 龙虎榜数据爬取 - 每个交易日下午6点
        self.scheduler.add_job(
            func=self._crawl_dragon_tiger_job,
            trigger=CronTrigger(
                day_of_week='mon-fri',  # 工作日
                hour=18,                # 下午6点
                minute=0
            ),
            id='dragon_tiger_crawl',
            name='龙虎榜数据爬取',
            replace_existing=True
        )
        
        # 6. 健康检查任务 - 每小时
        self.scheduler.add_job(
            func=self._health_check_job,
            trigger=IntervalTrigger(hours=1),
            id='health_check',
            name='系统健康检查',
            replace_existing=True
        )
        
        logger.info("定时任务添加完成")
    
    async def _update_stock_basic_job(self):
        """更新股票基本信息任务"""
        logger.info("开始执行每日股票基本信息更新任务")
        
        db = SessionLocal()
        try:
            crawler_service = CrawlerService(db)
            await crawler_service.crawl_stock_basic()
            logger.info("每日股票基本信息更新任务完成")
            
        except Exception as e:
            logger.error(f"每日股票基本信息更新任务失败: {e}")
        finally:
            db.close()
    
    async def _update_daily_data_job(self):
        """更新每日股票数据任务"""
        logger.info("开始执行每日股票数据更新任务")
        
        db = SessionLocal()
        try:
            crawler_service = CrawlerService(db)
            
            # 获取昨天的日期作为更新日期
            from datetime import datetime, timedelta
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            
            await crawler_service.crawl_stock_daily_all(
                start_date=yesterday,
                end_date=yesterday
            )
            
            logger.info("每日股票数据更新任务完成")
            
        except Exception as e:
            logger.error(f"每日股票数据更新任务失败: {e}")
        finally:
            db.close()
    
    async def _incremental_update_job(self):
        """增量数据更新任务"""
        logger.info("开始执行增量数据更新任务")
        
        # 检查是否为交易日
        if not await self._is_trading_day():
            logger.info("今日非交易日，跳过增量更新")
            return
        
        db = SessionLocal()
        try:
            crawler_service = CrawlerService(db)
            
            # 获取今天的日期
            today = datetime.now().strftime('%Y%m%d')
            
            # 只更新部分活跃股票的数据
            from app.models import Stock
            active_stocks = db.query(Stock).filter(
                Stock.is_active == True
            ).limit(100).all()  # 限制数量避免过载
            
            for stock in active_stocks:
                try:
                    await crawler_service.crawl_stock_daily_single(
                        stock.ts_code, today, today
                    )
                    # 添加延迟
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"更新股票 {stock.ts_code} 增量数据失败: {e}")
                    continue
            
            logger.info("增量数据更新任务完成")
            
        except Exception as e:
            logger.error(f"增量数据更新任务失败: {e}")
        finally:
            db.close()
    
    async def _database_cleanup_job(self):
        """数据库清理任务"""
        logger.info("开始执行数据库清理任务")
        
        db = SessionLocal()
        try:
            # 清理错误状态的股票记录
            from app.models import Stock
            
            # 重置长时间处于错误状态的股票
            error_stocks = db.query(Stock).filter(
                Stock.crawl_status == 'error'
            ).all()
            
            reset_count = 0
            for stock in error_stocks:
                # 如果错误时间超过7天，重置状态
                if stock.updated_at:
                    days_since_error = (datetime.now() - stock.updated_at).days
                    if days_since_error > 7:
                        stock.crawl_status = 'pending'
                        stock.error_message = None
                        reset_count += 1
            
            if reset_count > 0:
                db.commit()
                logger.info(f"重置了 {reset_count} 个错误状态的股票")
            
            # 可以添加更多清理逻辑，如删除过期数据等
            
            logger.info("数据库清理任务完成")
            
        except Exception as e:
            logger.error(f"数据库清理任务失败: {e}")
        finally:
            db.close()
    
    async def _crawl_dragon_tiger_job(self):
        """龙虎榜数据爬取任务"""
        logger.info("开始执行龙虎榜数据爬取任务")
        
        try:
            # 检查是否为交易日
            if not await self._is_trading_day():
                logger.info("今日非交易日，跳过龙虎榜数据爬取")
                return
            
            # 执行龙虎榜数据爬取
            result = await crawl_today_dragon_tiger()
            
            if result['success']:
                logger.info(
                    f"龙虎榜数据爬取成功: 汇总数据 {result['summary_count']} 条, "
                    f"详细数据 {result['detail_count']} 条"
                )
            else:
                logger.error(f"龙虎榜数据爬取失败: {result['message']}")
                
        except Exception as e:
            logger.error(f"龙虎榜数据爬取任务执行失败: {e}")
    
    async def _health_check_job(self):
        """系统健康检查任务"""
        logger.info("开始执行系统健康检查")
        
        db = SessionLocal()
        try:
            # 检查数据库连接
            from app.models import Stock
            stock_count = db.query(Stock).count()
            
            # 检查最近的数据更新情况
            from app.models import StockDaily
            from sqlalchemy import desc
            
            latest_data = db.query(StockDaily.trade_date).order_by(
                desc(StockDaily.trade_date)
            ).first()
            
            latest_date = latest_data[0] if latest_data else None
            
            # 检查是否有数据更新延迟
            if latest_date:
                latest_datetime = datetime.strptime(latest_date, '%Y%m%d')
                days_behind = (datetime.now() - latest_datetime).days
                
                if days_behind > 3:  # 数据延迟超过3天
                    logger.warning(f"数据更新延迟 {days_behind} 天，最新数据日期: {latest_date}")
                else:
                    logger.info(f"数据更新正常，最新数据日期: {latest_date}")
            
            logger.info(f"系统健康检查完成 - 股票总数: {stock_count}, 最新数据: {latest_date}")
            
        except Exception as e:
            logger.error(f"系统健康检查失败: {e}")
        finally:
            db.close()
    
    async def _is_trading_day(self) -> bool:
        """检查是否为交易日"""
        try:
            # 简单的交易日判断：周一到周五，且不是节假日
            now = datetime.now()
            
            # 周末不是交易日
            if now.weekday() >= 5:  # 5=周六, 6=周日
                return False
            
            # 可以添加更复杂的节假日判断逻辑
            # 或者调用数据源的交易日历接口
            
            return True
            
        except Exception as e:
            logger.error(f"判断交易日失败: {e}")
            return False
    
    def get_job_status(self) -> dict:
        """获取任务状态"""
        if not self.is_running:
            return {"status": "stopped", "jobs": []}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running",
            "jobs": jobs,
            "scheduler_state": str(self.scheduler.state)
        }
    
    def add_one_time_job(self, func, run_date: datetime, job_id: str, name: str):
        """添加一次性任务"""
        try:
            self.scheduler.add_job(
                func=func,
                trigger='date',
                run_date=run_date,
                id=job_id,
                name=name,
                replace_existing=True
            )
            logger.info(f"添加一次性任务: {name}")
            
        except Exception as e:
            logger.error(f"添加一次性任务失败: {e}")
    
    def remove_job(self, job_id: str):
        """移除任务"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"移除任务: {job_id}")
            
        except Exception as e:
            logger.error(f"移除任务失败: {e}")

# 全局调度器实例
scheduler = TaskScheduler()