# LLM-SR Code Execution Flow Analysis

Starting from `main_gemini.py`

## Overview

The LLM-SR (Large Language Model Symbolic Regression) system is a scientific equation discovery framework that combines LLM code generation capabilities with evolutionary search algorithms. This document provides a detailed analysis of the code execution flow starting from `main_gemini.py`.

## 1. Entry Point: `main_gemini.py`

### 1.1 Environment Setup
```python
# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError/Exception:
    # Continue without dotenv if not available
```

**Purpose**: Loads API keys and configuration from `.env` file, particularly for Gemini API access.

### 1.2 Argument Parsing
```python
parser = ArgumentParser()
parser.add_argument('--use_api', type=bool, default=True)  # API mode enabled by default
parser.add_argument('--api_type', type=str, default="gemini", choices=['openai', 'gemini', 'auto'])
parser.add_argument('--api_model', type=str, default="models/gemini-2.5-flash-lite")
parser.add_argument('--spec_path', type=str, default="./specs/specification_oscillator1_numpy.txt")
parser.add_argument('--problem_name', type=str, default="oscillator1")
```

**Key Differences from `main.py`**:
- Default `use_api=True` (vs False in main.py)
- Default `api_type="gemini"` (specific to Gemini)
- Default model is Gemini Flash Lite

### 1.3 Configuration Setup
```python
class_config = config.ClassConfig(
    llm_class=sampler.LocalLLM,           # LLM sampling class
    sandbox_class=evaluator.LocalSandbox  # Code execution sandbox
)

config = config.Config(
    use_api=args.use_api,
    api_type=args.api_type,    # New: specifies API type
    api_model=args.api_model,
)
```

### 1.4 Data Loading
```python
# Load training dataset
df = pd.read_csv('./data/' + problem_name + '/train.csv')
data = np.array(df)
X = data[:, :-1]  # Input features
y = data[:, -1]   # Target outputs

# Convert to torch tensors if torch specification
if 'torch' in args.spec_path:
    X = torch.Tensor(X)
    y = torch.Tensor(y)

dataset = {'data': {'inputs': X, 'outputs': y}}
```

### 1.5 Specification Loading
```python
with open(args.spec_path, encoding="utf-8") as f:
    specification = f.read()
```

**Specification Template Structure**:
- Contains problem-specific code template
- Must have `@evaluate.run` decorator (evaluation function)
- Must have `@equation.evolve` decorator (function to be evolved)

## 2. Pipeline Execution: `pipeline.main()`

### 2.1 Function Extraction
```python
def _extract_function_names(specification: str) -> Tuple[str, str]:
    run_functions = list(code_manipulation.yield_decorated(specification, 'evaluate', 'run'))
    evolve_functions = list(code_manipulation.yield_decorated(specification, 'equation', 'evolve'))
    
    # Validates exactly one function with each decorator
    return evolve_functions[0], run_functions[0]
```

**Purpose**: Identifies which functions to evolve and which to use for evaluation.

### 2.2 Experience Buffer Initialization
```python
template = code_manipulation.text_to_program(specification)
database = buffer.ExperienceBuffer(config.experience_buffer, template, function_to_evolve)
```

**ExperienceBuffer Features**:
- Multi-island evolutionary algorithm
- Maintains population diversity
- Temperature-based sampling
- Periodic island resets

### 2.3 Evaluator Setup
```python
evaluators = []
for _ in range(config.num_evaluators):
    evaluators.append(evaluator.Evaluator(
        database,
        template,
        function_to_evolve,
        function_to_run,
        inputs,
        timeout_seconds=config.evaluate_timeout_seconds,
        sandbox_class=class_config.sandbox_class
    ))
```

**Evaluator Responsibilities**:
- Execute generated equation code
- Compute fitness scores
- Handle code safety (sandboxed execution)
- Parameter optimization (BFGS/Adam)

### 2.4 Initial Evaluation
```python
initial = template.get_function(function_to_evolve).body
evaluators[0].analyse(initial, island_id=None, version_generated=None, profiler=profiler)
```

**Purpose**: Evaluates the initial template function to establish baseline performance.

### 2.5 Sampler Initialization and Execution
```python
samplers = [sampler.Sampler(database, evaluators, 
                           config.samples_per_prompt, 
                           max_sample_nums=max_sample_nums, 
                           llm_class=class_config.llm_class,
                           config=config) 
                           for _ in range(config.num_samplers)]

# Main execution loop
for s in samplers:
    s.sample(profiler=profiler)
```

## 3. Sampling Process: `sampler.Sampler.sample()`

### 3.1 Main Sampling Loop
```python
def sample(self, **kwargs):
    while True:
        # Stop condition check
        if self._max_sample_nums and self.__class__._global_samples_nums >= self._max_sample_nums:
            break
        
        # Get prompt from experience buffer
        prompt = self._database.get_prompt()
        
        # Generate samples using LLM
        reset_time = time.time()
        samples = self._llm.draw_samples(prompt.code, self.config)
        sample_time = (time.time() - reset_time) / self._samples_per_prompt
        
        # Distribute samples to evaluators
        for sample in samples:
            self._global_sample_nums_plus_one()
            chosen_evaluator = np.random.choice(self._evaluators)
            chosen_evaluator.analyse(sample, prompt.island_id, prompt.version_generated, ...)
```

