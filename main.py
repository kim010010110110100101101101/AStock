#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股数据爬取系统启动脚本

使用方法:
    python main.py
    或
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )