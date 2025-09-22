# LLMFormBridge

> LLM服务转接平台 - 支持OpenAI和Anthropic格式互转的智能代理服务

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18.0+-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

## 🚀 项目简介

LLMFormBridge 是一个强大的LLM（大语言模型）服务转接平台，主要功能是将不同供应商的LLM接口格式进行相互转换。通过统一的管理界面，用户可以轻松配置多个LLM供应商的API凭证，并实现格式之间的无缝转换。

特别支持 **Claude Code** 集成，可以直接使用 Claude Code 的 API 凭证和 claude-relay-service 进行无缝对接。

### 核心特性

- 🔄 **格式转换**：OpenAI ↔ Anthropic 双向格式转换
- 🔐 **安全管理**：API密钥加密存储，JWT认证
- 🎛️ **灵活配置**：支持多凭证、多模型配置
- 📊 **监控统计**：详细的请求日志和使用统计
- 🏗️ **可扩展**：架构设计支持轻松添加新的LLM供应商
- 🌐 **Web界面**：直观的管理界面，支持响应式设计
- ⚡ **Claude Code集成**：完整支持 Claude Code API 和 claude-relay-service
- 🌍 **多语言支持**：支持中文、英文等多种语言内容处理
- 🔗 **多轮对话**：完整的对话上下文保持能力

## 🛠️ 技术栈

### 后端
- **Python 3.12+** - 编程语言
- **FastAPI** - Web框架
- **SQLAlchemy** - ORM
- **Alembic** - 数据库迁移
- **PostgreSQL/SQLite** - 数据库
- **JWT** - 身份认证
- **Cryptography** - 密钥加密

### 前端
- **React 18** - UI框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Material-UI** - UI组件库
- **TailwindCSS** - 样式框架
- **Valtio** - 状态管理
- **Axios** - HTTP客户端

## 🚀 快速开始

### 前置条件

- Python 3.12+
- Node.js 18+
- npm 或 yarn

### 一键启动（推荐）

```bash
# 一键启动所有服务
./start.sh

# 或者查看详细选项
./start.sh help
```

启动完成后访问：
- 前端界面：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

### 启动脚本选项

`start.sh` 脚本支持多种启动模式：

```bash
./start.sh start      # 启动完整服务（默认）
./start.sh stop       # 停止所有服务
./start.sh restart    # 重启所有服务
./start.sh install    # 只安装依赖
./start.sh backend    # 只启动后端
./start.sh frontend   # 只启动前端
./start.sh help       # 显示帮助信息
```

## 📖 使用指南

### 1. 注册和登录

首次访问需要注册账户：
1. 访问 http://localhost:3000
2. 点击"注册"标签
3. 填写用户信息并注册
4. 使用注册的账户登录

### 2. 添加LLM凭证

在凭证管理页面添加LLM服务商的API凭证：

#### 标准 Anthropic API
1. 点击"添加凭证"
2. 选择服务商："Anthropic"
3. 输入凭证名称和API密钥（sk-ant-xxx格式）
4. 保持默认API URL或留空
5. 点击"验证凭证"确保配置正确

#### Claude Code 集成 ⭐
1. 点击"添加凭证"
2. 选择服务商："Anthropic"
3. 输入凭证名称
4. 输入Claude Code API密钥（cr_xxx格式）
5. 设置自定义API URL：`https://your-claude-relay-service.com/api`
6. 点击"验证凭证"确保配置正确

**注意**：Claude Code集成支持完整的 claude-relay-service 功能，包括：
- 自动系统提示词注入
- 完整的Claude Code客户端模拟
- 支持所有Claude模型（包括claude-sonnet-4-20250514）

### 3. 配置模型转发

在模型配置页面设置转发规则：

1. 点击"添加模型配置"
2. 选择已验证的凭证
3. 输入模型名称：
   - **标准模型**：`claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`
   - **Claude Code专用**：`claude-sonnet-4-20250514`（最新模型）
4. 选择目标格式（OpenAI或Anthropic）
5. 设置速率限制（每分钟请求数）
6. 生成的代理API密钥（llmb_xxx格式）用于调用转发服务

### 4. 调用转发服务

#### OpenAI格式调用