### 3.2 LLM Integration: `LocalLLM.draw_samples()`

#### API Type Determination
```python
def _determine_api_type(self, config: config_lib.Config) -> str:
    # Check explicit api_type
    if hasattr(config, 'api_type') and config.api_type and config.api_type != 'auto':
        return config.api_type.lower()
    
    # Auto-detect from model name
    if config.api_model:
        model_name = config.api_model.lower()
        if 'gemini' in model_name:
            return 'gemini'
        elif any(openai_model in model_name for openai_model in ['gpt', 'chatgpt', ...]):
            return 'openai'
    
    return 'openai'  # Default
```

#### Gemini API Integration
```python
def _draw_samples_api_gemini(self, prompt: str, config: config_lib.Config) -> Collection[str]:
    # Import Google Gen AI SDK
    from google import genai
    from google.genai import types
    
    # API key configuration
    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('API_KEY')
    client = genai.Client(api_key=api_key)
    
    # Generate samples with retry logic
    for i in range(self._samples_per_prompt):
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=512,
                        temperature=0.8,
                        top_p=0.9,
                        top_k=40,
                    )
                )
                
                if response.text:
                    response_text = _extract_body(response.text, config)
                    all_samples.append(response_text)
                    break
            except Exception:
                retry_count += 1
                time.sleep(1)  # Retry delay
```

**Key Features**:
- Robust error handling and retry mechanism
- Configurable generation parameters
- Response text extraction and cleaning

#### Code Extraction: `_extract_body()`
```python
def _extract_body(sample: str, config: config_lib.Config) -> str:
    lines = sample.splitlines()
    
    # Find function definition
    for lineno, line in enumerate(lines):
        if line[:3] == 'def':
            func_body_lineno = lineno
            break
    
    # Extract function body based on API type
    if config.use_api:
        # For API responses - clean extraction
        code = '\n'.join(lines[func_body_lineno + 1:])
    else:
        # For local LLM - ensure proper indentation
        code = ''
        indent = '    '
        for line in lines[func_body_lineno + 1:]:
            if line[:4] != indent:
                line = indent + line
            code += line + '\n'
    
    return code
```

## 4. Evaluation Process: `evaluator.Evaluator.analyse()`

### 4.1 Code Integration and Execution
1. **Program Assembly**: Combines the generated function body with the template
2. **Safety Checks**: Validates code structure and safety
3. **Sandbox Execution**: Runs code in isolated environment
4. **Parameter Optimization**: Uses BFGS or Adam optimizer to fit parameters
5. **Fitness Calculation**: Computes MSE or other loss metrics

### 4.2 Experience Buffer Update
1. **Score Assignment**: Assigns fitness score to the generated function
2. **Population Management**: Updates island populations
3. **Selection Pressure**: Maintains best candidates
4. **Diversity Control**: Manages population diversity through island model

## 5. Key Architectural Components

### 5.1 Multi-Island Evolution
- **Islands**: Independent populations with different characteristics
- **Migration**: Periodic exchange of best candidates between islands
- **Reset Mechanism**: Weak islands are periodically reset
- **Temperature Sampling**: Controls exploration vs exploitation

### 5.2 LLM Integration Layers
```
User Request → main_gemini.py → Pipeline → Sampler → LocalLLM → API (Gemini/OpenAI/Local)
                                    ↓
Experience Buffer ← Evaluator ← Generated Code Samples
```

### 5.3 Configuration Hierarchy
```
main_gemini.py args → Config dataclass → Component-specific configs
                                     ↓
                           ExperienceBufferConfig, ClassConfig
```

## 6. Data Flow Summary

1. **Initialization**: Load specification template and dataset
2. **Template Parsing**: Extract evaluation and evolution functions
3. **Buffer Setup**: Initialize multi-island experience buffer
4. **Initial Evaluation**: Baseline performance measurement
5. **Sampling Loop**:
   - Get prompt from experience buffer
   - Generate code samples via LLM (Gemini API)
   - Extract and clean function bodies
   - Distribute to evaluators
6. **Evaluation Loop**:
   - Execute generated code safely
   - Optimize parameters
   - Compute fitness scores
   - Update experience buffer
7. **Evolution**: Buffer manages populations and generates new prompts
8. **Termination**: Stop when max samples reached or convergence

## 7. Key Differences from Standard Implementation

### 7.1 Gemini-Specific Features
- **API Integration**: Native Google Gemini API support
- **Error Handling**: Robust retry mechanisms for API calls
- **Model Configuration**: Optimized parameters for Gemini models
- **Response Processing**: Gemini-specific text extraction

### 7.2 Enhanced Configuration
- **API Type Detection**: Automatic model type recognition
- **Flexible Backends**: Support for multiple LLM providers
- **Environment Integration**: Seamless `.env` file support

### 7.3 Production Readiness
- **Error Recovery**: Comprehensive exception handling
- **Logging**: Detailed operation tracking
- **Resource Management**: Efficient API usage and rate limiting

This execution flow demonstrates how LLM-SR combines evolutionary algorithms with modern LLM capabilities to discover mathematical equations from data, with `main_gemini.py` specifically optimized for Google's Gemini API integration.