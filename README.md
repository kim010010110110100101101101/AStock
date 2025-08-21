# A股数据爬取系统

一个基于 FastAPI 的 A股数据爬取和分析系统，支持从多个数据源获取股票数据，提供 RESTful API 接口和定时任务调度功能。

## 功能特性

- 🚀 **高性能 API**: 基于 FastAPI 构建，支持异步处理
- 📊 **多数据源**: 支持同花顺、Tushare 和 AKShare 数据源
- 🐅 **龙虎榜数据**: 自动获取和分析龙虎榜交易数据
- 🕐 **定时任务**: 自动化数据更新和维护
- 📝 **完整日志**: 结构化日志记录和错误追踪
- 🛡️ **异常处理**: 完善的错误处理和重试机制
- 💾 **数据存储**: MySQL 数据库支持
- 📈 **股票数据**: 基本信息、日线数据、龙虎榜数据
- 🔌 **双接口支持**: 同时提供 HTTP API 和 MCP (Model Context Protocol) 接口

## 项目结构

```
AStock/
├── app/
│   ├── api/                 # HTTP API 路由
│   │   └── endpoints/       # API 端点
│   ├── mcp/                 # MCP 接口支持
│   │   ├── server.py        # MCP 服务器
│   │   ├── tools.py         # MCP 工具实现
│   │   └── main.py          # MCP 启动脚本
│   ├── core/                # 核心配置
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库连接
│   │   ├── logging.py       # 日志配置
│   │   └── exceptions.py    # 异常处理
│   ├── models/              # 数据模型
│   │   ├── stock.py         # 股票汇总模型
│   │   ├── stock_basic.py   # 股票基本信息
│   │   ├── stock_daily.py   # 股票日线数据
│   │   └── dragon_tiger.py  # 龙虎榜数据模型
│   ├── schemas/             # Pydantic 模型
│   │   ├── stock.py         # 股票相关模式
│   │   └── dragon_tiger.py  # 龙虎榜模式
│   ├── services/            # 业务逻辑
│   │   ├── crawler_service.py    # 爬虫服务
│   │   ├── scheduler.py          # 定时任务
│   │   └── data_sources/         # 数据源
│   │       ├── tonghuashun.py    # 同花顺数据源
│   │       ├── tushare_source.py # Tushare数据源
│   │       └── akshare_source.py # AKShare数据源
│   └── main.py              # FastAPI 应用
├── start_server.py          # 统一启动脚本
├── requirements.txt         # 依赖包
├── .env.example            # 环境变量模板
└── README.md               # 项目说明
```

## 快速开始

### 1. 环境要求

- Python 3.8+
- pip 或 conda

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd AStock

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置必要参数
```

**重要配置项：**

```env
# 数据库配置 (MySQL)
DATABASE_URL=mysql+pymysql://root:111111@localhost:3306/astock

# Tushare Token（可选，用于获取更丰富的数据）
TUSHARE_TOKEN=your_tushare_token_here

# 是否启用定时任务
SCHEDULER_ENABLED=true

# 日志级别
LOG_LEVEL=INFO

# 龙虎榜数据源配置
DRAGON_TIGER_ENABLED=true
DRAGON_TIGER_SOURCE=tonghuashun
```

### 4. 启动服务

系统支持两种接口模式：HTTP API 和 MCP (Model Context Protocol)。

#### HTTP API 服务器

```bash
# 方式1：使用统一启动脚本（推荐）
python start_server.py
# 或指定HTTP模式
python start_server.py --mode http

# 方式2：直接使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### MCP 服务器

```bash
# 启动MCP服务器
python start_server.py --mode mcp

# 或直接运行MCP模块
python -m app.mcp.main
```

#### 同时启动两种服务器

```bash
# 同时启动HTTP API和MCP服务器
python start_server.py --mode both
```

**HTTP API 服务启动后，访问：**
- API 文档: http://localhost:8000/docs
- 系统信息: http://localhost:8000/system/info
- 健康检查: http://localhost:8000/api/v1/health

**MCP 服务器通过标准输入输出与客户端通信，适用于AI模型集成。**

