from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class DragonTigerBase(BaseModel):
    """龙虎榜基础模型"""
    ts_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    trade_date: str = Field(..., description="交易日期 YYYYMMDD")
    close_price: Optional[float] = Field(None, description="收盘价")
    pct_change: Optional[float] = Field(None, description="涨跌幅(%)")
    turnover_rate: Optional[float] = Field(None, description="换手率(%)")
    amount: Optional[float] = Field(None, description="成交额(万元)")
    reason: Optional[str] = Field(None, description="上榜原因")
    reason_code: Optional[str] = Field(None, description="上榜原因代码")

class DragonTigerDetail(DragonTigerBase):
    """龙虎榜详细数据模型"""
    buy_rank: Optional[int] = Field(None, description="买入排名")
    buy_dept: Optional[str] = Field(None, description="买入营业部")
    buy_amount: Optional[float] = Field(None, description="买入金额(万元)")
    buy_rate: Optional[float] = Field(None, description="买入占总成交比例(%)")
    
    sell_rank: Optional[int] = Field(None, description="卖出排名")
    sell_dept: Optional[str] = Field(None, description="卖出营业部")
    sell_amount: Optional[float] = Field(None, description="卖出金额(万元)")
    sell_rate: Optional[float] = Field(None, description="卖出占总成交比例(%)")
    
    net_amount: Optional[float] = Field(None, description="净买入金额(万元)")
    is_institution: Optional[int] = Field(0, description="是否机构专用席位 0-否 1-是")
    data_source: Optional[str] = Field("ths", description="数据来源")

class DragonTigerResponse(DragonTigerDetail):
    """龙虎榜响应模型"""
    id: int = Field(..., description="记录ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True

class DragonTigerSummaryBase(BaseModel):
    """龙虎榜汇总基础模型"""
    ts_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    trade_date: str = Field(..., description="交易日期 YYYYMMDD")
    close_price: Optional[float] = Field(None, description="收盘价")
    pct_change: Optional[float] = Field(None, description="涨跌幅(%)")
    turnover_rate: Optional[float] = Field(None, description="换手率(%)")
    amount: Optional[float] = Field(None, description="成交额(万元)")

class DragonTigerSummaryDetail(DragonTigerSummaryBase):
    """龙虎榜汇总详细模型"""
    reasons: Optional[str] = Field(None, description="上榜原因列表(JSON格式)")
    reason_count: Optional[int] = Field(1, description="上榜原因数量")
    
    total_buy_amount: Optional[float] = Field(None, description="总买入金额(万元)")
    total_sell_amount: Optional[float] = Field(None, description="总卖出金额(万元)")
    net_amount: Optional[float] = Field(None, description="净买入金额(万元)")
    
    institution_buy_amount: Optional[float] = Field(0, description="机构买入金额(万元)")
    institution_sell_amount: Optional[float] = Field(0, description="机构卖出金额(万元)")
    institution_net_amount: Optional[float] = Field(0, description="机构净买入金额(万元)")
    
    buy_dept_count: Optional[int] = Field(None, description="买入营业部数量")
    sell_dept_count: Optional[int] = Field(None, description="卖出营业部数量")
    data_source: Optional[str] = Field("ths", description="数据来源")

class DragonTigerSummaryResponse(DragonTigerSummaryDetail):
    """龙虎榜汇总响应模型"""
    id: int = Field(..., description="记录ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True

class DragonTigerListResponse(BaseModel):
    """龙虎榜列表响应模型"""
    total: int = Field(..., description="总记录数")
    items: List[DragonTigerResponse] = Field(..., description="龙虎榜数据列表")
    page: int = Field(1, description="当前页码")
    size: int = Field(50, description="每页大小")
    has_next: bool = Field(False, description="是否有下一页")

class DragonTigerSummaryListResponse(BaseModel):
    """龙虎榜汇总列表响应模型"""
    total: int = Field(..., description="总记录数")
    items: List[DragonTigerSummaryResponse] = Field(..., description="龙虎榜汇总数据列表")
    page: int = Field(1, description="当前页码")
    size: int = Field(50, description="每页大小")
    has_next: bool = Field(False, description="是否有下一页")

class DragonTigerStatsResponse(BaseModel):
    """龙虎榜统计响应模型"""
    trade_date: str = Field(..., description="交易日期")
    total_stocks: int = Field(..., description="上榜股票总数")
    total_buy_amount: float = Field(..., description="总买入金额(万元)")
    total_sell_amount: float = Field(..., description="总卖出金额(万元)")
    total_net_amount: float = Field(..., description="总净买入金额(万元)")
    institution_net_amount: float = Field(..., description="机构净买入金额(万元)")
    
    # 按上榜原因分类统计
    reason_stats: List[dict] = Field([], description="按上榜原因统计")
    
    # 涨跌分布
    rise_count: int = Field(0, description="上涨股票数量")
    fall_count: int = Field(0, description="下跌股票数量")
    flat_count: int = Field(0, description="平盘股票数量")

class DragonTigerCreate(DragonTigerDetail):
    """创建龙虎榜数据模型"""
    pass

class DragonTigerUpdate(BaseModel):
    """更新龙虎榜数据模型"""
    stock_name: Optional[str] = None
    close_price: Optional[float] = None
    pct_change: Optional[float] = None
    turnover_rate: Optional[float] = None
    amount: Optional[float] = None
    reason: Optional[str] = None
    reason_code: Optional[str] = None
    buy_rank: Optional[int] = None
    buy_dept: Optional[str] = None
    buy_amount: Optional[float] = None
    buy_rate: Optional[float] = None
    sell_rank: Optional[int] = None
    sell_dept: Optional[str] = None
    sell_amount: Optional[float] = None
    sell_rate: Optional[float] = None
    net_amount: Optional[float] = None
    is_institution: Optional[int] = None