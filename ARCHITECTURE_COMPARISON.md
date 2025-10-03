# Architecture Comparison: Original vs SmolAgents

## Visual Overview

### Original Architecture (main.py)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Terminal 1: LLM Server                      │
│                                                                   │
│  bash run_server.sh                                              │
│    ↓                                                              │
│  llm_engine/engine.py (Flask)                                    │
│    ├─ Load model from HuggingFace                                │
│    ├─ GPU management                                             │
│    ├─ Quantization setup                                         │
│    └─ Serve on http://localhost:5000/completions                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Terminal 2: Main Process                      │
│                                                                   │
│  python main.py --problem_name oscillator1 ...                  │
│    ↓                                                              │
│  pipeline.main()                                                 │
│    ├─ Parse specification (@evaluate.run, @equation.evolve)     │
│    ├─ Create ExperienceBuffer (multi-island)                    │
│    ├─ Create Evaluators (LocalSandbox)                          │
│    └─ Create Samplers                                            │
│         ↓                                                         │
│       Sampler.sample() ←─────────────────────┐                  │
│         ├─ Get prompt from ExperienceBuffer  │                  │
│         ├─ LocalLLM.draw_samples()           │                  │
│         │   ├─ Build HTTP request            │                  │
│         │   └─ POST to localhost:5000 ───────┘ (HTTP)           │
│         ├─ Extract function body              │                  │
│         └─ Send to Evaluator                  │                  │
│              ↓                                  │                  │
│            Evaluator.analyse()                 │                  │
│              ├─ Compile code                   │                  │
│              ├─ LocalSandbox.run()             │                  │
│              │   ├─ Fork process (multiprocess)│                  │
│              │   ├─ Execute with timeout       │                  │
│              │   └─ Optimize params (scipy)    │                  │
│              └─ Register in ExperienceBuffer   │                  │
│                    ↓                            │                  │
│                  Multi-island evolution        │                  │
│                  (cluster sampling, reset)     │                  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

Dependencies:
  - Flask server (144 LOC)
  - HTTP client code (~100 LOC)
  - Per-API custom logic (~100 LOC)
  - Port management
```

---

### SmolAgents Architecture (main_smolagents.py)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Single Terminal Process                     │
│                                                                   │
│  python main_smolagents.py --problem_name oscillator1 ...       │
│    ↓                                                              │
│  smolagents_pipeline.main()                                     │
│    ├─ Parse specification (@evaluate.run, @equation.evolve)     │
│    ├─ Create ExperienceBuffer (multi-island) ✓ UNCHANGED       │
│    ├─ Create Evaluators (LocalSandbox) ✓ UNCHANGED             │
│    ├─ Create UnifiedModel                                        │
│    │   └─ if use_api:                                            │
│    │       ├─ InferenceClientModel (HF API)                      │
│    │       ├─ LiteLLMModel (OpenAI/Gemini/Claude/100+)          │
│    │       └─ Auto-detect from model name                        │
│    │   └─ else:                                                  │
│    │       └─ TransformersModel (local, direct load)            │
│    └─ Create SmolAgentsSampler                                  │
│         ↓                                                         │
│       SmolAgentsSampler.sample() ←──────────┐                   │
│         ├─ Get prompt from ExperienceBuffer │                   │
│         ├─ UnifiedModel.generate()          │                   │
│         │   ├─ Format as chat messages      │                   │
│         │   └─ Call SmolAgents model        │ (Direct/API)      │
│         │       ├─ Local: transformers lib  │                   │
│         │       └─ API: SmolAgents client   │                   │
│         ├─ Extract function body            │                   │
│         └─ Send to Evaluator                │                   │
│              ↓                                │                   │
│            Evaluator.analyse() ✓ UNCHANGED  │                   │
│              ├─ Compile code                 │                   │
│              ├─ LocalSandbox.run()           │                   │
│              │   ├─ Fork process             │                   │
│              │   ├─ Execute with timeout     │                   │
│              │   └─ Optimize params          │                   │
│              └─ Register in ExperienceBuffer │                   │
│                    ↓                          │                   │
│                  Multi-island evolution ✓ UNCHANGED             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

Dependencies:
  - SmolAgents (handles all model access)
  - No server needed
  - No HTTP client code
  - Automatic API routing
```

---

## Component Comparison

