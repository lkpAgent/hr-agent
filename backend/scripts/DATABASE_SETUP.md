# HR Agent 数据库初始化指南

本指南介绍如何初始化 HR Agent 数据库并创建管理员账号。

## 📋 目录

- [快速开始](#快速开始)
- [详细说明](#详细说明)
- [脚本说明](#脚本说明)
- [常见问题](#常见问题)

## 🚀 快速开始

### 1. 完整数据库初始化（推荐）

```bash
# 进入后端目录
cd backend

# 运行完整初始化（包含数据库创建、表结构、管理员账号）
python scripts/init_database.py init
```

默认管理员账号信息：
- **用户名**: `admin`
- **邮箱**: `admin@hr-agent.com`
- **密码**: `admin123`

### 2. 自定义管理员账号初始化

```bash
# 使用自定义管理员信息初始化
python scripts/init_database.py init-custom your-email@company.com your-password your-username
```

## 📖 详细说明

### 数据库初始化脚本 (`init_database.py`)

这个脚本提供完整的数据库初始化功能：

#### 可用命令：

```bash
# 1. 标准初始化
python scripts/init_database.py init

# 2. 自定义初始化
python scripts/init_database.py init-custom <email> <password> [username]

# 3. 重置数据库（删除并重新创建）
python scripts/init_database.py reset

# 4. 仅创建管理员账号（数据库必须已存在）
python scripts/init_database.py admin-only
```

#### 初始化过程包括：

1. ✅ 创建数据库（如果不存在）
2. ✅ 安装必要的 PostgreSQL 扩展（uuid-ossp, vector）
3. ✅ 创建所有数据表
4. ✅ 创建管理员账号
5. ✅ 创建示例知识库和FAQ（可选）

### 管理员账号管理脚本 (`create_admin.py`)

专门用于管理员账号的创建和管理：

#### 可用命令：

```bash
# 1. 交互式创建管理员
python scripts/create_admin.py create

# 2. 快速创建默认管理员
python scripts/create_admin.py create-quick

# 3. 指定参数创建管理员
python scripts/create_admin.py create-custom <username> <email> <password> <full_name>

# 4. 列出所有管理员
python scripts/create_admin.py list

# 5. 修改用户密码
python scripts/create_admin.py change-password <username>

# 6. 提升用户为管理员
python scripts/create_admin.py promote <username>
```

## 🗂️ 脚本说明

### 1. `init_database.py` - 完整数据库初始化

**功能特点：**
- 自动创建数据库
- 安装必要扩展
- 创建所有表结构
- 创建管理员账号
- 可选创建示例数据

**适用场景：**
- 首次部署系统
- 开发环境搭建
- 测试环境重置

### 2. `create_admin.py` - 管理员账号管理

**功能特点：**
- 创建新管理员账号
- 修改用户密码
- 提升普通用户为管理员
- 列出现有管理员

**适用场景：**
- 添加新管理员
- 密码重置
- 用户权限管理

### 3. `db_manager.py` - 数据库迁移管理

**功能特点：**
- Alembic 迁移管理
- 数据库版本控制
- 结构变更管理

**适用场景：**
- 数据库结构更新
- 版本迁移
- 开发过程中的结构变更

## 🔧 使用示例

### 场景1：首次部署

```bash
# 1. 确保数据库服务运行
# 2. 配置 .env 文件中的数据库连接信息
# 3. 运行初始化
cd backend
python scripts/init_database.py init
```

### 场景2：开发环境重置

```bash
# 重置数据库（删除所有数据并重新初始化）
python scripts/init_database.py reset
```

### 场景3：添加新管理员

```bash
# 交互式创建
python scripts/create_admin.py create

# 或者直接指定参数
python scripts/create_admin.py create-custom newadmin admin@company.com password123 "New Admin"
```

### 场景4：忘记管理员密码

```bash
# 重置密码
python scripts/create_admin.py change-password admin
```

## ❓ 常见问题

### Q1: 数据库连接失败

**错误**: `ConnectionRefusedError`

**解决方案**:
1. 检查 PostgreSQL 服务是否运行
2. 验证 `.env` 文件中的数据库配置
3. 确保数据库用户有足够权限

### Q2: 扩展安装失败

**错误**: `extension "vector" does not exist`

**解决方案**:
1. 确保安装了 pgvector 扩展
2. 检查数据库用户是否有创建扩展的权限

### Q3: 管理员账号已存在

**错误**: `User already exists`

**解决方案**:
1. 使用不同的用户名或邮箱
2. 或者使用 `change-password` 命令重置密码

### Q4: 权限不足

**错误**: `permission denied`

**解决方案**:
1. 检查数据库用户权限
2. 确保用户可以创建数据库和表

## 🔐 安全建议

1. **修改默认密码**: 生产环境中务必修改默认管理员密码
2. **使用强密码**: 密码至少8位，包含字母、数字和特殊字符
3. **限制管理员数量**: 只创建必要的管理员账号
4. **定期更新密码**: 建议定期更换管理员密码

## 📞 获取帮助

如果遇到问题，可以：

1. 查看脚本的详细日志输出
2. 检查数据库连接配置
3. 验证 PostgreSQL 服务状态
4. 查看应用程序日志文件

---

**注意**: 在生产环境中使用这些脚本前，请确保已经备份了重要数据。