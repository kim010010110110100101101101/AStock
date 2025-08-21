from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import setup_logging
from app.core.exceptions import (
    AStockException,
    astock_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.api import api_router
from app.api.v1 import api_router as v1_router
from app.services.scheduler import TaskScheduler
from contextlib import asynccontextmanager
from loguru import logger
import asyncio

# 全局调度器实例
scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global scheduler
    
    # 启动时执行
    logger.info("正在启动A股数据系统...")
    
    # 初始化日志系统
    setup_logging()
    logger.info("日志系统初始化完成")
    
    # 创建数据库表
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建/检查完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    
    # 启动调度器
    if settings.SCHEDULER_ENABLED:
        try:
            scheduler = TaskScheduler()
            await scheduler.start()
            logger.info("定时任务调度器启动完成")
        except Exception as e:
            logger.error(f"调度器启动失败: {e}")
    
    logger.info("A股数据系统启动完成")
    
    yield
    
    # 关闭时执行
    logger.info("正在关闭A股数据系统...")
    
    if scheduler:
        try:
            await scheduler.stop()
            logger.info("定时任务调度器已停止")
        except Exception as e:
            logger.error(f"调度器停止失败: {e}")
    
    logger.info("A股数据系统已关闭")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A股数据爬取和分析系统",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# 添加异常处理器
app.add_exception_handler(AStockException, astock_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = asyncio.get_event_loop().time()
    
    # 记录请求开始
    logger.info(
        f"请求开始: {request.method} {request.url} - "
        f"客户端: {request.client.host if request.client else 'unknown'}"
    )
    
    try:
        response = await call_next(request)
        
        # 计算处理时间
        process_time = asyncio.get_event_loop().time() - start_time
        
        # 记录请求完成
        logger.info(
            f"请求完成: {request.method} {request.url} - "
            f"状态码: {response.status_code} - "
            f"处理时间: {process_time:.3f}s"
        )
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = asyncio.get_event_loop().time() - start_time
        logger.error(
            f"请求异常: {request.method} {request.url} - "
            f"错误: {str(e)} - "
            f"处理时间: {process_time:.3f}s"
        )
        raise

# 注册路由
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(v1_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "A股数据爬取系统", 
        "version": "1.0.0",
        "status": "running",
        "scheduler_enabled": settings.SCHEDULER_ENABLED
    }

@app.get("/system/info")
async def system_info():
    """系统信息"""
    global scheduler
    
    scheduler_status = "disabled"
    if settings.ENABLE_SCHEDULER and scheduler:
        scheduler_status = "running" if scheduler.scheduler.running else "stopped"
    
    return {
        "system": {
            "name": settings.PROJECT_NAME,
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG
        },
        "database": {
            "url": settings.DATABASE_URL.replace(settings.DATABASE_PASSWORD, "***") if settings.DATABASE_PASSWORD else settings.DATABASE_URL
        },
        "scheduler": {
            "enabled": settings.ENABLE_SCHEDULER,
            "status": scheduler_status
        },
        "data_sources": {
            "tushare_enabled": bool(settings.TUSHARE_TOKEN),
            "akshare_enabled": True
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)