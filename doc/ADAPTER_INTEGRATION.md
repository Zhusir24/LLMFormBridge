# 新增适配器集成说明

本次更新为 LLMFormBridge 项目添加了四个新的LLM服务提供商适配器支持。

## 新增适配器

### 1. Google Gemini 适配器
- **文件**: `backend/app/adapters/gemini_adapter.py`
- **支持模型**:
  - `gemini-pro`
  - `gemini-pro-vision`
  - `gemini-1.5-pro`
  - `gemini-1.5-flash`
  - `gemini-1.5-flash-8b`
- **特点**:
  - API密钥通过查询参数传递
  - 支持 systemInstruction
  - 角色映射: assistant → model

### 2. 百度文心一言适配器
- **文件**: `backend/app/adapters/ernie_adapter.py`
- **支持模型**:
  - `ERNIE-Bot`
  - `ERNIE-Bot-turbo`
  - `ERNIE-Bot-4`
  - `ERNIE-Speed`
  - `ERNIE-Lite`
  - `ERNIE-Tiny`
- **特点**:
  - 使用 API Key 和 Secret Key 组合（格式: `API_KEY:SECRET_KEY`）
  - 需要先获取 access_token
  - System消息合并到第一个user消息

### 3. 阿里通义千问适配器
- **文件**: `backend/app/adapters/qwen_adapter.py`
- **支持模型**:
  - `qwen-turbo`
  - `qwen-plus`
  - `qwen-max`
  - `qwen-max-longcontext`
  - `qwen-vl-plus`
  - `qwen-vl-max`
- **特点**:
  - 使用 Bearer Token 认证
  - 支持 system 角色
  - 使用 `result_format: message` 返回格式

### 4. Azure OpenAI 适配器
- **文件**: `backend/app/adapters/azure_openai_adapter.py`
- **支持模型**:
  - `gpt-35-turbo`
  - `gpt-35-turbo-16k`
  - `gpt-4`
  - `gpt-4-32k`
  - `gpt-4-turbo`
  - `gpt-4o`
- **特点**:
  - 使用 `api-key` header（非 Authorization）
  - 必须提供 Azure endpoint URL
  - 可选deployment名称（格式: `API_KEY:DEPLOYMENT_NAME`）

## 后端更新

### 核心文件更新

1. **适配器工厂** (`backend/app/adapters/factory.py`)
   - 添加4个新适配器的导入和注册
   - 支持的provider: `gemini`, `ernie`, `qwen`, `azure_openai`

2. **数据库模型** (`backend/app/models/credential.py`)
   - 更新provider字段注释，包含新的供应商类型

3. **测试文件** (`backend/tests/`)
   - `test_gemini_adapter.py` - Gemini适配器测试（17个测试用例）
   - `test_ernie_adapter.py` - 文心一言适配器测试（14个测试用例）
   - `test_qwen_adapter.py` - 通义千问适配器测试（13个测试用例）
   - `test_azure_openai_adapter.py` - Azure OpenAI适配器测试（11个测试用例）

## 前端更新

### UI组件更新

1. **类型定义** (`frontend/src/types/credential.ts`)
   - 更新 `Provider` 类型，添加新的供应商

2. **凭证管理页面** (`frontend/src/pages/Credentials.tsx`)
   - 添加4个新供应商到选择器
   - 更新 `getProviderName()` 函数，提供友好的中文显示名称

### 显示名称映射

| Provider ID    | 显示名称      |
|----------------|--------------|
| `gemini`       | Google Gemini |
| `ernie`        | 百度文心一言  |
| `qwen`         | 阿里通义千问  |
| `azure_openai` | Azure OpenAI  |

## 测试说明

### 运行测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定适配器测试
pytest tests/test_gemini_adapter.py
pytest tests/test_ernie_adapter.py
pytest tests/test_qwen_adapter.py
pytest tests/test_azure_openai_adapter.py

# 运行异步测试
pytest -m asyncio