### Model Access Layer

| Original | SmolAgents |
|----------|------------|
| **Flask Server** | **No Server** |
| `llm_engine/engine.py` | `smolagents_models.py` |
| - Load model manually | - SmolAgents handles loading |
| - Manage GPU placement | - Auto device_map |
| - HTTP endpoint | - Direct function call |
| - 144 lines | - 130 lines (wrapper only) |

### LLM Client

| Original | SmolAgents |
|----------|------------|
| **LocalLLM** | **UnifiedModel** |
| `sampler.py` (483 LOC) | `smolagents_models.py` (130 LOC) |
| - HTTP POST requests | - Direct method calls |
| - Manual retry logic | - SmolAgents built-in |
| - Per-API if/else | - Auto-routing |
| - Custom error handling | - Standard exceptions |

### Sampler

| Original | SmolAgents |
|----------|------------|
| **Sampler** | **SmolAgentsSampler** |
| `sampler.py` | `smolagents_sampler.py` |
| - 483 lines (all features) | - 280 lines (simplified) |
| - HTTP request logic | - Direct model calls |
| - API detection | - Handled by UnifiedModel |
| - Extract body | - Same logic preserved |

### Evaluator

| Original | SmolAgents |
|----------|------------|
| **Evaluator** | **Evaluator** |
| `evaluator.py` | `evaluator.py` |
| - 297 lines | - ✓ UNCHANGED |
| - LocalSandbox | - ✓ UNCHANGED |
| - Multiprocessing timeout | - ✓ UNCHANGED |
| - Parameter optimization | - ✓ UNCHANGED |

### Experience Buffer

| Original | SmolAgents |
|----------|------------|
| **ExperienceBuffer** | **ExperienceBuffer** |
| `buffer.py` | `buffer.py` |
| - 327 lines | - ✓ UNCHANGED |
| - Multi-island evolution | - ✓ UNCHANGED |
| - Cluster sampling | - ✓ UNCHANGED |
| - Temperature annealing | - ✓ UNCHANGED |

---

## Data Flow Comparison

### Original Flow

```
User starts server
   ↓
Server loads model (30-60s)
   ↓
User runs main.py
   ↓
Sampler gets prompt from Buffer
   ↓
Sampler sends HTTP POST to server
   ↓
Server generates text
   ↓
Server returns JSON response
   ↓
Sampler extracts function body
   ↓
Evaluator executes and scores
   ↓
Buffer stores result
   ↓
Loop (get prompt → sample → evaluate)
```

### SmolAgents Flow

```
User runs main_smolagents.py
   ↓
UnifiedModel loads (if local) (30-60s)
   ↓
Sampler gets prompt from Buffer
   ↓
Sampler calls model.generate()
   ↓
SmolAgents model generates text
   ↓
Sampler extracts function body
   ↓
Evaluator executes and scores ✓ SAME
   ↓
Buffer stores result ✓ SAME
   ↓
Loop (get prompt → sample → evaluate)
```

---

## API Support Matrix

### Original

| Provider | Support | How |
|----------|---------|-----|
| Local models | ✅ | Via Flask server |
| OpenAI | ✅ | Manual HTTP client |
| Gemini | ✅ | Google SDK |
| HF Inference | ❌ | Not implemented |
| Claude | ❌ | Not implemented |
| Others | ❌ | Would need custom code |

### SmolAgents

| Provider | Support | How |
|----------|---------|-----|
| Local models | ✅ | TransformersModel (direct) |
| OpenAI | ✅ | LiteLLMModel |
| Gemini | ✅ | LiteLLMModel |
| HF Inference | ✅ | InferenceClientModel |
| Claude | ✅ | LiteLLMModel |
| Azure OpenAI | ✅ | LiteLLMModel |
| Bedrock | ✅ | LiteLLMModel |
| 100+ others | ✅ | LiteLLMModel |

---

## File Structure Comparison

### Original Files
```
llm_engine/
  └─ engine.py (144 LOC) ← Flask server

llmsr/
  ├─ pipeline.py (104 LOC)
  ├─ sampler.py (483 LOC) ← Includes HTTP client
  ├─ evaluator.py (297 LOC)
  ├─ buffer.py (327 LOC)
  ├─ config.py (74 LOC)
  └─ code_manipulation.py (277 LOC)

main.py (62 LOC)
main_gemini.py (79 LOC)
run_server.sh
run_llmsr.sh
```

