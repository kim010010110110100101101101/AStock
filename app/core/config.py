"""应用程序配置模块

该模块定义了应用程序的所有配置项，包括数据库连接、API设置、
爬虫参数、数据源配置、定时任务和日志配置等。

配置项可以通过环境变量或.env文件进行设置。
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用程序配置类
    
    使用Pydantic BaseSettings自动从环境变量和.env文件加载配置。
    所有配置项都有合理的默认值，可根据部署环境进行调整。
    """
    
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:111111@localhost:3306/astock"
    """数据库连接URL，支持MySQL和SQLite
    
    格式示例:
    - MySQL: mysql+pymysql://user:password@host:port/database
    - SQLite: sqlite:///./database.db
    """
    
    # API配置
    API_V1_STR: str = "/api/v1"
    """API版本前缀路径"""
    
    PROJECT_NAME: str = "A股数据爬取系统"
    """项目名称，用于API文档标题"""
    
    ALLOWED_HOSTS: list = ["*"]
    """CORS允许的主机列表，生产环境应设置具体域名"""
    
    # 爬虫配置
    CRAWLER_DELAY: float = 1.0
    """爬取请求间隔时间（秒），避免过于频繁的请求"""
    
    MAX_RETRY_TIMES: int = 3
    """网络请求失败时的最大重试次数"""
    
    REQUEST_TIMEOUT: int = 30
    """HTTP请求超时时间（秒）"""
    
    # 数据源配置
    TUSHARE_TOKEN: Optional[str] = None
    """Tushare API访问令牌，需要在tushare.pro注册获取"""
    
    AKSHARE_ENABLED: bool = True
    """是否启用AKShare数据源"""
    
    # 定时任务配置
    SCHEDULER_ENABLED: bool = True
    """是否启用定时任务调度器"""
    
    DAILY_UPDATE_TIME: str = "09:30"
    """每日数据更新时间（HH:MM格式）"""
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    """日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL"""
    
    LOG_FILE: str = "logs/astock.log"
    """日志文件路径"""
    
    class Config:
        """Pydantic配置类"""
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()