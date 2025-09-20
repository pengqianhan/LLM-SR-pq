# Gemini API 集成指南

本项目现已支持同时使用 OpenAI API 和 Google Gemini API。以下是使用说明：

## 安装依赖

```bash
# 安装最新的 Google Gen AI 客户端
pip install google-genai

# 可选：安装 dotenv 用于环境变量管理
pip install python-dotenv
```

## 环境变量配置

### 使用 Gemini API
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

### 使用 OpenAI API
```bash
export API_KEY="your_openai_api_key_here"
```

### 兼容性支持
如果只设置了 `API_KEY`，Gemini API 也会尝试使用该密钥。

## 使用方法

### 1. 自动检测模式（推荐）

程序会根据模型名称自动选择对应的API：

```bash
# 使用 Gemini
python main_gemini.py --use_api True --api_model "gemini-1.5-flash"

# 使用 OpenAI
python main.py --use_api True --api_model "gpt-3.5-turbo"
```

### 2. 明确指定API类型

```bash
# 明确使用 Gemini API
python main_gemini.py --use_api True --api_type gemini --api_model "gemini-1.5-flash"

# 明确使用 OpenAI API  
python main_gemini.py --use_api True --api_type openai --api_model "gpt-4"
```

## 支持的模型

### Gemini 模型
- `gemini-1.5-pro`
- `gemini-1.5-flash`
- `gemini-1.0-pro`
- `models/gemini-1.5-flash` (带前缀格式也支持)

### OpenAI 模型
- `gpt-3.5-turbo`
- `gpt-4`
- `gpt-4-turbo`
- 其他 OpenAI 模型

## 配置选项

在 `Config` 类中新增了以下配置项：

- `api_type`: API类型，可选值为 "openai", "gemini", "auto"
  - "auto": 根据 `api_model` 自动检测（默认）
  - "openai": 强制使用 OpenAI API
  - "gemini": 强制使用 Gemini API

## 代码结构

### 新增方法

1. **`_draw_samples_api_gemini()`**: 使用最新Google Gen AI Python SDK的Gemini API调用实现
2. **`_determine_api_type()`**: API 类型自动检测逻辑

### 兼容性保证

- 原有的 `_draw_samples_api()` 方法保持不变，继续支持 OpenAI API
- 通过 `draw_samples()` 方法的路由逻辑，自动选择合适的API实现
- 向后兼容，不影响现有代码
- 更新为最新的Google Gen AI Python SDK，提供更好的性能和稳定性

## SDK 迁移说明

### 从旧版本迁移

如果您之前使用的是 `google-generativeai` 库，现在已更新为最新的 `google-genai` 库：

#### 主要变化：
1. **导入方式变化**：
   - 旧版本：`import google.generativeai as genai`
   - 新版本：`from google import genai` 和 `from google.genai import types`

2. **客户端创建**：
   - 旧版本：`genai.configure(api_key=api_key)` + `genai.GenerativeModel(model_name)`
   - 新版本：`client = genai.Client(api_key=api_key)`

3. **内容生成**：
   - 旧版本：`model.generate_content(prompt, generation_config=genai.types.GenerationConfig(...))`
   - 新版本：`client.models.generate_content(model=model_name, contents=prompt, config=types.GenerateContentConfig(...))`

4. **配置参数**：
   - 旧版本：使用 `genai.types.GenerationConfig`
   - 新版本：使用 `types.GenerateContentConfig`

### 安装说明
```bash
# 卸载旧版本（如果已安装）
pip uninstall google-generativeai

# 安装新版本
pip install google-genai
```

## 错误处理

Gemini API 实现包含了完善的错误处理机制：

- 自动重试（最多3次）
- 空响应处理
- 详细的错误日志
- 优雅降级（过滤失败的样本）

## 示例命令

```bash
# 使用 Gemini Flash 模型
python main_gemini.py \
    --use_api True \
    --api_model "gemini-1.5-flash" \
    --spec_path "./specs/specification_oscillator1_numpy.txt" \
    --log_path "./logs/oscillator1_gemini" \
    --problem_name "oscillator1"

# 使用 Gemini Pro 模型
python main_gemini.py \
    --use_api True \
    --api_type gemini \
    --api_model "gemini-1.5-pro" \
    --spec_path "./specs/specification_oscillator1_numpy.txt" \
    --log_path "./logs/oscillator1_gemini_pro" \
    --problem_name "oscillator1"
```

## 注意事项

1. **API 密钥安全**: 请妥善保管API密钥，不要将其提交到代码仓库
2. **费用控制**: 注意监控API调用费用，特别是在大规模实验中
3. **速率限制**: 两种API都有速率限制，代码已包含重试机制
4. **模型选择**: 根据任务需求选择合适的模型，Flash 模型速度更快，Pro 模型质量更高
