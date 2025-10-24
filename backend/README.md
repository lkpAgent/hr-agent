# HR Agent Backend

一个基于FastAPI和LangChain的智能HR助手后端系统，提供AI驱动的对话、文档管理和知识库功能。

## 功能特性

### 🤖 AI对话系统
- 基于OpenAI GPT的智能对话
- 支持流式响应
- 上下文感知的对话历史
- 智能建议生成

### 👥 用户管理
- JWT认证系统
- 基于角色的权限控制（员工/HR/管理员）
- 用户资料管理
- 安全的密码处理

### 📄 文档管理
- 文档上传和处理
- 文本提取和向量化
- 基于向量相似度的文档搜索
- 支持多种文件格式（PDF、Word、TXT等）

### 📚 知识库系统
- 知识库创建和管理
- FAQ管理
- 文档分类和标签
- 全文搜索功能

### 🔍 向量搜索
- 基于pgvector的向量存储
- 语义搜索功能
- 文档块化处理
- 相关性评分

## 技术栈

- **Web框架**: FastAPI
- **数据库**: PostgreSQL + pgvector
- **ORM**: SQLAlchemy (异步)
- **AI/LLM**: LangChain + OpenAI
- **认证**: JWT + OAuth2
- **数据验证**: Pydantic
- **日志**: Structlog
- **测试**: Pytest

## 项目结构

```
backend/
├── app/
│   ├── api/                    # API路由
│   │   ├── deps.py            # 依赖注入
│   │   └── v1/                # API v1版本
│   │       ├── api.py         # 主路由器
│   │       └── endpoints/     # 具体端点
│   ├── core/                  # 核心配置
│   │   ├── config.py         # 应用配置
│   │   ├── database.py       # 数据库配置
│   │   ├── logging.py        # 日志配置
│   │   ├── middleware.py     # 中间件
│   │   └── security.py       # 安全工具
│   ├── models/               # 数据库模型
│   │   ├── base.py          # 基础模型
│   │   ├── user.py          # 用户模型
│   │   ├── conversation.py  # 对话模型
│   │   ├── document.py      # 文档模型
│   │   └── knowledge_base.py # 知识库模型
│   ├── schemas/             # Pydantic模式
│   │   ├── user.py         # 用户模式
│   │   ├── conversation.py # 对话模式
│   │   ├── document.py     # 文档模式
│   │   ├── knowledge_base.py # 知识库模式
│   │   └── chat.py         # 聊天模式
│   └── services/           # 业务逻辑层
│       ├── llm_service.py  # LLM服务
│       ├── chat_service.py # 聊天服务
│       ├── user_service.py # 用户服务
│       ├── conversation_service.py # 对话服务
│       ├── document_service.py # 文档服务
│       └── knowledge_base_service.py # 知识库服务
├── main.py                 # 应用入口
├── requirements.txt        # 依赖列表
└── README.md              # 项目文档
```

## 快速开始

### 1. 环境要求

- Python 3.9+
- PostgreSQL 14+
- Redis (可选，用于缓存)

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 环境配置

创建 `.env` 文件：

```env
# 应用配置
APP_NAME="HR Agent"
VERSION="1.0.0"
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/hr_agent
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# JWT配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo

# 文件上传配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

### 4. 数据库设置

```bash
# 创建数据库
createdb hr_agent

# 启用pgvector扩展
psql -d hr_agent -c "CREATE EXTENSION vector;"
```

### 5. 运行应用

```bash
# 开发模式
python main.py

# 或使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API端点

### 认证
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新令牌
- `GET /api/v1/auth/me` - 获取当前用户信息

### 聊天
- `POST /api/v1/chat/send` - 发送消息
- `POST /api/v1/chat/stream` - 流式发送消息
- `GET /api/v1/chat/suggestions` - 获取建议
- `POST /api/v1/chat/feedback` - 提交反馈

### 用户管理
- `GET /api/v1/users/` - 获取用户列表
- `GET /api/v1/users/{user_id}` - 获取用户信息
- `PUT /api/v1/users/{user_id}` - 更新用户信息
- `DELETE /api/v1/users/{user_id}` - 删除用户

### 对话管理
- `GET /api/v1/conversations/` - 获取对话列表
- `POST /api/v1/conversations/` - 创建对话
- `GET /api/v1/conversations/{conversation_id}` - 获取对话详情
- `PUT /api/v1/conversations/{conversation_id}` - 更新对话
- `DELETE /api/v1/conversations/{conversation_id}` - 删除对话

### 文档管理
- `GET /api/v1/documents/` - 获取文档列表
- `POST /api/v1/documents/upload` - 上传文档
- `GET /api/v1/documents/{document_id}` - 获取文档详情
- `DELETE /api/v1/documents/{document_id}` - 删除文档
- `POST /api/v1/documents/search` - 搜索文档

### 知识库管理
- `GET /api/v1/knowledge-bases/` - 获取知识库列表
- `POST /api/v1/knowledge-bases/` - 创建知识库
- `GET /api/v1/knowledge-bases/{kb_id}` - 获取知识库详情
- `PUT /api/v1/knowledge-bases/{kb_id}` - 更新知识库
- `DELETE /api/v1/knowledge-bases/{kb_id}` - 删除知识库

## 开发指南

### 代码规范

```bash
# 代码格式化
black app/
isort app/

# 代码检查
flake8 app/
mypy app/
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

## 部署

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 生产环境配置

```bash
# 使用gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
### 前端部署配置,比如部署在{nginx_home}/html/hragent，则指定base路径编译
# npm run build -- --base=hragent