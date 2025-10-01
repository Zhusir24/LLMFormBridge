# LLMFormBridge 架构设计文档

## 1. 项目概述

LLMFormBridge 是一个LLM服务转接平台，主要功能是将不同供应商的LLM接口格式进行相互转换。用户可以配置多个LLM供应商的API凭证，选择特定模型进行格式转换，并通过统一的API接口对外提供服务。

### 1.1 核心功能
- **多供应商支持**：目前支持OpenAI和Anthropic，架构支持后续扩展
- **Claude Code集成**：完整支持Claude Code API和claude-relay-service
- **格式转换**：实现不同LLM接口格式的相互转换
- **凭证管理**：支持多个API凭证的配置、验证和管理
- **模型选择**：灵活选择哪些模型进行转发
- **用户管理**：基于JWT的身份认证系统
- **Web管理界面**：提供友好的前端管理界面
- **多轮对话**：完整的对话上下文保持能力
- **多语言支持**：支持中文、英文等多种语言内容处理

### 1.2 技术栈
- **前端**：React 18 + TypeScript + Vite + TailwindCSS + MUI + Valtio
- **后端**：Python 3.12 + FastAPI + SQLAlchemy + Alembic
- **数据库**：PostgreSQL (生产环境) / SQLite (开发环境)
- **认证**：JWT (JSON Web Tokens)
- **部署**：Docker + Docker Compose

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          用户界面层                              │
├─────────────────────────────────────────────────────────────────┤
│  React Frontend (Vite + TypeScript + TailwindCSS + MUI)       │
│  - 用户认证界面  - 凭证管理界面  - 模型配置界面  - 监控面板     │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTPS/REST API
┌─────────────────────────────┴───────────────────────────────────┐
│                        API网关层                               │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Server                                               │
│  - JWT认证中间件  - 请求验证  - 响应处理  - 错误处理            │
└─────────┬───────────────────────────────┬─────────────────────────┘
         │                               │
┌─────────┴───────────┐         ┌─────────┴─────────────────────────┐
│     管理API模块      │         │        转发API模块               │
├─────────────────────┤         ├───────────────────────────────────┤
│ - 用户管理          │         │ - LLM服务转发                    │
│ - 凭证管理          │         │ - 格式转换                       │
│ - 模型配置          │         │ - 负载均衡                       │
│ - 监控统计          │         │ - 错误处理                       │
└─────────┬───────────┘         └─────────┬─────────────────────────┘
         │                               │
         └───────────┬───────────────────┘
                     │
┌─────────────────────┴───────────────────────────────────────────┐
│                    LLM适配器层                                 │
├─────────────────────────────────────────────────────────────────┤
│  AbstractLLMAdapter (抽象基类)                                │
│  ├── OpenAIAdapter     ├── AnthropicAdapter    ├── 扩展适配器   │
│  - 请求格式转换  - 响应格式转换  - 错误处理  - 重试机制        │
└─────────┬───────────────────────┬─────────────────────────────────┘
         │                       │
┌─────────┴─────────┐   ┌─────────┴─────────┐
│   OpenAI API      │   │  Anthropic API    │
│   GPT-4, GPT-3.5  │   │  Claude-3.5       │
└───────────────────┘   └───────────────────┘
         │                       │
┌─────────┴───────────────────────┴─────────────────────────────────┐
│                        数据存储层                               │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL Database                                           │
│  - 用户表  - 凭证表  - 模型配置表  - 转发规则表  - 日志表      │
└─────────────────────────────────────────────────────────────────┘
```

## 3. 后端架构设计

### 3.1 项目结构
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py              # 配置管理
│   ├── database.py            # 数据库连接
│   ├── dependencies.py        # 依赖注入
│   ├── exceptions.py          # 自定义异常
│   ├── middleware/            # 中间件
│   │   ├── __init__.py
│   │   ├── auth.py            # JWT认证中间件
│   │   ├── cors.py            # CORS中间件
│   │   └── logging.py         # 日志中间件
│   ├── models/                # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py            # 用户模型
│   │   ├── credential.py      # 凭证模型
│   │   ├── model_config.py    # 模型配置
│   │   └── forwarding_rule.py # 转发规则
│   ├── schemas/               # Pydantic模式
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── credential.py
│   │   ├── model_config.py
│   │   └── llm_request.py
│   ├── api/                   # API路由
│   │   ├── __init__.py
│   │   ├── auth.py            # 认证相关API
│   │   ├── users.py           # 用户管理API
│   │   ├── credentials.py     # 凭证管理API
│   │   ├── models.py          # 模型配置API
│   │   └── proxy.py           # LLM转发API
│   ├── services/              # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── auth_service.py    # 认证服务
│   │   ├── credential_service.py # 凭证服务
│   │   ├── model_service.py   # 模型服务
│   │   └── proxy_service.py   # 转发服务
│   ├── adapters/              # LLM适配器
│   │   ├── __init__.py
│   │   ├── base.py            # 抽象基类
│   │   ├── openai_adapter.py  # OpenAI适配器
│   │   └── anthropic_adapter.py # Anthropic适配器
│   └── utils/                 # 工具函数
│       ├── __init__.py
│       ├── security.py        # 安全工具
│       ├── validation.py      # 验证工具
│       └── logging.py         # 日志工具
├── alembic/                   # 数据库迁移
├── tests/                     # 测试文件
├── requirements.txt           # 依赖列表
└── Dockerfile                 # Docker配置
```