# 详细输出
pytest -v
```

### 测试覆盖

每个适配器测试覆盖以下功能：
- ✅ 初始化和配置
- ✅ 默认API URL
- ✅ 请求头生成
- ✅ 可用模型列表
- ✅ 请求格式转换（OpenAI ↔ Anthropic ↔ 原生格式）
- ✅ 响应格式转换
- ✅ 模型名称映射

## 使用示例

### 1. Google Gemini

```python
from app.adapters.gemini_adapter import GeminiAdapter

adapter = GeminiAdapter(
    api_key="your_google_api_key"
)

request = LLMRequest(
    model="gemini-pro",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=100
)

response = await adapter.forward_to_gemini(request)
```

### 2. 百度文心一言

```python
from app.adapters.ernie_adapter import ErnieAdapter

adapter = ErnieAdapter(
    api_key="your_api_key:your_secret_key"
)

request = LLMRequest(
    model="ERNIE-Bot",
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=100
)

response = await adapter.forward_to_ernie(request)
```

### 3. 阿里通义千问

```python
from app.adapters.qwen_adapter import QwenAdapter

adapter = QwenAdapter(
    api_key="your_dashscope_api_key"
)

request = LLMRequest(
    model="qwen-turbo",
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=100
)

response = await adapter.forward_to_qwen(request)
```

### 4. Azure OpenAI

```python
from app.adapters.azure_openai_adapter import AzureOpenAIAdapter

adapter = AzureOpenAIAdapter(
    api_key="your_azure_api_key:your_deployment_name",
    api_url="https://your-resource.openai.azure.com"
)

request = LLMRequest(
    model="gpt-35-turbo",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=100
)

response = await adapter.forward_to_openai(request)
```

## Web界面使用

1. **添加凭证**
   - 进入"凭证管理"页面
   - 点击"添加凭证"
   - 选择新的供应商（Google Gemini / 百度文心一言 / 阿里通义千问 / Azure OpenAI）
   - 填写对应的API密钥和配置
   - 点击"验证凭证"

2. **特殊配置说明**
   - **百度文心一言**: API密钥格式为 `API_KEY:SECRET_KEY`
   - **Azure OpenAI**: 必须提供Azure endpoint URL，API密钥可选deployment名称 `API_KEY:DEPLOYMENT_NAME`
   - **Google Gemini**: 直接使用Google API Key
   - **阿里通义千问**: 使用DashScope API Key

3. **模型配置**
   - 创建凭证后，在"模型配置"页面设置转发规则
   - 选择对应的凭证和模型
   - 生成代理API密钥用于调用

## 架构优势

### 统一接口
所有适配器都继承自 `AbstractLLMAdapter`，实现统一的接口：
- `validate_credentials()` - 凭证验证
- `get_available_models()` - 获取可用模型
- `transform_request_to_openai()` - OpenAI格式转换
- `transform_request_to_anthropic()` - Anthropic格式转换
- `transform_response_from_*()` - 响应格式转换

### 格式互转
支持三种主要格式的互相转换：
- OpenAI格式
- Anthropic格式
- 各供应商原生格式

### 扩展性
添加新的LLM供应商只需：
1. 创建新的适配器类
2. 在factory中注册
3. 更新前端类型和UI
4. 编写测试用例

## 注意事项

1. **API密钥安全**: 所有API密钥在数据库中加密存储
2. **速率限制**: 各供应商有不同的速率限制，需要在模型配置中设置
3. **模型名称**: 使用供应商原生模型名称，不要使用映射后的名称
4. **Token计费**: 不同供应商的token计费方式可能不同

## 依赖要求

测试需要以下依赖：
```txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
```

## 贡献指南

如需添加新的LLM供应商适配器，请参考现有适配器的实现模式，并确保：
- ✅ 实现所有抽象方法
- ✅ 支持OpenAI和Anthropic格式转换
- ✅ 编写完整的测试用例
- ✅ 更新前端UI和类型定义
- ✅ 添加使用文档

---

**版本**: v1.2.0
**更新日期**: 2025-10-01
**作者**: Claude Code
