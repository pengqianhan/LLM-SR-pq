# SmolAgents Migration Guide

## Overview

This repository now supports a **simplified architecture using HuggingFace SmolAgents**, which eliminates the need for a custom LLM inference server and streamlines the code generation workflow.

### What Changed?

**Before (Original Architecture):**
- Custom Flask-based inference server (`llm_engine/engine.py`)
- Manual HTTP requests to local/remote models
- Custom LLM wrapper classes with API-specific logic
- Separate code paths for OpenAI, Gemini, local models

**After (SmolAgents Architecture):**
- ✅ No separate inference server needed
- ✅ Unified model interface via SmolAgents
- ✅ Support for local models, HF Inference API, OpenAI, Gemini via one abstraction
- ✅ Built-in safety features and better error handling
- ✅ Optional agent-based reasoning with planning

---

## New Components

### 1. `llmsr/smolagents_models.py`
Unified model wrapper that supports:
- **Local models** via `TransformersModel` (no server required)
- **HuggingFace Inference API** via `InferenceClientModel`
- **OpenAI/Gemini/100+ APIs** via `LiteLLMModel`

### 2. `llmsr/smolagents_tools.py`
SmolAgents `@tool` decorated functions:
- `evaluate_equation_code`: Executes and scores generated equations
- `extract_function_body`: Cleans LLM output
- `validate_equation_syntax`: Syntax validation

### 3. `llmsr/smolagents_sampler.py`
Two sampler variants:
- `SmolAgentsSampler`: Drop-in replacement for original `Sampler`
- `SmolAgentsCodeAgentSampler`: Advanced agent with planning (experimental)

### 4. `llmsr/smolagents_pipeline.py`
Simplified pipeline that uses SmolAgents models while keeping:
- Original `ExperienceBuffer` (multi-island evolution)
- Original `Evaluator` and `LocalSandbox` (proven safe execution)

### 5. `main_smolagents.py`
New entry point demonstrating the SmolAgents workflow

---

## Installation

```bash
# Install SmolAgents with toolkit
pip install "smolagents[toolkit]>=1.0.0"

# Or update from requirements.txt
pip install -r requirements.txt
```

---

## Usage Examples

### Local Model (No Server Required!)

**Before:** You had to start `llm_engine/engine.py` in a separate process.

**Now:**
```bash
python main_smolagents.py \
  --problem_name oscillator1 \
  --spec_path specs/specification_oscillator1_numpy.txt \
  --log_path logs/oscillator1_smolagents \
  --local_model_id Qwen/Qwen2.5-Coder-32B-Instruct
```

The model loads directly in the same process using `TransformersModel`.

---

### OpenAI API

```bash
export OPENAI_API_KEY=sk-...

python main_smolagents.py \
  --problem_name oscillator1 \
  --spec_path specs/specification_oscillator1_numpy.txt \
  --log_path logs/oscillator1_openai \
  --use_api True \
  --api_model gpt-4
```

---

### Gemini API

```bash
export GEMINI_API_KEY=your_key

python main_smolagents.py \
  --problem_name oscillator1 \
  --spec_path specs/specification_oscillator1_numpy.txt \
  --log_path logs/oscillator1_gemini \
  --use_api True \
  --api_model gemini-2.5-flash-latest
```

---

### HuggingFace Inference API

```bash
export HF_TOKEN=hf_...

python main_smolagents.py \
  --problem_name oscillator1 \
  --spec_path specs/specification_oscillator1_numpy.txt \
  --log_path logs/oscillator1_hf \
  --use_api True \
  --api_model Qwen/Qwen2.5-Coder-32B-Instruct
```

---

## Key Benefits

### 🚀 Simplified Deployment
- **No separate server process** for local models
- **One interface** for all model types
- **Automatic device mapping** for GPU/CPU

### 🔒 Enhanced Safety
- SmolAgents provides battle-tested execution sandboxing
- Option to use Docker/Wasm executors (future enhancement)
- Better error handling and recovery

### 🧠 Advanced Features (Optional)
- **Planning mode**: Agent can break down complex tasks
- **Tool support**: Extensible with custom `@tool` functions
- **Streaming**: Built-in support for real-time output

### 📦 Code Reduction
- **~150 lines removed**: Deleted custom Flask server
- **~200 lines simplified**: Model/API handling unified
- **Better maintainability**: Leverage SmolAgents' active development

---

## Architecture Comparison