### SmolAgents Files
```
llm_engine/
  └─ engine.py (144 LOC) ← Still available, not used

llmsr/
  ├─ pipeline.py (104 LOC) ✓ PRESERVED
  ├─ sampler.py (483 LOC) ✓ PRESERVED
  ├─ evaluator.py (297 LOC) ✓ PRESERVED
  ├─ buffer.py (327 LOC) ✓ PRESERVED
  ├─ config.py (74 LOC) ✓ PRESERVED
  ├─ code_manipulation.py (277 LOC) ✓ PRESERVED
  ├─ smolagents_models.py (130 LOC) ← NEW
  ├─ smolagents_tools.py (170 LOC) ← NEW
  ├─ smolagents_sampler.py (280 LOC) ← NEW
  └─ smolagents_pipeline.py (120 LOC) ← NEW

main.py (62 LOC) ✓ PRESERVED
main_gemini.py (79 LOC) ✓ PRESERVED
main_smolagents.py (120 LOC) ← NEW
run_server.sh ✓ PRESERVED
run_llmsr.sh ✓ PRESERVED
run_smolagents.sh (130 LOC) ← NEW
```

---

## Deployment Comparison

### Original Deployment

**Development:**
```bash
# Terminal 1
bash run_server.sh
# Wait for "Running on http://127.0.0.1:5000"

# Terminal 2
python main.py --problem_name oscillator1 ...
```

**Production:**
- Keep server running as daemon
- Run experiments against server
- Monitor server logs separately
- Restart server if OOM

### SmolAgents Deployment

**Development:**
```bash
# Single terminal
python main_smolagents.py --problem_name oscillator1 ...
```

**Production:**
- No daemon needed
- Each experiment is self-contained
- Or: Use API models (no local deployment)

---

## Resource Usage

### Memory (GPU)

| Scenario | Original | SmolAgents | Winner |
|----------|----------|------------|--------|
| Single experiment | Server holds model | Process holds model | Tie |
| Multiple experiments | Server reused | Each loads model | Original |
| API-based | No GPU | No GPU | Tie |

**Recommendation**: Local = Original for batch; SmolAgents for single runs or APIs

### CPU/Network

| Scenario | Original | SmolAgents | Winner |
|----------|----------|------------|--------|
| HTTP overhead | Yes (localhost) | No | SmolAgents |
| JSON parsing | Yes | No | SmolAgents |
| Network reliability | Dependent | N/A | SmolAgents |

---

## Error Handling

### Original
```python
try:
    response = requests.post(url, ...)
    if response.status_code == 200:
        return response.json()["content"]
except Exception:
    continue  # Retry
```

### SmolAgents
```python
try:
    response = self.model(messages)
    return response
except Exception as e:
    print(f"Generation error: {e}")
    return ""
```

**Benefit**: SmolAgents handles retries, rate limiting, etc. internally

---

## Configuration

### Original (`main.py`)
```python
parser.add_argument('--port', type=int)
parser.add_argument('--use_api', type=bool)
parser.add_argument('--api_model', type=str)
# Model path in run_server.sh
```

### SmolAgents (`main_smolagents.py`)
```python
parser.add_argument('--use_api', type=bool)
parser.add_argument('--api_model', type=str)
parser.add_argument('--local_model_id', type=str)
# No port needed!
```

---

## Summary

### What Changed
- ✅ **No Flask server** (144 LOC removed)
- ✅ **No HTTP client** (~100 LOC removed)
- ✅ **Unified model interface** (simpler code)
- ✅ **Broader API support** (3 → 100+ providers)

### What Stayed the Same
- ✅ **Multi-island evolution** (core algorithm)
- ✅ **Safe execution** (LocalSandbox)
- ✅ **Parameter optimization** (scipy/torch)
- ✅ **Specification templates** (all specs work)
- ✅ **Logging/profiling** (TensorBoard)

### Bottom Line
- **Simpler deployment**: 2 processes → 1
- **Cleaner code**: ~350 LOC infrastructure removed
- **More flexible**: 100+ model providers vs 3
- **Same science**: Core algorithms unchanged

**Recommended for**: New projects, API-based workflows, simpler deployments  
**Original still good for**: Batch experiments with local models, established workflows