### 3.2 数据模型设计

#### 3.2.1 用户表 (users)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.2.2 凭证表 (credentials)
```sql
CREATE TABLE credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL, -- 'openai', 'anthropic'
    api_key_encrypted TEXT NOT NULL,
    api_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_validated BOOLEAN DEFAULT FALSE,
    validation_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);
```

#### 3.2.3 模型配置表 (model_configs)
```sql
CREATE TABLE model_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    credential_id UUID REFERENCES credentials(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    target_format VARCHAR(50) NOT NULL, -- 'openai', 'anthropic'
    is_enabled BOOLEAN DEFAULT TRUE,
    proxy_api_key VARCHAR(255) NOT NULL, -- 用于访问转发服务的密钥
    rate_limit INTEGER DEFAULT 100, -- 每分钟请求限制
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(credential_id, model_name, target_format)
);
```

#### 3.2.4 请求日志表 (request_logs)
```sql
CREATE TABLE request_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_config_id UUID REFERENCES model_configs(id),
    request_id VARCHAR(100),
    method VARCHAR(10),
    path TEXT,
    source_format VARCHAR(50),
    target_format VARCHAR(50),
    status_code INTEGER,
    response_time_ms INTEGER,
    tokens_used INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.3 API端点设计

#### 3.3.1 认证API (/api/auth)
```
POST /api/auth/register     # 用户注册
POST /api/auth/login        # 用户登录
POST /api/auth/refresh      # 刷新令牌
POST /api/auth/logout       # 用户登出
```

#### 3.3.2 凭证管理API (/api/credentials)
```
GET    /api/credentials           # 获取凭证列表
POST   /api/credentials           # 创建新凭证
PUT    /api/credentials/{id}      # 更新凭证
DELETE /api/credentials/{id}      # 删除凭证
POST   /api/credentials/{id}/validate  # 验证凭证
```

#### 3.3.3 模型配置API (/api/models)
```
GET    /api/models                # 获取模型配置列表
POST   /api/models                # 创建模型配置
PUT    /api/models/{id}           # 更新模型配置
DELETE /api/models/{id}           # 删除模型配置
GET    /api/models/{id}/info      # 获取模型详细信息
```

#### 3.3.4 LLM转发API (/api/v1)
```
POST /api/v1/chat/completions    # OpenAI兼容接口
POST /api/v1/messages            # Anthropic兼容接口
GET  /api/v1/models              # 获取可用模型列表
```

## 4. 前端架构设计

### 4.1 项目结构
```
frontend/
├── src/
│   ├── main.tsx               # 应用入口
│   ├── App.tsx                # 根组件
│   ├── index.css              # 全局样式
│   ├── components/            # 可复用组件
│   │   ├── common/            # 通用组件
│   │   │   ├── Layout.tsx     # 布局组件
│   │   │   ├── Header.tsx     # 头部组件
│   │   │   ├── Sidebar.tsx    # 侧边栏组件
│   │   │   └── Loading.tsx    # 加载组件
│   │   ├── auth/              # 认证组件
│   │   │   ├── LoginForm.tsx
│   │   │   └── RegisterForm.tsx
│   │   ├── credentials/       # 凭证管理组件
│   │   │   ├── CredentialList.tsx
│   │   │   ├── CredentialForm.tsx
│   │   │   └── CredentialCard.tsx
│   │   └── models/            # 模型配置组件
│   │       ├── ModelList.tsx
│   │       ├── ModelForm.tsx
│   │       └── ModelCard.tsx
│   ├── pages/                 # 页面组件
│   │   ├── Dashboard.tsx      # 仪表板
│   │   ├── Login.tsx          # 登录页
│   │   ├── Credentials.tsx    # 凭证管理页
│   │   ├── Models.tsx         # 模型配置页
│   │   └── Logs.tsx           # 日志页
│   ├── store/                 # 状态管理 (Valtio)
│   │   ├── auth.ts            # 认证状态
│   │   ├── credentials.ts     # 凭证状态
│   │   ├── models.ts          # 模型状态
│   │   └── ui.ts              # UI状态
│   ├── services/              # API服务
│   │   ├── api.ts             # API客户端配置
│   │   ├── auth.ts            # 认证API
│   │   ├── credentials.ts     # 凭证API
│   │   └── models.ts          # 模型API
│   ├── hooks/                 # 自定义Hooks
│   │   ├── useAuth.ts         # 认证Hook
│   │   ├── useCredentials.ts  # 凭证Hook
│   │   └── useModels.ts       # 模型Hook
│   ├── types/                 # TypeScript类型定义
│   │   ├── auth.ts
│   │   ├── credential.ts
│   │   └── model.ts
│   └── utils/                 # 工具函数
│       ├── constants.ts       # 常量定义
│       ├── helpers.ts         # 帮助函数
│       └── validation.ts      # 表单验证
├── public/                    # 静态资源
├── index.html                 # HTML模板
├── vite.config.ts            # Vite配置
├── tailwind.config.js        # TailwindCSS配置
├── tsconfig.json             # TypeScript配置
└── package.json              # 依赖配置
```

### 4.2 状态管理设计 (Valtio)

#### 4.2.1 认证状态 (store/auth.ts)
```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const authStore = proxy<AuthState>({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: false,
  isLoading: false,
});
```

#### 4.2.2 凭证状态 (store/credentials.ts)
```typescript
interface CredentialState {
  credentials: Credential[];
  selectedCredential: Credential | null;
  isLoading: boolean;
  validationStatus: Record<string, boolean>;
}
```

#### 4.2.3 模型状态 (store/models.ts)
```typescript
interface ModelState {
  modelConfigs: ModelConfig[];
  selectedModel: ModelConfig | null;
  availableModels: AvailableModel[];
  isLoading: boolean;
}
```

### 4.3 路由设计
```typescript
const routes = [
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'credentials', element: <Credentials /> },
      { path: 'models', element: <Models /> },
      { path: 'logs', element: <Logs /> },
    ],
  },
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },
];
```

## 5. LLM适配器架构

### 5.1 抽象基类设计
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel

class LLMRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    max_tokens: int = 1000
    temperature: float = 0.7
    stream: bool = False

class LLMResponse(BaseModel):
    id: str
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class AbstractLLMAdapter(ABC):
    def __init__(self, api_key: str, api_url: str = None):
        self.api_key = api_key
        self.api_url = api_url

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """验证API凭证是否有效"""
        pass

    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        pass

    @abstractmethod
    async def transform_request(self, request: LLMRequest, target_format: str) -> Dict[str, Any]:
        """转换请求格式"""
        pass

    @abstractmethod
    async def transform_response(self, response: Dict[str, Any], source_format: str) -> LLMResponse:
        """转换响应格式"""
        pass

    @abstractmethod
    async def send_request(self, transformed_request: Dict[str, Any]) -> Dict[str, Any]:
        """发送请求到LLM服务"""
        pass
```

