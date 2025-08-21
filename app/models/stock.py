from sqlalchemy import Column, String, DateTime, Float, Integer, Text, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class Stock(Base):
    """股票信息汇总表"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), unique=True, nullable=False, comment="股票代码")
    symbol = Column(String(10), nullable=False, comment="股票代码(不含后缀)")
    name = Column(String(50), nullable=False, comment="股票名称")
    
    # 基本信息
    industry = Column(String(50), comment="所属行业")
    area = Column(String(20), comment="地域")
    market = Column(String(10), comment="市场类型")
    exchange = Column(String(10), comment="交易所")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否活跃")
    list_date = Column(String(10), comment="上市日期")
    delist_date = Column(String(10), comment="退市日期")
    
    # 最新数据
    latest_price = Column(Float, comment="最新价格")
    latest_date = Column(String(10), comment="最新数据日期")
    
    # 数据更新状态
    last_crawl_date = Column(String(10), comment="最后爬取日期")
    crawl_status = Column(String(20), default="pending", comment="爬取状态")
    error_message = Column(Text, comment="错误信息")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Stock(ts_code='{self.ts_code}', name='{self.name}', latest_price={self.latest_price})>"