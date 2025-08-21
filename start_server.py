#!/usr/bin/env python3
"""A股数据系统启动脚本

支持启动HTTP API服务器或MCP服务器。

使用方法:
    # 启动HTTP API服务器（默认）
    python start_server.py
    python start_server.py --mode http
    
    # 启动MCP服务器
    python start_server.py --mode mcp
    
    # 同时启动HTTP和MCP服务器
    python start_server.py --mode both
"""

import argparse
import asyncio
import sys
from pathlib import Path
import uvicorn
from multiprocessing import Process

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger('startup')


def start_http_server():
    """启动HTTP API服务器"""
    logger.info("Starting HTTP API server...")
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )


async def start_mcp_server():
    """启动MCP服务器"""
    logger.info("Starting MCP server...")
    from app.mcp.server import MCPServer
    
    server = MCPServer()
    await server.run()


def run_mcp_server():
    """在单独进程中运行MCP服务器"""
    asyncio.run(start_mcp_server())


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="A股数据系统启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 启动HTTP API服务器
  %(prog)s --mode http        # 启动HTTP API服务器
  %(prog)s --mode mcp         # 启动MCP服务器
  %(prog)s --mode both        # 同时启动HTTP和MCP服务器
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["http", "mcp", "both"],
        default="http",
        help="启动模式：http（HTTP API服务器）、mcp（MCP服务器）、both（同时启动两个服务器）"
    )
    
    parser.add_argument(
        "--host",
        default=settings.API_HOST,
        help=f"HTTP服务器主机地址（默认：{settings.API_HOST}）"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=settings.API_PORT,
        help=f"HTTP服务器端口（默认：{settings.API_PORT}）"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "http":
            logger.info(f"启动HTTP API服务器 - {args.host}:{args.port}")
            # 更新设置
            settings.API_HOST = args.host
            settings.API_PORT = args.port
            start_http_server()
            
        elif args.mode == "mcp":
            logger.info("启动MCP服务器")
            asyncio.run(start_mcp_server())
            
        elif args.mode == "both":
            logger.info(f"同时启动HTTP API服务器({args.host}:{args.port})和MCP服务器")
            
            # 更新设置
            settings.API_HOST = args.host
            settings.API_PORT = args.port
            
            # 在单独进程中启动MCP服务器
            mcp_process = Process(target=run_mcp_server)
            mcp_process.start()
            
            try:
                # 在主进程中启动HTTP服务器
                start_http_server()
            except KeyboardInterrupt:
                logger.info("正在停止服务器...")
            finally:
                # 停止MCP服务器进程
                if mcp_process.is_alive():
                    mcp_process.terminate()
                    mcp_process.join(timeout=5)
                    if mcp_process.is_alive():
                        mcp_process.kill()
                        mcp_process.join()
                logger.info("所有服务器已停止")
                
    except KeyboardInterrupt:
        logger.info("用户中断，服务器已停止")
    except Exception as e:
        logger.error(f"启动服务器时发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()