## 接口使用说明

本系统提供两种接口形式：HTTP API 和 MCP (Model Context Protocol) 接口。

### HTTP API 使用说明

#### 健康检查

```bash
# 基础健康检查
curl http://localhost:8000/api/v1/health

# 数据库健康检查
curl http://localhost:8000/api/v1/health/db

# 详细健康检查
curl http://localhost:8000/api/v1/health/detailed
```

### 股票数据查询

```bash
# 获取股票列表
curl "http://localhost:8000/api/v1/stocks?limit=10"

# 获取单个股票信息
curl "http://localhost:8000/api/v1/stocks/000001.SZ"

# 获取股票日线数据
curl "http://localhost:8000/api/v1/stocks/000001.SZ/daily?limit=30"

# 获取市场概况
curl "http://localhost:8000/api/v1/stocks/market/overview"
```

### 数据爬取管理

```bash
# 启动基本信息爬取
curl -X POST "http://localhost:8000/api/v1/crawler/crawl/basic"

# 启动日线数据爬取
curl -X POST "http://localhost:8000/api/v1/crawler/crawl/daily"

# 启动龙虎榜数据爬取
curl -X POST "http://localhost:8000/api/v1/crawler/crawl/dragon-tiger"

# 获取爬虫状态
curl "http://localhost:8000/api/v1/crawler/status"

# 更新单个股票数据
curl -X POST "http://localhost:8000/api/v1/crawler/update/000001.SZ"
```

### 龙虎榜数据查询

```bash
# 获取龙虎榜数据列表
curl "http://localhost:8000/api/v1/dragon-tiger?limit=20"

# 按日期查询龙虎榜数据
curl "http://localhost:8000/api/v1/dragon-tiger?trade_date=20241220"

# 按股票代码查询龙虎榜数据
curl "http://localhost:8000/api/v1/dragon-tiger?ts_code=000617.SZ"

# 获取龙虎榜统计信息
curl "http://localhost:8000/api/v1/dragon-tiger/stats"
```

### MCP 接口使用说明

MCP (Model Context Protocol) 是一个标准化协议，用于AI模型与外部工具和数据源的交互。本系统提供的MCP接口可以让AI模型直接调用股票数据查询功能。

#### MCP 工具列表

系统提供以下MCP工具：

1. **get_stocks** - 获取股票列表
   - 支持按市场、行业筛选
   - 支持分页查询
   - 可筛选活跃/非活跃股票

2. **get_stock_detail** - 获取股票详细信息
   - 包含基本信息、财务数据、最新价格
   - 需要提供股票代码参数

3. **get_dragon_tiger_summary** - 获取龙虎榜汇总数据
   - 支持按日期、股票代码、上榜原因筛选
   - 支持分页查询

4. **get_dragon_tiger_detail** - 获取龙虎榜详细数据
   - 显示具体买卖席位信息
   - 支持按交易类型筛选

5. **start_crawler** - 启动数据爬取任务
   - 支持基本信息、日线数据、全量数据爬取
   - 可指定特定股票或日期范围

#### MCP 客户端集成示例

