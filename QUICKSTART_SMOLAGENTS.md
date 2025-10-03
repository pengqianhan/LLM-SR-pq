# SmolAgents Quick Start Guide

## 🚀 5-Minute Setup

### 1. Install Dependencies
```bash
pip install "smolagents[toolkit]>=1.0.0"
```

### 2. Run Your First Experiment

**Local Model (No Server Needed!):**
```bash
python main_smolagents.py \
  --problem_name oscillator1 \
  --spec_path specs/specification_oscillator1_numpy.txt \
  --log_path logs/oscillator1_smolagents \
  --max_samples 100
```

**OR use the interactive script:**
```bash
bash run_smolagents.sh
```

---

## 📋 Command Cheat Sheet

### Local Models
```bash
# Default (Qwen 32B)
python main_smolagents.py --problem_name oscillator1 --spec_path specs/specification_oscillator1_numpy.txt

# Smaller model (7B - faster)
python main_smolagents.py --problem_name oscillator1 --spec_path specs/specification_oscillator1_numpy.txt \
  --local_model_id Qwen/Qwen2.5-Coder-7B-Instruct

# Custom model
python main_smolagents.py --problem_name oscillator1 --spec_path specs/specification_oscillator1_numpy.txt \
  --local_model_id meta-llama/Llama-3.2-3B-Instruct
```

### API Models

**OpenAI:**
```bash
export OPENAI_API_KEY=sk-...
python main_smolagents.py --use_api True --api_model gpt-3.5-turbo --problem_name oscillator1 --spec_path specs/specification_oscillator1_numpy.txt
```

**Gemini:**
```bash
export GEMINI_API_KEY=your_key
python main_smolagents.py --use_api True --api_model gemini-2.5-flash-latest --problem_name oscillator1 --spec_path specs/specification_oscillator1_numpy.txt
```

**HuggingFace Inference API:**
```bash
export HF_TOKEN=hf_...
python main_smolagents.py --use_api True --api_model Qwen/Qwen2.5-Coder-32B-Instruct --problem_name oscillator1 --spec_path specs/specification_oscillator1_numpy.txt
```

---

## 🔧 Common Options

| Flag | Default | Description |
|------|---------|-------------|
| `--problem_name` | oscillator1 | Dataset name in `data/` |
| `--spec_path` | (required) | Specification template path |
| `--log_path` | logs/smolagents_run | TensorBoard log directory |
| `--max_samples` | 10000 | Maximum equations to generate |
| `--samples_per_prompt` | 4 | Equations per iteration |
| `--use_api` | False | Use API instead of local model |
| `--api_model` | gpt-3.5-turbo | API model identifier |
| `--local_model_id` | Qwen/Qwen2.5-Coder-32B-Instruct | Local model ID |

---

## 📊 Available Problems

| Problem | Dataset | Spec File |
|---------|---------|-----------|
| oscillator1 | data/oscillator1/train.csv | specs/specification_oscillator1_numpy.txt |
| oscillator2 | data/oscillator2/train.csv | specs/specification_oscillator2_numpy.txt |
| bactgrow | data/bactgrow/train.csv | specs/specification_bactgrow_numpy.txt |
| stressstrain | data/stressstrain/train.csv | specs/specification_stressstrain_numpy.txt |

---

## 🎯 Quick Examples

### Test Run (100 samples, ~5 min)
```bash
python main_smolagents.py \
  --problem_name oscillator1 \
  --spec_path specs/specification_oscillator1_numpy.txt \
  --max_samples 100
```

### Full Experiment (10K samples)
```bash
python main_smolagents.py \
  --problem_name oscillator2 \
  --spec_path specs/specification_oscillator2_numpy.txt \
  --max_samples 10000 \
  --log_path logs/oscillator2_full
```

### API-Based (Fast Iteration)
```bash
export OPENAI_API_KEY=sk-...
python main_smolagents.py \
  --use_api True \
  --api_model gpt-4 \
  --problem_name stressstrain \
  --spec_path specs/specification_stressstrain_numpy.txt \
  --max_samples 500
```

---

## 📈 View Results

```bash
# Start TensorBoard
tensorboard --logdir logs/oscillator1_smolagents

# Or browse files directly
ls logs/oscillator1_smolagents/samples/
cat logs/oscillator1_smolagents/best_program.json
```

---

## 🆚 Original vs SmolAgents

| Aspect | Original (`main.py`) | SmolAgents (`main_smolagents.py`) |
|--------|---------------------|-----------------------------------|
| Setup | Start server → Run experiment | Single command |
| Processes | 2 (server + main) | 1 |
| Local models | Via HTTP server | Direct loading |
| API support | OpenAI, Gemini | OpenAI, Gemini, HF, Claude, 100+ |
| Configuration | Port management | Automatic |
| Code complexity | Higher | Lower |

**Both preserve:**
- ✅ Multi-island evolutionary algorithm
- ✅ Safe code execution with timeout
- ✅ Parameter optimization
- ✅ All specification templates
- ✅ TensorBoard logging

---

## 🐛 Troubleshooting

### "Module smolagents not found"
```bash
pip install "smolagents[toolkit]>=1.0.0"
```

### CUDA out of memory
Try a smaller model:
```bash
--local_model_id Qwen/Qwen2.5-Coder-7B-Instruct
```

### API key errors
Check environment variables:
```bash
echo $OPENAI_API_KEY
echo $GEMINI_API_KEY
```

### Slow inference
- Use API models for faster iteration
- Reduce `--max_samples` for testing
- Use smaller local models

---

## 📚 Learn More

- **Full migration guide**: [SMOLAGENTS_MIGRATION.md](./SMOLAGENTS_MIGRATION.md)
- **Code simplification**: [SIMPLIFICATION_SUMMARY.md](./SIMPLIFICATION_SUMMARY.md)
- **SmolAgents docs**: https://github.com/huggingface/smolagents
- **Original paper**: https://arxiv.org/abs/2404.18400

---

## ✨ What's Next?

After your first successful run:
1. Try different problems (`oscillator2`, `bactgrow`, etc.)
2. Compare local vs API models
3. Experiment with `--samples_per_prompt` and `--max_samples`
4. Check out advanced features in [SMOLAGENTS_MIGRATION.md](./SMOLAGENTS_MIGRATION.md)

---

**Happy equation discovering! 🧮✨**

