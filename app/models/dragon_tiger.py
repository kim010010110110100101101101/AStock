from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Index
from sqlalchemy.sql import func
from app.core.database import Base

class DragonTiger(Base):
    """龙虎榜数据模型"""
    __tablename__ = "dragon_tiger"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 基本信息
    ts_code = Column(String(10), nullable=False, comment="股票代码")
    stock_name = Column(String(20), nullable=False, comment="股票名称")
    trade_date = Column(String(8), nullable=False, comment="交易日期 YYYYMMDD")
    
    # 价格信息
    close_price = Column(Float, comment="收盘价")
    pct_change = Column(Float, comment="涨跌幅(%)")
    turnover_rate = Column(Float, comment="换手率(%)")
    amount = Column(Float, comment="成交额(万元)")
    
    # 上榜信息
    reason = Column(String(100), comment="上榜原因")
    reason_code = Column(String(10), comment="上榜原因代码")
    
    # 买入信息
    buy_rank = Column(Integer, comment="买入排名")
    buy_dept = Column(String(100), comment="买入营业部")
    buy_amount = Column(Float, comment="买入金额(万元)")
    buy_rate = Column(Float, comment="买入占总成交比例(%)")
    
    # 卖出信息
    sell_rank = Column(Integer, comment="卖出排名")
    sell_dept = Column(String(100), comment="卖出营业部")
    sell_amount = Column(Float, comment="卖出金额(万元)")
    sell_rate = Column(Float, comment="卖出占总成交比例(%)")
    
    # 净买入信息
    net_amount = Column(Float, comment="净买入金额(万元)")
    
    # 机构标识
    is_institution = Column(Integer, default=0, comment="是否机构专用席位 0-否 1-是")
    
    # 数据来源和状态
    data_source = Column(String(20), default="ths", comment="数据来源")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 创建索引
    __table_args__ = (
        Index('idx_dragon_tiger_code_date', 'ts_code', 'trade_date'),
        Index('idx_dragon_tiger_date', 'trade_date'),
        Index('idx_dragon_tiger_reason', 'reason_code'),
        Index('idx_dragon_tiger_amount', 'net_amount'),
    )
    
    def __repr__(self):
        return f"<DragonTiger(ts_code='{self.ts_code}', trade_date='{self.trade_date}', reason='{self.reason}')>"

class DragonTigerSummary(Base):
    """龙虎榜汇总数据模型"""
    __tablename__ = "dragon_tiger_summary"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 基本信息
    ts_code = Column(String(10), nullable=False, comment="股票代码")
    stock_name = Column(String(20), nullable=False, comment="股票名称")
    trade_date = Column(String(8), nullable=False, comment="交易日期 YYYYMMDD")
    
    # 价格信息
    close_price = Column(Float, comment="收盘价")
    pct_change = Column(Float, comment="涨跌幅(%)")
    turnover_rate = Column(Float, comment="换手率(%)")
    amount = Column(Float, comment="成交额(万元)")
    
    # 上榜原因汇总
    reasons = Column(Text, comment="上榜原因列表(JSON格式)")
    reason_count = Column(Integer, default=1, comment="上榜原因数量")
    
    # 买卖汇总
    total_buy_amount = Column(Float, comment="总买入金额(万元)")
    total_sell_amount = Column(Float, comment="总卖出金额(万元)")
    net_amount = Column(Float, comment="净买入金额(万元)")
    
    # 机构参与情况
    institution_buy_amount = Column(Float, default=0, comment="机构买入金额(万元)")
    institution_sell_amount = Column(Float, default=0, comment="机构卖出金额(万元)")
    institution_net_amount = Column(Float, default=0, comment="机构净买入金额(万元)")
    
    # 营业部数量
    buy_dept_count = Column(Integer, comment="买入营业部数量")
    sell_dept_count = Column(Integer, comment="卖出营业部数量")
    
    # 数据来源和状态
    data_source = Column(String(20), default="ths", comment="数据来源")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 创建索引
    __table_args__ = (
        Index('idx_dt_summary_code_date', 'ts_code', 'trade_date'),
        Index('idx_dt_summary_date', 'trade_date'),
        Index('idx_dt_summary_net_amount', 'net_amount'),
        Index('idx_dt_summary_pct_change', 'pct_change'),
    )
    
    def __repr__(self):
        return f"<DragonTigerSummary(ts_code='{self.ts_code}', trade_date='{self.trade_date}', net_amount={self.net_amount})>"