from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger
import traceback

class AStockException(Exception):
    """A股系统基础异常类"""
    
    def __init__(self, message: str, code: str = "ASTOCK_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class DatabaseException(AStockException):
    """数据库异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)

class CrawlerException(AStockException):
    """爬虫异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CRAWLER_ERROR", details)

class DataSourceException(AStockException):
    """数据源异常"""
    
    def __init__(self, message: str, source: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["source"] = source
        super().__init__(message, "DATA_SOURCE_ERROR", details)

class ValidationException(AStockException):
    """数据验证异常"""
    
    def __init__(self, message: str, field: str = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(message, "VALIDATION_ERROR", details)

class RateLimitException(AStockException):
    """频率限制异常"""
    
    def __init__(self, message: str = "请求频率过高，请稍后重试", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "RATE_LIMIT_ERROR", details)

class ConfigurationException(AStockException):
    """配置异常"""
    
    def __init__(self, message: str, config_key: str = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, "CONFIGURATION_ERROR", details)

class SchedulerException(AStockException):
    """调度器异常"""
    
    def __init__(self, message: str, job_id: str = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if job_id:
            details["job_id"] = job_id
        super().__init__(message, "SCHEDULER_ERROR", details)

# 异常处理器
async def astock_exception_handler(request: Request, exc: AStockException):
    """A股系统异常处理器"""
    logger.error(f"AStock异常: {exc.code} - {exc.message}, 详情: {exc.details}")
    
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            },
            "success": False
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {}
            },
            "success": False
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    error_id = id(exc)  # 生成错误ID用于追踪
    
    logger.error(
        f"未处理异常 [ID: {error_id}]: {type(exc).__name__} - {str(exc)}\n"
        f"请求路径: {request.url}\n"
        f"请求方法: {request.method}\n"
        f"堆栈跟踪:\n{traceback.format_exc()}"
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "服务器内部错误，请联系管理员",
                "details": {
                    "error_id": error_id,
                    "type": type(exc).__name__
                }
            },
            "success": False
        }
    )

# 装饰器：用于捕获和转换异常
def handle_exceptions(func):
    """异常处理装饰器"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AStockException:
            # 重新抛出自定义异常
            raise
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            # 转换为自定义异常
            logger.error(f"函数 {func.__name__} 发生未处理异常: {e}")
            raise AStockException(
                message=f"执行 {func.__name__} 时发生错误",
                code="FUNCTION_ERROR",
                details={"function": func.__name__, "error": str(e)}
            )
    
    return wrapper

# 重试装饰器
import asyncio
from functools import wraps

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # 最后一次尝试失败
                        logger.error(
                            f"函数 {func.__name__} 重试 {max_attempts} 次后仍然失败: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                        f"{current_delay}秒后重试"
                    )
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            # 理论上不会到达这里
            raise last_exception
        
        return wrapper
    return decorator

# 上下文管理器：用于数据库事务
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

@asynccontextmanager
async def db_transaction(db: Session):
    """数据库事务上下文管理器"""
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"数据库事务回滚: {e}")
        raise DatabaseException(f"数据库操作失败: {str(e)}")
    finally:
        db.close()

# 验证函数
def validate_ts_code(ts_code: str) -> str:
    """验证股票代码格式"""
    if not ts_code:
        raise ValidationException("股票代码不能为空", "ts_code")
    
    # 基本格式验证
    if not ts_code.count('.') == 1:
        raise ValidationException("股票代码格式错误，应为 XXXXXX.XX 格式", "ts_code")
    
    code, market = ts_code.split('.')
    
    if len(code) != 6 or not code.isdigit():
        raise ValidationException("股票代码应为6位数字", "ts_code")
    
    if market not in ['SH', 'SZ', 'BJ']:
        raise ValidationException("市场代码应为 SH、SZ 或 BJ", "ts_code")
    
    return ts_code.upper()

def validate_date_format(date_str: str, field_name: str = "date") -> str:
    """验证日期格式 YYYYMMDD"""
    if not date_str:
        raise ValidationException(f"{field_name}不能为空", field_name)
    
    if len(date_str) != 8 or not date_str.isdigit():
        raise ValidationException(f"{field_name}格式错误，应为YYYYMMDD格式", field_name)
    
    try:
        from datetime import datetime
        datetime.strptime(date_str, '%Y%m%d')
    except ValueError:
        raise ValidationException(f"{field_name}不是有效日期", field_name)
    
    return date_str