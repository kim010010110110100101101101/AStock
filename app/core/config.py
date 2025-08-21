from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:111111@localhost:3306/astock"
    
    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "A股数据爬取系统"
    ALLOWED_HOSTS: list = ["*"]  # CORS允许的主机
    
    # 爬虫配置
    CRAWLER_DELAY: float = 1.0  # 爬取间隔(秒)
    MAX_RETRY_TIMES: int = 3    # 最大重试次数
    REQUEST_TIMEOUT: int = 30   # 请求超时时间(秒)
    
    # 数据源配置
    TUSHARE_TOKEN: Optional[str] = None  # Tushare API Token
    AKSHARE_ENABLED: bool = True         # 是否启用AKShare
    
    # 定时任务配置
    SCHEDULER_ENABLED: bool = True
    DAILY_UPDATE_TIME: str = "09:30"     # 每日更新时间
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/astock.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()