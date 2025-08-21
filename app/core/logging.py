import os
import sys
from pathlib import Path
from loguru import logger
from app.core.config import settings

def setup_logging():
    """配置日志系统"""
    
    # 移除默认的日志处理器
    logger.remove()
    
    # 创建日志目录
    log_file_path = Path(settings.LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 控制台日志格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 文件日志格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 添加文件处理器 - 普通日志
    logger.add(
        settings.LOG_FILE,
        format=file_format,
        level=settings.LOG_LEVEL,
        rotation="10 MB",  # 文件大小轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        backtrace=True,
        diagnose=True,
        encoding="utf-8"
    )
    
    # 添加错误日志文件处理器
    error_log_file = log_file_path.parent / "error.log"
    logger.add(
        str(error_log_file),
        format=file_format,
        level="ERROR",
        rotation="5 MB",
        retention="60 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        encoding="utf-8"
    )
    
    # 添加爬虫专用日志文件
    crawler_log_file = log_file_path.parent / "crawler.log"
    logger.add(
        str(crawler_log_file),
        format=file_format,
        level="INFO",
        rotation="20 MB",
        retention="15 days",
        compression="zip",
        filter=lambda record: "crawler" in record["name"].lower() or "crawl" in record["message"].lower(),
        encoding="utf-8"
    )
    
    # 添加API访问日志文件
    api_log_file = log_file_path.parent / "api.log"
    logger.add(
        str(api_log_file),
        format=file_format,
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        filter=lambda record: "api" in record["name"].lower() or "endpoint" in record["message"].lower(),
        encoding="utf-8"
    )
    
    logger.info(f"日志系统初始化完成 - 级别: {settings.LOG_LEVEL}, 文件: {settings.LOG_FILE}")

def get_logger(name: str):
    """获取指定名称的日志器"""
    return logger.bind(name=name)

# 创建不同用途的日志器
crawler_logger = get_logger("crawler")
api_logger = get_logger("api")
db_logger = get_logger("database")
scheduler_logger = get_logger("scheduler")