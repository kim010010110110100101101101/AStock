from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StockBase(BaseModel):
    ts_code: str
    symbol: str
    name: str
    industry: Optional[str] = None
    area: Optional[str] = None
    market: Optional[str] = None
    exchange: Optional[str] = None

class StockResponse(StockBase):
    id: int
    is_active: bool
    list_date: Optional[str] = None
    delist_date: Optional[str] = None
    latest_price: Optional[float] = None
    latest_date: Optional[str] = None
    last_crawl_date: Optional[str] = None
    crawl_status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StockBasicResponse(BaseModel):
    ts_code: str
    symbol: str
    name: str
    area: Optional[str] = None
    industry: Optional[str] = None
    market: Optional[str] = None
    exchange: Optional[str] = None
    curr_type: Optional[str] = None
    list_status: Optional[str] = None
    list_date: Optional[str] = None
    delist_date: Optional[str] = None
    is_hs: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StockDailyResponse(BaseModel):
    id: int
    ts_code: str
    trade_date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    pre_close: Optional[float] = None
    change: Optional[float] = None
    pct_chg: Optional[float] = None
    vol: Optional[float] = None
    amount: Optional[float] = None
    turnover_rate: Optional[float] = None
    turnover_rate_f: Optional[float] = None
    volume_ratio: Optional[float] = None
    pe: Optional[float] = None
    pe_ttm: Optional[float] = None
    pb: Optional[float] = None
    ps: Optional[float] = None
    ps_ttm: Optional[float] = None
    dv_ratio: Optional[float] = None
    dv_ttm: Optional[float] = None
    total_share: Optional[float] = None
    float_share: Optional[float] = None
    free_share: Optional[float] = None
    total_mv: Optional[float] = None
    circ_mv: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StockCreate(StockBase):
    is_active: bool = True
    list_date: Optional[str] = None

class StockUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    area: Optional[str] = None
    is_active: Optional[bool] = None
    latest_price: Optional[float] = None
    latest_date: Optional[str] = None
    crawl_status: Optional[str] = None
    error_message: Optional[str] = None