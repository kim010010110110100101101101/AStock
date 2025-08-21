import asyncio
import pandas as pd
from typing import List, Dict, Optional
from loguru import logger
from datetime import datetime

try:
    import akshare as ak
except ImportError:
    ak = None
    logger.warning("AKShare未安装，请运行: pip install akshare")

class AkshareDataSource:
    """AKShare数据源"""
    
    def __init__(self):
        if not ak:
            raise ImportError("AKShare未安装")
        
        logger.info("AKShare数据源初始化完成")
    
    def _convert_ts_code_to_symbol(self, ts_code: str) -> str:
        """将Tushare格式的代码转换为AKShare格式"""
        # 例: 000001.SZ -> 000001, 600000.SH -> 600000
        return ts_code.split('.')[0]
    
    def _convert_symbol_to_ts_code(self, symbol: str, market: str = None) -> str:
        """将股票代码转换为Tushare格式"""
        if symbol.startswith('6'):
            return f"{symbol}.SH"
        elif symbol.startswith(('0', '3')):
            return f"{symbol}.SZ"
        elif symbol.startswith('8') or symbol.startswith('4'):
            return f"{symbol}.BJ"
        else:
            return f"{symbol}.SH"  # 默认上海
    
    async def get_stock_basic(self, ts_code: Optional[str] = None) -> List[Dict]:
        """获取股票基本信息"""
        try:
            logger.info(f"从AKShare获取股票基本信息: {ts_code or '全部'}")
            
            loop = asyncio.get_event_loop()
            
            if ts_code:
                # 获取单个股票信息
                symbol = self._convert_ts_code_to_symbol(ts_code)
                
                # 从股票信息表中查找
                df_all = await loop.run_in_executor(None, ak.stock_info_a_code_name)
                df = df_all[df_all['code'] == symbol]
                
                if df.empty:
                    logger.warning(f"未找到股票 {ts_code} 的基本信息")
                    return []
            else:
                # 获取所有股票基本信息
                df = await loop.run_in_executor(None, ak.stock_info_a_code_name)
            
            if df.empty:
                logger.warning("未获取到股票基本信息")
                return []
            
            # 转换数据格式以匹配Tushare格式
            data = []
            for _, row in df.iterrows():
                symbol = row['code']
                ts_code = self._convert_symbol_to_ts_code(symbol)
                
                # 确定市场
                if symbol.startswith('6'):
                    market = 'SSE'
                    exchange = 'SSE'
                elif symbol.startswith(('0', '3')):
                    market = 'SZSE'
                    exchange = 'SZSE'
                else:
                    market = 'BSE'
                    exchange = 'BSE'
                
                item = {
                    'ts_code': ts_code,
                    'symbol': symbol,
                    'name': row['name'],
                    'area': None,  # AKShare不提供地域信息
                    'industry': None,  # 需要额外获取
                    'market': market,
                    'exchange': exchange,
                    'curr_type': 'CNY',
                    'list_status': 'L',  # 假设都是上市状态
                    'list_date': None,  # 需要额外获取
                    'delist_date': None,
                    'is_hs': None  # 需要额外判断
                }
                data.append(item)
            
            logger.info(f"获取到 {len(data)} 条股票基本信息")
            return data
            
        except Exception as e:
            logger.error(f"从AKShare获取股票基本信息失败: {e}")
            return []
    
    async def get_stock_daily(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """获取股票日线数据"""
        try:
            logger.info(f"从AKShare获取股票 {ts_code} 日线数据: {start_date} - {end_date}")
            
            symbol = self._convert_ts_code_to_symbol(ts_code)
            loop = asyncio.get_event_loop()
            
            # 转换日期格式 YYYYMMDD -> YYYY-MM-DD
            if start_date:
                start_date_formatted = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
            else:
                start_date_formatted = "19900101"
            
            if end_date:
                end_date_formatted = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"
            else:
                end_date_formatted = datetime.now().strftime("%Y-%m-%d")
            
            # 获取股票历史数据
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date_formatted,
                    end_date=end_date_formatted,
                    adjust="qfq"  # 前复权
                )
            )
            
            if df.empty:
                logger.info(f"股票 {ts_code} 没有日线数据")
                return []
            
            # 转换数据格式以匹配Tushare格式
            data = []
            for _, row in df.iterrows():
                # 转换日期格式
                trade_date = row['日期'].strftime('%Y%m%d')
                
                item = {
                    'ts_code': ts_code,
                    'trade_date': trade_date,
                    'open': float(row['开盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'close': float(row['收盘']),
                    'pre_close': None,  # AKShare不直接提供
                    'change': float(row['涨跌额']) if '涨跌额' in row else None,
                    'pct_chg': float(row['涨跌幅']) if '涨跌幅' in row else None,
                    'vol': float(row['成交量']) / 100 if '成交量' in row else None,  # 转换为手
                    'amount': float(row['成交额']) / 1000 if '成交额' in row else None,  # 转换为千元
                    'turnover_rate': float(row['换手率']) if '换手率' in row else None,
                    'turnover_rate_f': None,
                    'volume_ratio': None,
                    'pe': None,
                    'pe_ttm': None,
                    'pb': None,
                    'ps': None,
                    'ps_ttm': None,
                    'dv_ratio': None,
                    'dv_ttm': None,
                    'total_share': None,
                    'float_share': None,
                    'free_share': None,
                    'total_mv': None,
                    'circ_mv': None
                }
                data.append(item)
            
            logger.info(f"获取到股票 {ts_code} {len(data)} 条日线数据")
            return data
            
        except Exception as e:
            logger.error(f"从AKShare获取股票 {ts_code} 日线数据失败: {e}")
            return []
    
    async def get_realtime_data(self, ts_codes: List[str]) -> List[Dict]:
        """获取实时数据"""
        try:
            logger.info(f"从AKShare获取实时数据: {len(ts_codes)} 只股票")
            
            loop = asyncio.get_event_loop()
            
            # 获取实时行情
            df = await loop.run_in_executor(None, ak.stock_zh_a_spot_em)
            
            if df.empty:
                return []
            
            # 筛选指定股票
            symbols = [self._convert_ts_code_to_symbol(code) for code in ts_codes]
            df_filtered = df[df['代码'].isin(symbols)]
            
            # 转换数据格式
            data = []
            for _, row in df_filtered.iterrows():
                symbol = row['代码']
                ts_code = self._convert_symbol_to_ts_code(symbol)
                
                item = {
                    'ts_code': ts_code,
                    'name': row['名称'],
                    'price': float(row['最新价']),
                    'change': float(row['涨跌额']),
                    'pct_chg': float(row['涨跌幅']),
                    'vol': float(row['成交量']),
                    'amount': float(row['成交额']),
                    'open': float(row['今开']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'pre_close': float(row['昨收']),
                    'timestamp': datetime.now().isoformat()
                }
                data.append(item)
            
            logger.info(f"获取到 {len(data)} 条实时数据")
            return data
            
        except Exception as e:
            logger.error(f"从AKShare获取实时数据失败: {e}")
            return []
    
    async def get_stock_industry(self, symbol: str) -> Optional[str]:
        """获取股票行业信息"""
        try:
            loop = asyncio.get_event_loop()
            
            # 获取行业分类
            df = await loop.run_in_executor(None, ak.stock_board_industry_name_em)
            
            # 这里需要根据具体需求实现行业匹配逻辑
            # AKShare的行业分类接口比较复杂，需要进一步处理
            
            return None
            
        except Exception as e:
            logger.error(f"获取股票 {symbol} 行业信息失败: {e}")
            return None
    
    async def get_market_summary(self) -> Dict:
        """获取市场概况"""
        try:
            logger.info("从AKShare获取市场概况")
            
            loop = asyncio.get_event_loop()
            
            # 获取A股市场总貌
            df_summary = await loop.run_in_executor(None, ak.stock_zh_a_spot_em)
            
            if df_summary.empty:
                return {}
            
            # 统计市场数据
            total_stocks = len(df_summary)
            up_stocks = len(df_summary[df_summary['涨跌幅'] > 0])
            down_stocks = len(df_summary[df_summary['涨跌幅'] < 0])
            flat_stocks = len(df_summary[df_summary['涨跌幅'] == 0])
            
            summary = {
                'total_stocks': total_stocks,
                'up_stocks': up_stocks,
                'down_stocks': down_stocks,
                'flat_stocks': flat_stocks,
                'up_ratio': round(up_stocks / total_stocks * 100, 2) if total_stocks > 0 else 0,
                'down_ratio': round(down_stocks / total_stocks * 100, 2) if total_stocks > 0 else 0,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"市场概况: 总计{total_stocks}只，上涨{up_stocks}只，下跌{down_stocks}只")
            return summary
            
        except Exception as e:
            logger.error(f"从AKShare获取市场概况失败: {e}")
            return {}
    
    async def fetch_dragon_tiger_data(self, trade_date: str) -> List[Dict]:
        """获取龙虎榜数据"""
        try:
            logger.info(f"从AKShare获取龙虎榜数据: {trade_date}")
            
            loop = asyncio.get_event_loop()
            
            # 转换日期格式 YYYYMMDD -> YYYY-MM-DD
            formatted_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
            
            # 获取龙虎榜数据
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_lhb_detail_em(date=formatted_date)
            )
            
            if df.empty:
                logger.info(f"日期 {trade_date} 没有龙虎榜数据")
                return []
            
            # 转换数据格式
            data = []
            for _, row in df.iterrows():
                # 转换股票代码格式
                symbol = str(row['代码'])
                ts_code = self._convert_symbol_to_ts_code(symbol)
                
                item = {
                    'ts_code': ts_code,
                    'trade_date': trade_date,
                    'name': str(row['名称']),
                    'close': float(row['收盘价']) if pd.notna(row['收盘价']) else 0.0,
                    'pct_chg': float(row['涨跌幅']) if pd.notna(row['涨跌幅']) else 0.0,
                    'turnover': float(row['成交额']) if pd.notna(row['成交额']) else 0.0,
                    'net_amount': float(row['净买额']) if pd.notna(row['净买额']) else 0.0,
                    'reason': str(row['上榜原因']) if pd.notna(row['上榜原因']) else '',
                    'buy_amount': float(row['买入额']) if '买入额' in row and pd.notna(row['买入额']) else 0.0,
                    'sell_amount': float(row['卖出额']) if '卖出额' in row and pd.notna(row['卖出额']) else 0.0
                }
                data.append(item)
            
            logger.info(f"成功获取龙虎榜数据 {len(data)} 条")
            return data
            
        except Exception as e:
            logger.error(f"从AKShare获取龙虎榜数据失败: {e}")
            return []