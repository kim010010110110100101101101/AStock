"""MCP (Model Context Protocol) 模块

本模块提供MCP服务器实现，为A股数据爬虫项目提供MCP接口支持。
MCP是一个标准化的协议，用于AI模型与外部工具和数据源的交互。

主要功能：
- 提供股票数据的MCP工具接口
- 支持龙虎榜数据查询
- 支持数据爬取任务管理
- 提供统一的错误处理和日志记录
"""

from .server import MCPServer
from .tools import (
    StockDataTool,
    DragonTigerTool,
    CrawlerTool
)

__all__ = [
    'MCPServer',
    'StockDataTool',
    'DragonTigerTool',
    'CrawlerTool'
]