```python
import openai

client = openai.OpenAI(
    api_key="llmb_your_proxy_api_key",
    base_url="http://localhost:8000/api/v1"
)

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    max_tokens=1000,
    temperature=0.7
)

print(response.choices[0].message.content)
```

#### Anthropic格式调用

```python
import httpx

headers = {
    "x-api-key": "llmb_your_proxy_api_key",
    "Content-Type": "application/json"
}

data = {
    "model": "claude-3-5-sonnet-20241022",
    "messages": [
        {"role": "user", "content": "Hello!"}
    ],
    "max_tokens": 1000
}

response = httpx.post(
    "http://localhost:8000/api/v1/messages",
    headers=headers,
    json=data
)

print(response.json()["content"][0]["text"])
```

#### cURL调用示例

```bash
# OpenAI 格式
curl -X POST 'http://localhost:8000/api/v1/chat/completions' \
-H 'Authorization: Bearer llmb_your_proxy_api_key' \
-H 'Content-Type: application/json' \
-d '{
  "model": "claude-3-5-sonnet-20241022",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "max_tokens": 1000,
  "temperature": 0.7
}'

# Anthropic 格式
curl -X POST 'http://localhost:8000/api/v1/messages' \
-H 'x-api-key: llmb_your_proxy_api_key' \
-H 'Content-Type: application/json' \
-d '{
  "model": "claude-3-5-sonnet-20241022",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "max_tokens": 1000
}'
```

### 5. 多轮对话支持

平台完整支持多轮对话，自动保持上下文：

```python
# 多轮对话示例
messages = [
    {"role": "user", "content": "我叫张三，请记住我的名字"},
    {"role": "assistant", "content": "好的张三，我已经记住您的名字了。有什么我可以帮助您的吗？"},
    {"role": "user", "content": "我的名字是什么？"}
]

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=messages,
    max_tokens=100
)
# 响应: "您的名字是张三。"
```

### 6. 特性验证

#### 中文支持
```python
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "给我讲个笑话"}],
    max_tokens=500
)
```

#### Token限制精确控制
```python
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Write a long story"}],
    max_tokens=20  # 严格限制20个token
)
# 返回的completion_tokens将准确等于20
```

## 🔧 Docker部署

### 开发环境

```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 生产环境

```bash
# 启动生产环境
docker-compose up -d

# 查看服务状态
docker-compose ps
```

## 🔍 架构说明

### 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 React    │───▶│  后端 FastAPI   │───▶│   LLM服务商     │
│   管理界面      │    │   代理服务      │    │ OpenAI/Claude   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   数据库存储    │
                       │ 凭证/配置/日志  │
                       └─────────────────┘
```

### 核心组件

- **前端管理界面**：React + TypeScript + Material-UI
- **后端API服务**：FastAPI + SQLAlchemy + Alembic
- **适配器层**：AnthropicAdapter + OpenAIAdapter
- **代理服务层**：ProxyService（格式转换和请求转发）
- **数据存储层**：PostgreSQL/SQLite + 加密存储

### 请求流程

1. **用户配置**：在Web界面配置LLM凭证和模型
2. **请求接收**：客户端使用代理API密钥发送请求
3. **身份验证**：验证代理API密钥有效性
4. **格式转换**：根据配置进行OpenAI↔Anthropic格式转换
5. **请求转发**：使用真实凭证调用LLM服务商API
6. **响应处理**：转换响应格式并返回给客户端
7. **日志记录**：记录请求统计和使用量

## 🛠️ 开发指南

### 本地开发

```bash
# 克隆项目
git clone <repository-url>
cd LLMFormBridge

# 后端开发
cd backend
python -m venv ../.venv
source ../.venv/bin/activate  # Windows: ..\.venv\Scripts\activate
pip install -r requirements.txt
PYTHONPATH=. python app/main.py

# 前端开发
cd frontend
npm install
npm run dev
```

### 环境变量配置

项目使用**统一的根目录.env文件**控制前后端所有配置。

#### 📁 配置文件位置
```bash
# 主配置文件（推荐使用）
.env                    # 统一的环境变量配置

# 模板文件（可参考）
.env.example           # 配置模板和说明
backend/.env.example   # 后端配置模板
frontend/.env.example  # 前端配置模板
```

#### 🔧 端口配置说明

**.env文件中包含两组端口配置，必须保持一致：**

