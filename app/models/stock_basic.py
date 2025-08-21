from sqlalchemy import Column, String, DateTime, Float, Integer, Text
from sqlalchemy.sql import func
from app.core.database import Base

class StockBasic(Base):
    """股票基本信息表"""
    __tablename__ = "stock_basic"
    
    ts_code = Column(String(20), primary_key=True, comment="股票代码")
    symbol = Column(String(10), nullable=False, comment="股票代码(不含后缀)")
    name = Column(String(20), nullable=False, comment="股票名称")
    area = Column(String(20), comment="地域")
    industry = Column(String(50), comment="所属行业")
    market = Column(String(10), comment="市场类型")
    exchange = Column(String(10), comment="交易所代码")
    curr_type = Column(String(10), comment="交易货币")
    list_status = Column(String(1), comment="上市状态")
    list_date = Column(String(10), comment="上市日期")
    delist_date = Column(String(10), comment="退市日期")
    is_hs = Column(String(1), comment="是否沪深港通标的")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<StockBasic(ts_code='{self.ts_code}', name='{self.name}')>"