### 5.2 OpenAI适配器
```python
class OpenAIAdapter(AbstractLLMAdapter):
    def __init__(self, api_key: str, api_url: str = "https://api.openai.com/v1"):
        super().__init__(api_key, api_url)

    async def validate_credentials(self) -> bool:
        # 实现OpenAI凭证验证逻辑
        pass

    async def transform_request(self, request: LLMRequest, target_format: str) -> Dict[str, Any]:
        if target_format == "anthropic":
            # OpenAI格式 -> Anthropic格式转换
            return {
                "model": self._map_model_name(request.model, "anthropic"),
                "messages": self._convert_messages_to_anthropic(request.messages),
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            }
        return request.dict()
```

### 5.3 Anthropic适配器（含Claude Code集成）
```python
class AnthropicAdapter(AbstractLLMAdapter):
    def __init__(self, api_key: str, api_url: str = "https://api.anthropic.com/v1"):
        super().__init__(api_key, api_url)

        # Claude Code专用配置
        if self.api_url != self.get_default_api_url() and self.api_key.startswith("cr_"):
            # 创建没有默认头部的干净客户端
            self.client = httpx.AsyncClient(timeout=60.0, headers={})
        else:
            self.client = httpx.AsyncClient(timeout=60.0)

    def get_headers(self) -> Dict[str, str]:
        # 为Claude Code专用凭证使用简化的headers
        if self.api_url != self.get_default_api_url() and self.api_key.startswith("cr_"):
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
                "User-Agent": "claude-cli/1.0.102 (external, cli)",
                "Accept": "application/json",
                "x-stainless-retry-count": "0",
                "x-stainless-timeout": "60",
                "x-app": "cli"
            }
        else:
            return {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }

    def transform_request_to_anthropic(self, request: LLMRequest) -> Dict[str, Any]:
        # 为Claude Code专用凭证设置特殊的system格式
        if self.api_url != self.get_default_api_url() and self.api_key.startswith("cr_"):
            # claude-relay-service要求system字段为数组格式
            claude_code_system = {
                "type": "text",
                "text": "You are Claude Code, Anthropic's official CLI for Claude.",
                "cache_control": {"type": "ephemeral"}
            }
            anthropic_request["system"] = [claude_code_system]

        return anthropic_request
```

