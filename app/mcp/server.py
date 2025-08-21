"""MCP服务器实现

提供MCP (Model Context Protocol) 服务器，支持工具调用和资源访问。
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Sequence
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    CallToolRequest,
    CallToolResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    ReadResourceRequest,
    ReadResourceResult,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from .tools import StockDataTool, DragonTigerTool, CrawlerTool

logger = get_logger('mcp')


class MCPServer:
    """MCP服务器类
    
    提供股票数据的MCP接口服务，包括：
    - 股票基础数据查询工具
    - 龙虎榜数据查询工具
    - 数据爬取管理工具
    
    Attributes:
        server: MCP服务器实例
        stock_tool: 股票数据工具
        dragon_tiger_tool: 龙虎榜数据工具
        crawler_tool: 爬虫管理工具
    """
    
    def __init__(self):
        """初始化MCP服务器"""
        self.server = Server("astock-mcp-server")
        self.stock_tool = StockDataTool()
        self.dragon_tiger_tool = DragonTigerTool()
        self.crawler_tool = CrawlerTool()
        
        # 注册处理器
        self._register_handlers()
    
    def _register_handlers(self):
        """注册MCP处理器"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """列出所有可用工具"""
            return [
                Tool(
                    name="get_stocks",
                    description="获取股票列表，支持按市场、行业等条件筛选",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "skip": {"type": "integer", "description": "跳过记录数", "default": 0},
                            "limit": {"type": "integer", "description": "返回记录数", "default": 100},
                            "market": {"type": "string", "description": "市场类型筛选"},
                            "industry": {"type": "string", "description": "行业筛选"},
                            "is_active": {"type": "boolean", "description": "是否只返回活跃股票", "default": True}
                        }
                    }
                ),
                Tool(
                    name="get_stock_detail",
                    description="获取单个股票的详细信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ts_code": {"type": "string", "description": "股票代码"}
                        },
                        "required": ["ts_code"]
                    }
                ),
                Tool(
                    name="get_dragon_tiger_summary",
                    description="获取龙虎榜汇总数据",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "trade_date": {"type": "string", "description": "交易日期，格式YYYY-MM-DD"},
                            "stock_code": {"type": "string", "description": "股票代码"},
                            "reason": {"type": "string", "description": "上榜原因关键词"},
                            "page": {"type": "integer", "description": "页码", "default": 1},
                            "page_size": {"type": "integer", "description": "每页数量", "default": 20}
                        }
                    }
                ),
                Tool(
                    name="get_dragon_tiger_detail",
                    description="获取龙虎榜详细数据",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "stock_code": {"type": "string", "description": "股票代码"},
                            "trade_date": {"type": "string", "description": "交易日期，格式YYYY-MM-DD"},
                            "trade_type": {"type": "string", "description": "交易类型：buy/sell"},
                            "page": {"type": "integer", "description": "页码", "default": 1},
                            "page_size": {"type": "integer", "description": "每页数量", "default": 20}
                        },
                        "required": ["stock_code"]
                    }
                ),
                Tool(
                    name="start_crawler",
                    description="启动数据爬取任务",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "crawler_type": {"type": "string", "description": "爬虫类型：basic/daily/all", "default": "basic"},
                            "ts_code": {"type": "string", "description": "股票代码（仅daily类型需要）"},
                            "start_date": {"type": "string", "description": "开始日期"},
                            "end_date": {"type": "string", "description": "结束日期"}
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """处理工具调用"""
            try:
                # 获取数据库会话
                db = next(get_db())
                
                if name == "get_stocks":
                    result = await self.stock_tool.get_stocks(db, **arguments)
                elif name == "get_stock_detail":
                    result = await self.stock_tool.get_stock_detail(db, **arguments)
                elif name == "get_dragon_tiger_summary":
                    result = await self.dragon_tiger_tool.get_summary(db, **arguments)
                elif name == "get_dragon_tiger_detail":
                    result = await self.dragon_tiger_tool.get_detail(db, **arguments)
                elif name == "start_crawler":
                    result = await self.crawler_tool.start_crawler(db, **arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
                
            except Exception as e:
                logger.error(f"Tool call failed: {name}, error: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
            finally:
                if 'db' in locals():
                    db.close()
    
    async def run(self):
        """运行MCP服务器"""
        logger.info("Starting MCP server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="astock-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities()
                )
            )


if __name__ == "__main__":
    server = MCPServer()
    asyncio.run(server.run())