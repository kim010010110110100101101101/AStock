from sqlalchemy import Column, String, DateTime, Float, Integer, BigInteger, Index
from sqlalchemy.sql import func
from app.core.database import Base

class StockDaily(Base):
    """股票日线数据表"""
    __tablename__ = "stock_daily"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    trade_date = Column(String(10), nullable=False, comment="交易日期")
    
    # 价格数据
    open = Column(Float, comment="开盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    close = Column(Float, comment="收盘价")
    pre_close = Column(Float, comment="昨收价")
    change = Column(Float, comment="涨跌额")
    pct_chg = Column(Float, comment="涨跌幅")
    
    # 成交数据
    vol = Column(Float, comment="成交量(手)")
    amount = Column(Float, comment="成交额(千元)")
    
    # 技术指标
    turnover_rate = Column(Float, comment="换手率")
    turnover_rate_f = Column(Float, comment="换手率(自由流通股)")
    volume_ratio = Column(Float, comment="量比")
    pe = Column(Float, comment="市盈率")
    pe_ttm = Column(Float, comment="市盈率TTM")
    pb = Column(Float, comment="市净率")
    ps = Column(Float, comment="市销率")
    ps_ttm = Column(Float, comment="市销率TTM")
    dv_ratio = Column(Float, comment="股息率")
    dv_ttm = Column(Float, comment="股息率TTM")
    total_share = Column(Float, comment="总股本(万股)")
    float_share = Column(Float, comment="流通股本(万股)")
    free_share = Column(Float, comment="自由流通股本(万股)")
    total_mv = Column(Float, comment="总市值(万元)")
    circ_mv = Column(Float, comment="流通市值(万元)")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_ts_code_trade_date', 'ts_code', 'trade_date', unique=True),
        Index('idx_trade_date', 'trade_date'),
        Index('idx_ts_code', 'ts_code'),
    )
    
    def __repr__(self):
        return f"<StockDaily(ts_code='{self.ts_code}', trade_date='{self.trade_date}', close={self.close})>"