```env
# =================== 后端服务器配置 ===================
# 用于后端FastAPI服务和start.sh脚本

BACKEND_HOST=0.0.0.0    # 后端监听地址
BACKEND_PORT=8000       # 后端实际运行端口
FRONTEND_PORT=3000      # 前端端口（脚本显示用）

# =================== 前端专用配置 ===================
# VITE_开头变量只能被前端代码读取（技术限制）

VITE_FRONTEND_PORT=3000      # 前端Vite开发服务器端口
VITE_BACKEND_PORT=8000       # 前端API请求的后端端口 ⚠️必须与BACKEND_PORT一致
VITE_BACKEND_HOST=localhost  # 前端API请求的后端地址
```

#### 📝 修改端口示例

**如果要改为后端10008端口，前端10007端口：**

```env
# 后端配置组
BACKEND_PORT=10008
FRONTEND_PORT=10007

# 前端配置组
VITE_FRONTEND_PORT=10007
VITE_BACKEND_PORT=10008

# 同时更新相关URL
VITE_API_BASE_URL=http://localhost:10008/api
VITE_BACKEND_URL=http://localhost:10008
FRONTEND_URL=http://localhost:10007
```

#### 🔐 完整配置示例

```env
# 应用设置
APP_NAME=LLMFormBridge
DEBUG=true

# 服务器配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=3000

# 数据库配置
DATABASE_URL=sqlite:///./llmbridge.db

# JWT配置
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 加密密钥
ENCRYPTION_KEY=your-32-byte-encryption-key

# 前端配置
VITE_FRONTEND_PORT=3000
VITE_BACKEND_PORT=8000
VITE_API_BASE_URL=http://localhost:8000/api
```

**📌 注意事项：**
- 🔄 两组端口配置必须保持一致，否则前端无法连接后端
- 🎯 修改端口时需同时更新相关的URL配置
- 🔧 使用 `cp .env.example .env` 创建配置文件

### 数据库迁移

```bash
cd backend
# 创建迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head
```

## ❓ 常见问题

### Q: Claude Code集成失败怎么办？

**A**: 检查以下几点：
1. API密钥格式正确（cr_开头）
2. claude-relay-service URL正确且可访问
3. 网络连接正常
4. claude-relay-service服务正在运行

### Q: 为什么返回空内容？

**A**: 可能的原因：
1. max_tokens设置过小
2. 模型名称不正确
3. 系统提示词格式问题（Claude Code需要特定格式）

### Q: 如何查看详细错误信息？

**A**:
1. 查看后端日志：`docker-compose logs -f backend`
2. 检查浏览器控制台
3. 查看数据库中的request_logs表

### Q: 支持哪些模型？

**A**:
- **标准Anthropic**: claude-3-5-sonnet-20241022, claude-3-opus-20240229等
- **Claude Code专用**: claude-sonnet-4-20250514（通过claude-relay-service）
- **OpenAI**: gpt-4, gpt-3.5-turbo等（需配置OpenAI凭证）

### Q: 如何监控API使用量？

**A**:
1. Web界面查看实时统计
2. 查看request_logs表的详细记录
3. 通过API端点获取使用数据

## 🔒 安全注意事项

1. **API密钥加密**：所有LLM API密钥使用AES加密存储
2. **JWT认证**：用户身份验证使用JWT token
3. **代理密钥**：生成的代理API密钥仅用于内部转发
4. **HTTPS部署**：生产环境建议使用HTTPS
5. **定期轮换**：建议定期轮换API密钥和加密密钥

## 📈 性能优化

1. **连接池**：使用httpx异步客户端连接池
2. **缓存策略**：凭证验证结果缓存
3. **并发处理**：FastAPI异步处理请求
4. **数据库优化**：适当的索引和查询优化
5. **监控告警**：集成日志监控和性能告警

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📜 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [React](https://reactjs.org/) - 用户界面构建库
- [Material-UI](https://mui.com/) - React UI组件库
- [claude-relay-service](https://github.com/anthropics/claude-code) - Claude Code集成支持

---

**LLMFormBridge** - 让LLM服务转换变得简单而强大！

如有问题或建议，欢迎提交 [Issue](https://github.com/your-repo/LLMFormBridge/issues) 或参与讨论。
