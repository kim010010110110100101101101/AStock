"""数据库连接和会话管理模块

该模块负责配置SQLAlchemy数据库引擎、会话工厂和基础模型类。
提供数据库连接的依赖注入函数，用于FastAPI路由中获取数据库会话。

支持的数据库:
- MySQL (推荐)
- SQLite (开发环境)
- PostgreSQL
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings


# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    # SQLite需要特殊配置以支持多线程
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    # 连接池配置（MySQL/PostgreSQL）
    pool_pre_ping=True,  # 验证连接有效性
    pool_recycle=3600,   # 连接回收时间（秒）
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,  # 不自动提交事务
    autoflush=False,   # 不自动刷新到数据库
    bind=engine        # 绑定到数据库引擎
)

# 创建基础模型类
# 所有数据库模型都应继承此类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话的依赖注入函数
    
    这是一个生成器函数，用于FastAPI的依赖注入系统。
    确保每个请求都有独立的数据库会话，并在请求结束后正确关闭。
    
    Yields:
        Session: SQLAlchemy数据库会话对象
        
    Example:
        ```python
        @app.get("/users/")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()