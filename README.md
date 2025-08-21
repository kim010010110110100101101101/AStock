# A股数据爬取系统

一个基于 FastAPI 的 A股数据爬取和分析系统，支持从多个数据源获取股票数据，提供 RESTful API 接口和定时任务调度功能。

## 功能特性

- 🚀 **高性能 API**: 基于 FastAPI 构建，支持异步处理
- 📊 **多数据源**: 支持 Tushare 和 AKShare 数据源
- 🕐 **定时任务**: 自动化数据更新和维护
- 📝 **完整日志**: 结构化日志记录和错误追踪
- 🛡️ **异常处理**: 完善的错误处理和重试机制
- 💾 **数据存储**: SQLite/PostgreSQL 数据库支持
- 📈 **股票数据**: 基本信息、日线数据、实时行情

## 项目结构

```
AStock/
├── app/
│   ├── api/                 # API 路由
│   │   └── endpoints/       # API 端点
│   ├── core/                # 核心配置
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库连接
│   │   ├── logging.py       # 日志配置
│   │   └── exceptions.py    # 异常处理
│   ├── models/              # 数据模型
│   │   ├── stock.py         # 股票汇总模型
│   │   ├── stock_basic.py   # 股票基本信息
│   │   └── stock_daily.py   # 股票日线数据
│   ├── schemas/             # Pydantic 模型
│   ├── services/            # 业务逻辑
│   │   ├── crawler_service.py    # 爬虫服务
│   │   ├── scheduler.py          # 定时任务
│   │   └── data_sources/         # 数据源
│   └── main.py              # FastAPI 应用
├── main.py                  # 启动脚本
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
# 数据库配置
DATABASE_URL=sqlite:///./astock.db

# Tushare Token（可选，用于获取更丰富的数据）
TUSHARE_TOKEN=your_tushare_token_here

# 是否启用定时任务
ENABLE_SCHEDULER=true

# 日志级别
LOG_LEVEL=INFO
```

### 4. 启动服务

```bash
# 方式1：使用启动脚本
python main.py

# 方式2：直接使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后，访问：
- API 文档: http://localhost:8000/docs
- 系统信息: http://localhost:8000/system/info
- 健康检查: http://localhost:8000/api/v1/health

## API 使用说明

### 健康检查

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

# 获取爬虫状态
curl "http://localhost:8000/api/v1/crawler/status"

# 更新单个股票数据
curl -X POST "http://localhost:8000/api/v1/crawler/update/000001.SZ"
```

## 数据源配置

### Tushare 配置

1. 注册 [Tushare](https://tushare.pro/) 账号
2. 获取 API Token
3. 在 `.env` 文件中设置 `TUSHARE_TOKEN`

### AKShare 配置

AKShare 无需配置，开箱即用。但请注意：
- 免费版有访问频率限制
- 数据更新可能有延迟
- 部分高级功能需要付费

## 定时任务

系统支持以下定时任务：

- **股票基本信息更新**: 每天早上 8:00
- **日线数据更新**: 每天下午 6:00（可配置）
- **增量数据更新**: 交易日每 30 分钟
- **数据库清理**: 每周日凌晨 2:00
- **系统健康检查**: 每小时

可通过环境变量 `ENABLE_SCHEDULER=false` 禁用定时任务。

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

# 使用 PostgreSQL
DATABASE_URL=postgresql://user:password@localhost/astock

# 安全配置
ALLOWED_HOSTS=["yourdomain.com"]
SECRET_KEY=your-secret-key
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