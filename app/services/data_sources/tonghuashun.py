import asyncio
import aiohttp
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re

from app.core.logging import get_logger
from app.core.exceptions import DataSourceException, handle_exceptions
from app.models.dragon_tiger import DragonTiger, DragonTigerSummary
from app.core.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import and_
# from app.services.data_sources.akshare_source import AkshareDataSource

logger = get_logger('crawler')

class TongHuaShunDragonTiger:
    """同花顺龙虎榜数据源"""
    
    def __init__(self):
        self.base_url = "http://data.10jqka.com.cn"
        self.dragon_tiger_url = f"{self.base_url}/market/longhu/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    @handle_exceptions
    async def fetch_dragon_tiger_data(self, trade_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取龙虎榜数据
        
        Args:
            trade_date: 交易日期，格式YYYY-MM-DD，默认为今天
            
        Returns:
            龙虎榜数据列表
        """
        if not self.session:
            raise DataSourceException("Session not initialized. Use async context manager.")
        
        if not trade_date:
            trade_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"开始获取同花顺龙虎榜数据，日期: {trade_date}")
        
        try:
            # 构建请求URL
            url = f"{self.dragon_tiger_url}?date={trade_date.replace('-', '')}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise DataSourceException(f"HTTP请求失败: {response.status}")
                
                html_content = await response.text()
                
            # 解析HTML内容
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找龙虎榜数据表格 - 同花顺网站结构：表头和数据分离
            # 首先查找包含数据的tbody
            data_table = None
            tables = soup.find_all('table', {'class': 'm-table'})
            
            for table in tables:
                tbody = table.find('tbody')
                if tbody and tbody.find_all('tr'):
                    # 检查是否包含股票代码（6位数字）
                    first_row = tbody.find('tr')
                    if first_row:
                        cells = first_row.find_all('td')
                        if len(cells) >= 6:
                            # 检查第二列是否包含6位数字（股票代码）
                            second_cell_text = cells[1].get_text(strip=True)
                            if re.match(r'^\d{6}$', second_cell_text):
                                data_table = table
                                break
            
            if not data_table:
                logger.warning(f"未找到龙虎榜数据表格，日期: {trade_date}")
                return []
            
            # 解析表格数据
            dragon_tiger_data = []
            
            # 从找到的数据表格中获取tbody中的所有行
            tbody = data_table.find('tbody')
            rows = tbody.find_all('tr') if tbody else []
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 7:  # 至少需要7列：空列、代码、名称、现价、涨跌幅、成交金额、净买入额
                    continue
                
                try:
                    # 根据实际HTML结构提取数据
                    # 列0: 空列或标签
                    # 列1: 股票代码
                    # 列2: 股票名称（包含链接）
                    # 列3: 现价
                    # 列4: 涨跌幅
                    # 列5: 成交金额
                    # 列6: 净买入额
                    
                    stock_code = cells[1].get_text(strip=True)
                    if not re.match(r'^\d{6}$', stock_code):
                        continue
                    
                    # 从链接中提取股票名称
                    name_cell = cells[2]
                    stock_link = name_cell.find('a')
                    stock_name = stock_link.get_text(strip=True) if stock_link else name_cell.get_text(strip=True)
                    
                    # 提取其他数据
                    close_price = self._parse_float(cells[3].get_text(strip=True))
                    change_rate_text = cells[4].get_text(strip=True).replace('%', '')
                    change_rate = self._parse_float(change_rate_text)
                    turnover_text = cells[5].get_text(strip=True).replace('亿', '').replace('万', '')
                    turnover = self._parse_float(turnover_text)
                    net_buy_text = cells[6].get_text(strip=True).replace('亿', '').replace('万', '')
                    net_buy = self._parse_float(net_buy_text)
                    
                    # 从第一列提取上榜原因（如果有标签）
                    reason_cell = cells[0]
                    reason_label = reason_cell.find('label')
                    reason = reason_label.get_text(strip=True) if reason_label else '连续三个交易日内涨跌幅偏离值累计达20%'
                    
                    data_item = {
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'trade_date': trade_date,
                        'reason': reason,
                        'close_price': close_price,
                        'change_rate': change_rate,
                        'turnover': turnover,
                        'net_buy_amount': net_buy,
                        'data_source': 'tonghuashun'
                    }
                    
                    dragon_tiger_data.append(data_item)
                    
                except Exception as e:
                    logger.warning(f"解析行数据失败: {e}, 行内容: {[cell.get_text(strip=True) for cell in cells]}")
                    continue
            
            logger.info(f"成功获取龙虎榜数据 {len(dragon_tiger_data)} 条")
            return dragon_tiger_data
            
        except Exception as e:
            logger.error(f"同花顺获取龙虎榜数据失败: {e}")
            # TODO: 尝试使用AKShare作为备用数据源（暂时禁用，因为依赖问题）
            # try:
            #     logger.info("尝试使用AKShare作为备用数据源获取龙虎榜数据")
            #     akshare_source = AkshareDataSource()
            #     # 转换日期格式 YYYY-MM-DD -> YYYYMMDD
            #     akshare_date = trade_date.replace('-', '')
            #     akshare_data = await akshare_source.fetch_dragon_tiger_data(akshare_date)
            #     
            #     # 转换AKShare数据格式为同花顺格式
            #     converted_data = []
            #     for item in akshare_data:
            #         converted_item = {
            #             'stock_code': item['ts_code'].split('.')[0],  # 去掉后缀
            #             'stock_name': item['name'],
            #             'trade_date': trade_date,
            #             'reason': item.get('reason', ''),
            #             'close_price': item.get('close', 0.0),
            #             'change_rate': item.get('pct_chg', 0.0),
            #             'turnover': item.get('turnover', 0.0),
            #             'net_buy_amount': item.get('net_amount', 0.0),
            #             'data_source': 'akshare'
            #         }
            #         converted_data.append(converted_item)
            #     
            #     logger.info(f"AKShare备用数据源成功获取龙虎榜数据 {len(converted_data)} 条")
            #     return converted_data
            #     
            # except Exception as akshare_error:
            #     logger.error(f"AKShare备用数据源也失败: {akshare_error}")
            #     raise DataSourceException(f"所有数据源都失败 - 同花顺: {e}, AKShare: {akshare_error}")
            raise DataSourceException(f"获取龙虎榜数据失败: {e}")
    
    @handle_exceptions
    async def fetch_dragon_tiger_detail(self, stock_code: str, trade_date: str) -> List[Dict[str, Any]]:
        """获取个股龙虎榜详细数据
        
        Args:
            stock_code: 股票代码
            trade_date: 交易日期
            
        Returns:
            详细龙虎榜数据
        """
        if not self.session:
            raise DataSourceException("Session not initialized. Use async context manager.")
        
        logger.info(f"获取个股龙虎榜详细数据: {stock_code}, 日期: {trade_date}")
        
        try:
            # 构建详情页URL
            url = f"{self.base_url}/market/longhu/stock/{stock_code}/{trade_date.replace('-', '')}/"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise DataSourceException(f"HTTP请求失败: {response.status}")
                
                html_content = await response.text()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找买入和卖出数据表格
            detail_data = []
            
            # 买入数据
            buy_table = soup.find('table', {'id': 'buy_table'})
            if buy_table:
                detail_data.extend(self._parse_detail_table(buy_table, 'buy', stock_code, trade_date))
            
            # 卖出数据
            sell_table = soup.find('table', {'id': 'sell_table'})
            if sell_table:
                detail_data.extend(self._parse_detail_table(sell_table, 'sell', stock_code, trade_date))
            
            logger.info(f"获取详细数据 {len(detail_data)} 条")
            return detail_data
            
        except Exception as e:
            logger.error(f"获取详细龙虎榜数据失败: {e}")
            raise DataSourceException(f"获取详细龙虎榜数据失败: {e}")
    
    def _parse_detail_table(self, table, trade_type: str, stock_code: str, trade_date: str) -> List[Dict[str, Any]]:
        """解析详细数据表格"""
        detail_data = []
        rows = table.find('tbody').find_all('tr') if table.find('tbody') else []
        
        for i, row in enumerate(rows, 1):
            cells = row.find_all('td')
            if len(cells) < 3:
                continue
            
            try:
                department = cells[0].get_text(strip=True)
                amount = self._parse_float(cells[1].get_text(strip=True))
                ratio = self._parse_float(cells[2].get_text(strip=True).replace('%', ''))
                
                detail_item = {
                    'stock_code': stock_code,
                    'trade_date': trade_date,
                    'rank': i,
                    'department': department,
                    'trade_type': trade_type,
                    'amount': amount,
                    'ratio': ratio,
                    'data_source': 'tonghuashun'
                }
                
                detail_data.append(detail_item)
                
            except Exception as e:
                logger.warning(f"解析详细数据行失败: {e}")
                continue
        
        return detail_data
    
    def _parse_float(self, value: str) -> Optional[float]:
        """解析浮点数"""
        if not value or value == '--' or value == '-':
            return None
        
        try:
            # 处理万、亿等单位
            value = value.replace(',', '').replace(' ', '')
            
            if '万' in value:
                return float(value.replace('万', '')) * 10000
            elif '亿' in value:
                return float(value.replace('亿', '')) * 100000000
            else:
                return float(value)
        except (ValueError, TypeError):
            return None
    
    @handle_exceptions
    async def save_dragon_tiger_data(self, data_list: List[Dict[str, Any]], db: Session) -> int:
        """保存龙虎榜数据到数据库
        
        Args:
            data_list: 龙虎榜数据列表
            db: 数据库会话
            
        Returns:
            保存的记录数
        """
        if not data_list:
            return 0
        
        saved_count = 0
        
        for data in data_list:
            try:
                # 检查是否已存在
                existing = db.query(DragonTigerSummary).filter(
                    and_(
                        DragonTigerSummary.stock_code == data['stock_code'],
                        DragonTigerSummary.trade_date == datetime.strptime(data['trade_date'], '%Y-%m-%d').date()
                    )
                ).first()
                
                if existing:
                    # 更新现有记录
                    for key, value in data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.updated_at = datetime.now()
                else:
                    # 创建新记录
                    dragon_tiger = DragonTigerSummary(
                        stock_code=data['stock_code'],
                        stock_name=data['stock_name'],
                        trade_date=datetime.strptime(data['trade_date'], '%Y-%m-%d').date(),
                        reason=data['reason'],
                        close_price=data['close_price'],
                        change_rate=data['change_rate'],
                        turnover=data['turnover'],
                        net_buy_amount=data['net_buy_amount'],
                        data_source=data['data_source']
                    )
                    db.add(dragon_tiger)
                
                saved_count += 1
                
            except Exception as e:
                logger.error(f"保存龙虎榜数据失败: {e}, 数据: {data}")
                continue
        
        try:
            db.commit()
            logger.info(f"成功保存龙虎榜数据 {saved_count} 条")
        except Exception as e:
            db.rollback()
            logger.error(f"提交数据库事务失败: {e}")
            raise DataSourceException(f"保存数据失败: {e}")
        
        return saved_count
    
    @handle_exceptions
    async def save_dragon_tiger_detail(self, detail_list: List[Dict[str, Any]], db: Session) -> int:
        """保存龙虎榜详细数据到数据库"""
        if not detail_list:
            return 0
        
        saved_count = 0
        
        for detail in detail_list:
            try:
                # 检查是否已存在
                existing = db.query(DragonTiger).filter(
                    and_(
                        DragonTiger.stock_code == detail['stock_code'],
                        DragonTiger.trade_date == datetime.strptime(detail['trade_date'], '%Y-%m-%d').date(),
                        DragonTiger.rank == detail['rank'],
                        DragonTiger.trade_type == detail['trade_type']
                    )
                ).first()
                
                if existing:
                    # 更新现有记录
                    for key, value in detail.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.updated_at = datetime.now()
                else:
                    # 创建新记录
                    dragon_tiger_detail = DragonTiger(
                        stock_code=detail['stock_code'],
                        trade_date=datetime.strptime(detail['trade_date'], '%Y-%m-%d').date(),
                        rank=detail['rank'],
                        department=detail['department'],
                        trade_type=detail['trade_type'],
                        amount=detail['amount'],
                        ratio=detail['ratio'],
                        data_source=detail['data_source']
                    )
                    db.add(dragon_tiger_detail)
                
                saved_count += 1
                
            except Exception as e:
                logger.error(f"保存龙虎榜详细数据失败: {e}, 数据: {detail}")
                continue
        
        try:
            db.commit()
            logger.info(f"成功保存龙虎榜详细数据 {saved_count} 条")
        except Exception as e:
            db.rollback()
            logger.error(f"提交详细数据事务失败: {e}")
            raise DataSourceException(f"保存详细数据失败: {e}")
        
        return saved_count


async def crawl_today_dragon_tiger() -> Dict[str, Any]:
    """爬取今日龙虎榜数据的主函数"""
    result = {
        'success': False,
        'message': '',
        'summary_count': 0,
        'detail_count': 0,
        'trade_date': datetime.now().strftime('%Y-%m-%d')
    }
    
    try:
        async with TongHuaShunDragonTiger() as crawler:
            # 获取数据库会话
            db = next(get_db())
            
            try:
                # 获取龙虎榜汇总数据
                summary_data = await crawler.fetch_dragon_tiger_data()
                
                if summary_data:
                    # 保存汇总数据
                    summary_count = await crawler.save_dragon_tiger_data(summary_data, db)
                    result['summary_count'] = summary_count
                    
                    # 获取详细数据
                    detail_count = 0
                    for item in summary_data[:5]:  # 限制获取前5只股票的详细数据
                        try:
                            detail_data = await crawler.fetch_dragon_tiger_detail(
                                item['stock_code'], 
                                item['trade_date']
                            )
                            if detail_data:
                                saved = await crawler.save_dragon_tiger_detail(detail_data, db)
                                detail_count += saved
                            
                            # 添加延时避免请求过快
                            await asyncio.sleep(1)
                            
                        except Exception as e:
                            logger.warning(f"获取 {item['stock_code']} 详细数据失败: {e}")
                            continue
                    
                    result['detail_count'] = detail_count
                    result['success'] = True
                    result['message'] = f"成功爬取龙虎榜数据，汇总 {summary_count} 条，详细 {detail_count} 条"
                    
                else:
                    result['message'] = "未获取到龙虎榜数据"
                    
            finally:
                db.close()
                
    except Exception as e:
        logger.error(f"爬取龙虎榜数据失败: {e}")
        result['message'] = f"爬取失败: {str(e)}"
    
    return result


if __name__ == "__main__":
    # 测试代码
    async def test():
        result = await crawl_today_dragon_tiger()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    asyncio.run(test())