### 5.4 适配器工厂
```python
class LLMAdapterFactory:
    _adapters = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
    }

    @classmethod
    def create_adapter(cls, provider: str, api_key: str, api_url: str = None) -> AbstractLLMAdapter:
        if provider not in cls._adapters:
            raise ValueError(f"Unsupported provider: {provider}")

        adapter_class = cls._adapters[provider]
        return adapter_class(api_key, api_url)

    @classmethod
    def register_adapter(cls, provider: str, adapter_class: type):
        """注册新的适配器类型"""
        cls._adapters[provider] = adapter_class
```

## 6. Claude Code集成架构

### 6.1 Claude Code集成概述

Claude Code是Anthropic官方的CLI工具，通过claude-relay-service提供API服务。LLMFormBridge完整支持Claude Code集成，可以直接使用Claude Code的API凭证（cr_前缀）和自定义API URL进行无缝对接。

### 6.2 核心集成特性

#### 6.2.1 凭证识别
- **API密钥格式**：支持`cr_`前缀的Claude Code专用密钥
- **URL检测**：自动识别claude-relay-service URL（非官方Anthropic API）
- **双模式支持**：同时支持标准Anthropic API和Claude Code API

#### 6.2.2 客户端模拟
```python
# Claude Code专用Headers
headers = {
    "Authorization": f"Bearer {self.api_key}",
    "Content-Type": "application/json",
    "anthropic-version": "2023-06-01",
    "User-Agent": "claude-cli/1.0.102 (external, cli)",
    "Accept": "application/json",
    "x-stainless-retry-count": "0",
    "x-stainless-timeout": "60",
    "x-app": "cli"
}
```

#### 6.2.3 系统提示词自动注入
```python
# Claude Code必需的系统提示词格式
system_prompt = [
    {
        "type": "text",
        "text": "You are Claude Code, Anthropic's official CLI for Claude.",
        "cache_control": {"type": "ephemeral"}
    }
]
```

### 6.3 请求处理流程

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  用户请求       │───▶│  LLMFormBridge  │───▶│ claude-relay-   │
│  (OpenAI格式)   │    │  格式转换       │    │ service         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Anthropic格式   │    │ Claude Code     │
                       │ 系统提示词注入  │    │ 原生API调用     │
                       └─────────────────┘    └─────────────────┘
```

### 6.4 关键技术实现

#### 6.4.1 凭证验证
```python
async def validate_credentials(self) -> bool:
    test_request = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 50
    }

    # Claude Code专用系统格式
    if self.api_url != self.get_default_api_url() and self.api_key.startswith("cr_"):
        test_request["system"] = [
            {
                "type": "text",
                "text": "You are Claude Code, Anthropic's official CLI for Claude.",
                "cache_control": {"type": "ephemeral"}
            }
        ]
        endpoint = "v1/messages"  # claude-relay-service路径
    else:
        endpoint = "messages"     # 官方API路径
```

#### 6.4.2 响应处理
```python
def transform_response_from_anthropic(self, response: Dict[str, Any]) -> LLMResponse:
    content = response.get("content", [])

    # 处理claude-relay-service返回的content数组格式
    if content and isinstance(content, list) and len(content) > 0:
        first_item = content[0]
        if isinstance(first_item, dict) and "text" in first_item:
            text = first_item.get("text", "")
        else:
            text = str(first_item)

    # 转换为OpenAI格式
    return LLMResponse(
        choices=[{
            "index": 0,
            "message": {"role": "assistant", "content": text},
            "finish_reason": "stop"
        }],
        usage={
            "prompt_tokens": response.get("usage", {}).get("input_tokens", 0),
            "completion_tokens": response.get("usage", {}).get("output_tokens", 0),
            "total_tokens": response.get("usage", {}).get("input_tokens", 0) +
                           response.get("usage", {}).get("output_tokens", 0)
        }
    )
