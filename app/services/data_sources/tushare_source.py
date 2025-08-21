import asyncio
import pandas as pd
from typing import List, Dict, Optional
from loguru import logger
from app.core.config import settings

try:
    import tushare as ts
except ImportError:
    ts = None
    logger.warning("Tushare未安装，请运行: pip install tushare")

class TushareDataSource:
    """Tushare数据源"""
    
    def __init__(self):
        if not ts:
            raise ImportError("Tushare未安装")
        
        if not settings.TUSHARE_TOKEN:
            raise ValueError("请设置TUSHARE_TOKEN")
        
        # 设置token
        ts.set_token(settings.TUSHARE_TOKEN)
        self.pro = ts.pro_api()
        
        logger.info("Tushare数据源初始化完成")
    
    async def get_stock_basic(self, ts_code: Optional[str] = None) -> List[Dict]:
        """获取股票基本信息"""
        try:
            logger.info(f"从Tushare获取股票基本信息: {ts_code or '全部'}")
            
            # 在异步环境中运行同步代码
            loop = asyncio.get_event_loop()
            
            if ts_code:
                df = await loop.run_in_executor(
                    None, 
                    lambda: self.pro.stock_basic(
                        ts_code=ts_code,
                        fields='ts_code,symbol,name,area,industry,market,exchange,curr_type,list_status,list_date,delist_date,is_hs'
                    )
                )
            else:
                df = await loop.run_in_executor(
                    None, 
                    lambda: self.pro.stock_basic(
                        exchange='',
                        list_status='L',
                        fields='ts_code,symbol,name,area,industry,market,exchange,curr_type,list_status,list_date,delist_date,is_hs'
                    )
                )
            
            if df.empty:
                logger.warning("未获取到股票基本信息")
                return []
            
            # 转换为字典列表
            data = df.to_dict('records')
            logger.info(f"获取到 {len(data)} 条股票基本信息")
            
            return data
            
        except Exception as e:
            logger.error(f"从Tushare获取股票基本信息失败: {e}")
            return []
    
    async def get_stock_daily(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """获取股票日线数据"""
        try:
            logger.info(f"从Tushare获取股票 {ts_code} 日线数据: {start_date} - {end_date}")
            
            loop = asyncio.get_event_loop()
            
            # 获取基础日线数据
            df_daily = await loop.run_in_executor(
                None,
                lambda: self.pro.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )
            )
            
            if df_daily.empty:
                logger.info(f"股票 {ts_code} 没有日线数据")
                return []
            
            # 获取每日指标数据
            df_daily_basic = await loop.run_in_executor(
                None,
                lambda: self.pro.daily_basic(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    fields='ts_code,trade_date,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
                )
            )
            
            # 合并数据
            if not df_daily_basic.empty:
                df = pd.merge(df_daily, df_daily_basic, on=['ts_code', 'trade_date'], how='left')
            else:
                df = df_daily
            
            # 转换为字典列表
            data = df.to_dict('records')
            logger.info(f"获取到股票 {ts_code} {len(data)} 条日线数据")
            
            return data
            
        except Exception as e:
            logger.error(f"从Tushare获取股票 {ts_code} 日线数据失败: {e}")
            return []
    
    async def get_trade_cal(self, start_date: str, end_date: str) -> List[str]:
        """获取交易日历"""
        try:
            logger.info(f"从Tushare获取交易日历: {start_date} - {end_date}")
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: self.pro.trade_cal(
                    exchange='SSE',
                    start_date=start_date,
                    end_date=end_date,
                    is_open='1'
                )
            )
            
            if df.empty:
                return []
            
            trade_dates = df['cal_date'].tolist()
            logger.info(f"获取到 {len(trade_dates)} 个交易日")
            
            return trade_dates
            
        except Exception as e:
            logger.error(f"从Tushare获取交易日历失败: {e}")
            return []
    
    async def get_stock_list(self, market: Optional[str] = None) -> List[Dict]:
        """获取股票列表"""
        try:
            logger.info(f"从Tushare获取股票列表: {market or '全部市场'}")
            
            loop = asyncio.get_event_loop()
            
            if market:
                df = await loop.run_in_executor(
                    None,
                    lambda: self.pro.stock_basic(
                        exchange=market,
                        list_status='L',
                        fields='ts_code,symbol,name,area,industry,market'
                    )
                )
            else:
                df = await loop.run_in_executor(
                    None,
                    lambda: self.pro.stock_basic(
                        exchange='',
                        list_status='L',
                        fields='ts_code,symbol,name,area,industry,market'
                    )
                )
            
            if df.empty:
                return []
            
            data = df.to_dict('records')
            logger.info(f"获取到 {len(data)} 只股票")
            
            return data
            
        except Exception as e:
            logger.error(f"从Tushare获取股票列表失败: {e}")
            return []
    
    async def get_realtime_data(self, ts_codes: List[str]) -> List[Dict]:
        """获取实时数据(需要高级权限)"""
        try:
            logger.info(f"从Tushare获取实时数据: {len(ts_codes)} 只股票")
            
            # 注意：实时数据需要Tushare高级权限
            # 这里提供接口，实际使用需要相应权限
            
            loop = asyncio.get_event_loop()
            
            # 分批获取，避免单次请求过多
            batch_size = 100
            all_data = []
            
            for i in range(0, len(ts_codes), batch_size):
                batch_codes = ts_codes[i:i + batch_size]
                ts_code_str = ','.join(batch_codes)
                
                try:
                    df = await loop.run_in_executor(
                        None,
                        lambda: self.pro.realtime_quote(
                            ts_code=ts_code_str
                        )
                    )
                    
                    if not df.empty:
                        batch_data = df.to_dict('records')
                        all_data.extend(batch_data)
                    
                    # 添加延迟避免频率限制
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    logger.error(f"获取批次 {i//batch_size + 1} 实时数据失败: {e}")
                    continue
            
            logger.info(f"获取到 {len(all_data)} 条实时数据")
            return all_data
            
        except Exception as e:
            logger.error(f"从Tushare获取实时数据失败: {e}")
            return []