### Original Architecture
```
main.py → pipeline.main()
  ↓
Sampler → LocalLLM → HTTP → llm_engine/engine.py (Flask server)
                              ↓
                        Transformers.generate()
  ↓
Evaluator → LocalSandbox (multiprocessing)
  ↓
ExperienceBuffer (multi-island evolution)
```

### SmolAgents Architecture
```
main_smolagents.py → smolagents_pipeline.main()
  ↓
SmolAgentsSampler → UnifiedModel → SmolAgents Models
                                    ├─ TransformersModel (local, direct)
                                    ├─ InferenceClientModel (HF API)
                                    └─ LiteLLMModel (OpenAI/Gemini/etc)
  ↓
Evaluator → LocalSandbox (unchanged)
  ↓
ExperienceBuffer (unchanged)
```

**What's preserved:**
- ✅ Multi-island evolutionary algorithm (`ExperienceBuffer`)
- ✅ Safe code execution (`LocalSandbox` with multiprocessing timeout)
- ✅ Fitness evaluation and parameter optimization
- ✅ All specification templates (`specs/*.txt`)
- ✅ Logging and profiling infrastructure

**What's removed:**
- ❌ Custom Flask inference server
- ❌ Manual HTTP request handling
- ❌ Per-API custom code paths
- ❌ Model loading/management logic

---

## Configuration

The `Config` class remains compatible. SmolAgents uses:
- `use_api`: Switch between local and API models
- `api_model`: Model identifier (auto-routed to correct API)
- `api_type`: Optional override ("openai", "gemini", "auto")

New optional parameters in `main_smolagents.py`:
- `--local_model_id`: Specify local model (default: Qwen/Qwen2.5-Coder-32B-Instruct)
- `--use_planning`: Enable agent planning (experimental)

---

## Migration Checklist

If you're moving from the original architecture:

- [ ] Install `smolagents[toolkit]`
- [ ] Stop using `run_server.sh` / `llm_engine/engine.py`
- [ ] Update scripts to use `main_smolagents.py`
- [ ] Set appropriate environment variables (`OPENAI_API_KEY`, `GEMINI_API_KEY`, etc.)
- [ ] Test with a small dataset first (e.g., `oscillator1`)

---

## Backward Compatibility

The **original workflow still works**:
- `main.py` and `main_gemini.py` are unchanged
- `llm_engine/engine.py` still available for custom deployments
- All original modules (`sampler.py`, `evaluator.py`, etc.) remain intact

You can **run both side-by-side** and compare results.

---

## Future Enhancements

Potential next steps using SmolAgents:

1. **Remote Executors**: Replace `LocalSandbox` with `DockerExecutor` or `WasmExecutor` for stronger isolation
2. **Multi-Agent Islands**: Each island as a separate `CodeAgent` with coordinator
3. **Interactive UI**: Add `GradioUI` for real-time experiment monitoring
4. **Tool Ecosystem**: Add tools for symbolic math, dimensional analysis, etc.
5. **Memory/RAG**: Integrate SmolAgents memory systems for long-context experiments

---

## Performance Notes

### Model Loading
- **Original**: Flask server loads model once, serves multiple requests
- **SmolAgents**: Model loads once per `main_smolagents.py` run
- **Recommendation**: For production, use API models or keep long-running process

### Execution Speed
- Local models: ~equivalent (same underlying `transformers`)
- API models: Potentially faster (SmolAgents has optimized batching)

### Memory Usage
- Local models: Same GPU/RAM requirements
- API models: Minimal local memory

---

## Troubleshooting

### "Module smolagents not found"
```bash
pip install "smolagents[toolkit]>=1.0.0"
```

### API key errors
Make sure environment variables are set:
```bash
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=your_key
export HF_TOKEN=hf_...
```

### CUDA out of memory
Reduce model size or use quantization:
```python
# In smolagents_models.py, you can add quantization support
# Currently uses TransformersModel defaults
```

### Slow local inference
Consider:
- Using smaller model (e.g., `Qwen/Qwen2.5-Coder-7B-Instruct`)
- API endpoints for faster iteration
- Batch inference (already supported)

---

## Questions?

- Check SmolAgents docs: https://github.com/huggingface/smolagents
- Review examples in `main_smolagents.py`
- Compare with original `main.py` for equivalent configurations

---

## License

Same as original repository (Apache 2.0 from DeepMind, with SmolAgents components under HuggingFace license).

