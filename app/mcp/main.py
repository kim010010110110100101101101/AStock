#!/usr/bin/env python3
"""MCP服务器启动脚本

用于启动A股数据爬虫项目的MCP服务器。

使用方法:
    python -m app.mcp.main

或者:
    python app/mcp/main.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.mcp.server import MCPServer
from app.core.logging import get_logger

logger = get_logger('mcp.main')


async def main():
    """主函数"""
    try:
        logger.info("Initializing MCP server...")
        server = MCPServer()
        
        logger.info("Starting MCP server...")
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"MCP server error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())