**Python 客户端示例：**

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # 连接到MCP服务器
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "app.mcp.main"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化
            await session.initialize()
            
            # 获取可用工具
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # 调用工具：获取股票列表
            result = await session.call_tool(
                "get_stocks",
                arguments={"limit": 10, "market": "主板"}
            )
            print(f"Stocks: {result.content[0].text}")
            
            # 调用工具：获取龙虎榜数据
            result = await session.call_tool(
                "get_dragon_tiger_summary",
                arguments={"page_size": 5}
            )
            print(f"Dragon Tiger: {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Claude Desktop 集成：**

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "astock": {
      "command": "python",
      "args": ["-m", "app.mcp.main"],
      "cwd": "/path/to/AStock"
    }
  }
}
```

**VS Code 集成：**

使用 MCP 扩展，配置服务器连接：

```json
{
  "mcp.servers": [
    {
      "name": "AStock Data",
      "command": "python",
      "args": ["-m", "app.mcp.main"],
      "cwd": "/path/to/AStock"
    }
  ]
}
```

#### MCP 工具调用示例

**获取股票信息：**
```json
{
  "tool": "get_stocks",
  "arguments": {
    "limit": 20,
    "market": "主板",
    "industry": "银行",
    "is_active": true
  }
}
```

**获取龙虎榜数据：**
```json
{
  "tool": "get_dragon_tiger_summary",
  "arguments": {
    "trade_date": "2024-12-20",
    "page_size": 10
  }
}
```

**启动数据爬取：**
```json
{
  "tool": "start_crawler",
  "arguments": {
    "crawler_type": "basic"
  }
}
```

## 数据源配置

### 同花顺配置

同花顺龙虎榜数据源无需额外配置，开箱即用。特点：
- 实时获取龙虎榜数据
- 包含详细的买卖席位信息
- 支持历史数据查询
- 免费使用，但请合理控制访问频率

### Tushare 配置

1. 注册 [Tushare](https://tushare.pro/) 账号
2. 获取 API Token
3. 在 `.env` 文件中设置 `TUSHARE_TOKEN`

### AKShare 配置

AKShare 无需配置，开箱即用。但请注意：
- 免费版有访问频率限制
- 数据更新可能有延迟
- 部分高级功能需要付费

### MySQL 数据库配置

1. 安装 MySQL 服务器
2. 创建数据库：`CREATE DATABASE astock CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
3. 配置连接信息：`DATABASE_URL=mysql+pymysql://username:password@localhost:3306/astock`
4. 安装 Python MySQL 驱动：`pip install pymysql mysqlclient`

## 定时任务

系统支持以下定时任务：

- **股票基本信息更新**: 每天早上 8:00
- **日线数据更新**: 每天下午 6:00（可配置）
- **龙虎榜数据更新**: 每天晚上 8:00（交易日）
- **增量数据更新**: 交易日每 30 分钟
- **数据库清理**: 每周日凌晨 2:00
- **系统健康检查**: 每小时

可通过环境变量 `SCHEDULER_ENABLED=false` 禁用定时任务。

## 日志管理

日志文件位置：`logs/` 目录

- `app.log`: 应用主日志
- `error.log`: 错误日志
- `crawler.log`: 爬虫专用日志
- `api.log`: API 访问日志

日志配置：
- 自动轮转（大小限制）
- 自动压缩旧日志
- 可配置保留天数

## 开发指南

### 添加新的数据源

1. 在 `app/services/data_sources/` 创建新的数据源类
2. 实现 `BaseDataSource` 接口
3. 在 `crawler_service.py` 中注册新数据源

### 添加新的 API 端点

1. 在 `app/api/endpoints/` 创建新的路由文件
2. 在 `app/api/__init__.py` 中注册路由
3. 添加相应的 Pydantic 模型到 `app/schemas/`

### 数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

## 部署说明

### Docker 部署

```dockerfile
# Dockerfile 示例
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 生产环境配置

```env
# 生产环境配置示例
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# 使用 MySQL
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/astock

# 安全配置
ALLOWED_HOSTS=["yourdomain.com"]
SECRET_KEY=your-secret-key

# 龙虎榜配置
DRAGON_TIGER_ENABLED=true
SCHEDULER_ENABLED=true
```

## 常见问题

### Q: 数据库连接失败
A: 检查 `DATABASE_URL` 配置，确保数据库服务正常运行。

### Q: Tushare 数据获取失败
A: 检查 `TUSHARE_TOKEN` 是否正确，账户是否有足够积分。

### Q: 定时任务不执行
A: 确认 `ENABLE_SCHEDULER=true` 且系统时区配置正确。

### Q: 内存使用过高
A: 调整爬取批次大小，增加延迟时间，或使用更大的服务器。

## 性能优化

- 使用数据库连接池
- 启用 Redis 缓存（可选）
- 调整爬取频率和批次大小
- 使用 Nginx 反向代理
- 启用 Gzip 压缩

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或联系维护者。

---

**注意**: 本项目仅用于学习和研究目的，请遵守相关数据源的使用条款和法律法规。