```

### 6.5 支持的模型

#### 6.5.1 Claude Code专用模型
- `claude-sonnet-4-20250514` - 最新的Claude 4模型
- `claude-3-5-sonnet-20241022` - Claude 3.5 Sonnet
- `claude-3-5-haiku-20241022` - Claude 3.5 Haiku
- `claude-3-opus-20240229` - Claude 3 Opus

#### 6.5.2 功能特性验证
- ✅ **中文支持**：完整支持中文内容处理
- ✅ **多轮对话**：上下文保持和对话连续性
- ✅ **Token控制**：精确的token限制和计数
- ✅ **参数映射**：temperature、max_tokens等参数完整传递

### 6.6 配置示例

#### 6.6.1 Web界面配置
1. 凭证管理 → 添加凭证
2. 选择供应商：Anthropic
3. 输入Claude Code API密钥：`cr_xxx...`
4. 设置API URL：`https://your-claude-relay-service.com/api`
5. 验证凭证

#### 6.6.2 API调用示例
```bash
# OpenAI格式调用Claude Code
curl -X POST 'http://localhost:8000/api/v1/chat/completions' \
-H 'Authorization: Bearer llmb_your_proxy_key' \
-H 'Content-Type: application/json' \
-d '{
  "model": "claude-sonnet-4-20250514",
  "messages": [{"role": "user", "content": "Hello"}],
  "max_tokens": 1000
}'
```

### 6.7 故障排除

#### 6.7.1 常见问题
- **凭证验证失败**：检查API密钥格式（cr_前缀）和URL可访问性
- **空响应内容**：确认claude-relay-service版本兼容性
- **系统提示词错误**：验证system字段数组格式正确

#### 6.7.2 调试方法
- 查看后端日志中的请求详情
- 验证claude-relay-service服务状态
- 测试原始curl命令是否工作

## 7. 安全设计

### 7.1 认证与授权
- **JWT令牌**：使用RS256算法签名，包含用户ID、角色等信息
- **令牌刷新**：实现refresh token机制，减少令牌泄露风险
- **权限控制**：基于角色的访问控制(RBAC)

### 6.2 数据安全
- **API密钥加密**：使用AES-256加密存储第三方API密钥
- **敏感数据脱敏**：日志中不记录完整API密钥
- **数据库安全**：数据库连接使用SSL，敏感字段加密

### 6.3 API安全
- **请求验证**：严格的输入验证和参数检查
- **率限制**：实现基于用户的API调用频率限制
- **CORS配置**：合理配置跨域访问策略

## 7. 部署架构

### 7.1 容器化部署
```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/llmbridge
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=llmbridge
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 7.2 环境配置
- **开发环境**：使用SQLite数据库，热重载
- **测试环境**：使用Docker Compose，模拟生产环境
- **生产环境**：使用PostgreSQL，配置SSL，启用监控

## 8. 扩展性设计

### 8.1 新供应商支持
1. 实现新的适配器类，继承`AbstractLLMAdapter`
2. 在`LLMAdapterFactory`中注册新适配器
3. 更新前端模型选择界面
4. 添加相应的数据库迁移

### 8.2 监控与日志
- **性能监控**：集成Prometheus + Grafana
- **错误追踪**：使用Sentry进行错误收集
- **访问日志**：详细记录API调用情况
- **健康检查**：实现服务健康状态检查端点

### 8.3 高可用性
- **负载均衡**：支持多实例部署
- **数据库主从**：配置PostgreSQL主从复制
- **缓存策略**：使用Redis缓存热点数据
- **容错机制**：实现API调用重试和熔断

## 9. 开发计划

### 9.1 第一阶段：核心功能开发
1. 用户认证系统
2. 凭证管理功能
3. 基础LLM适配器（OpenAI + Anthropic）
4. 简单的转发功能

### 9.2 第二阶段：完善功能
1. 模型配置管理
2. 请求日志和监控
3. 前端管理界面完善
4. API文档和测试

### 9.3 第三阶段：优化和扩展
1. 性能优化
2. 更多供应商支持
3. 高级功能（缓存、负载均衡等）
4. 部署和运维工具

这个架构设计为LLMFormBridge项目提供了清晰的技术路线和实现方案，确保项目的可扩展性、可维护性和安全性。