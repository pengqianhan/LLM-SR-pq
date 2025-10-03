# SmolAgents Integration - Complete Documentation Index

Welcome! This repository now supports a **simplified architecture using HuggingFace SmolAgents**. This index helps you navigate the documentation.

---

## 🚀 Quick Links

### For First-Time Users
👉 **Start Here**: [QUICKSTART_SMOLAGENTS.md](./QUICKSTART_SMOLAGENTS.md)  
5-minute setup guide with copy-paste commands

### For Migrating Users
👉 **Migration Guide**: [SMOLAGENTS_MIGRATION.md](./SMOLAGENTS_MIGRATION.md)  
Complete guide for moving from original architecture

### For Understanding the Changes
👉 **Architecture Comparison**: [ARCHITECTURE_COMPARISON.md](./ARCHITECTURE_COMPARISON.md)  
Visual diagrams showing before/after

👉 **Simplification Summary**: [SIMPLIFICATION_SUMMARY.md](./SIMPLIFICATION_SUMMARY.md)  
Metrics and code reduction details

### For Developers
👉 **Implementation Notes**: [IMPLEMENTATION_NOTES.md](./IMPLEMENTATION_NOTES.md)  
Technical design decisions and rationale

---

## 📚 Documentation Overview

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [QUICKSTART_SMOLAGENTS.md](./QUICKSTART_SMOLAGENTS.md) | Fast getting started | First time using SmolAgents version |
| [SMOLAGENTS_MIGRATION.md](./SMOLAGENTS_MIGRATION.md) | Complete migration guide | Planning to switch from original |
| [ARCHITECTURE_COMPARISON.md](./ARCHITECTURE_COMPARISON.md) | Visual architecture diagrams | Understanding design changes |
| [SIMPLIFICATION_SUMMARY.md](./SIMPLIFICATION_SUMMARY.md) | Code metrics and analysis | Evaluating benefits |
| [IMPLEMENTATION_NOTES.md](./IMPLEMENTATION_NOTES.md) | Technical details | Contributing or debugging |

---

## 🎯 Choose Your Path

### Path 1: Just Want to Run It (5 min)
1. Read [QUICKSTART_SMOLAGENTS.md](./QUICKSTART_SMOLAGENTS.md) (Section 1-2)
2. Run: `pip install "smolagents[toolkit]>=1.0.0"`
3. Run: `python main_smolagents.py --problem_name oscillator1 --spec_path specs/specification_oscillator1_numpy.txt`
4. Done! ✅

### Path 2: Understanding the Migration (15 min)
1. Skim [ARCHITECTURE_COMPARISON.md](./ARCHITECTURE_COMPARISON.md) (Visual Overview)
2. Read [SIMPLIFICATION_SUMMARY.md](./SIMPLIFICATION_SUMMARY.md) (Code Reduction)
3. Check [SMOLAGENTS_MIGRATION.md](./SMOLAGENTS_MIGRATION.md) (Benefits section)
4. Decide if you want to migrate

### Path 3: Deep Dive (1 hour)
1. Read [SMOLAGENTS_MIGRATION.md](./SMOLAGENTS_MIGRATION.md) (Full document)
2. Review [IMPLEMENTATION_NOTES.md](./IMPLEMENTATION_NOTES.md) (Design decisions)
3. Study [ARCHITECTURE_COMPARISON.md](./ARCHITECTURE_COMPARISON.md) (All sections)
4. Try examples from [QUICKSTART_SMOLAGENTS.md](./QUICKSTART_SMOLAGENTS.md)

### Path 4: Contributing/Debugging (2+ hours)
1. All of Path 3
2. Read source code:
   - `llmsr/smolagents_models.py`
   - `llmsr/smolagents_sampler.py`
   - `llmsr/smolagents_pipeline.py`
3. Study [IMPLEMENTATION_NOTES.md](./IMPLEMENTATION_NOTES.md) (Challenges section)

---

## 📂 Key Files

### New Entry Points
- `main_smolagents.py` - Main script (replaces `main.py` + server)
- `run_smolagents.sh` - Interactive runner script

### New Modules
- `llmsr/smolagents_models.py` - Unified model wrapper
- `llmsr/smolagents_sampler.py` - Simplified sampler
- `llmsr/smolagents_pipeline.py` - Pipeline orchestration
- `llmsr/smolagents_tools.py` - Tool definitions (optional)

### Unchanged (Still Works)
- `main.py` - Original entry point
- `main_gemini.py` - Gemini-specific entry
- `llmsr/pipeline.py` - Original pipeline
- `llmsr/sampler.py` - Original sampler
- `llmsr/evaluator.py` - Evaluator (used by both!)
- `llmsr/buffer.py` - Experience buffer (used by both!)

---

## 🔍 Quick Reference by Topic

### Installation
- **SmolAgents**: [QUICKSTART_SMOLAGENTS.md](./QUICKSTART_SMOLAGENTS.md#-5-minute-setup) (Section 1)
- **Original**: [README.md](./README.md#installation)

### Running Experiments
- **SmolAgents**: [QUICKSTART_SMOLAGENTS.md](./QUICKSTART_SMOLAGENTS.md#-command-cheat-sheet)
- **Original**: [README.md](./README.md#local-runs-open-source-llms)

### Architecture
- **Overview**: [ARCHITECTURE_COMPARISON.md](./ARCHITECTURE_COMPARISON.md#visual-overview)
- **Design Decisions**: [IMPLEMENTATION_NOTES.md](./IMPLEMENTATION_NOTES.md#architecture-design-decisions)

### Code Changes
- **Summary**: [SIMPLIFICATION_SUMMARY.md](./SIMPLIFICATION_SUMMARY.md#overview)
- **Line Counts**: [SIMPLIFICATION_SUMMARY.md](./SIMPLIFICATION_SUMMARY.md#complexity-reduction)

### Migration
- **Benefits**: [SMOLAGENTS_MIGRATION.md](./SMOLAGENTS_MIGRATION.md#key-benefits)
- **Checklist**: [SMOLAGENTS_MIGRATION.md](./SMOLAGENTS_MIGRATION.md#migration-checklist)

### Troubleshooting
- **Quick Fixes**: [QUICKSTART_SMOLAGENTS.md](./QUICKSTART_SMOLAGENTS.md#-troubleshooting)
- **Common Issues**: [SMOLAGENTS_MIGRATION.md](./SMOLAGENTS_MIGRATION.md#troubleshooting)

### API Support
- **Matrix**: [ARCHITECTURE_COMPARISON.md](./ARCHITECTURE_COMPARISON.md#api-support-matrix)
- **Examples**: [QUICKSTART_SMOLAGENTS.md](./QUICKSTART_SMOLAGENTS.md#api-models)

---

## 🆚 Which Version Should I Use?

### Use SmolAgents (`main_smolagents.py`) if:
- ✅ Starting a new project
- ✅ Want simpler deployment (1 command)
- ✅ Need multiple API providers (OpenAI, Gemini, Claude, etc.)
- ✅ Prefer cleaner code
- ✅ Don't want to manage a server

### Use Original (`main.py`) if:
- ✅ Already have working workflows
- ✅ Running many batch experiments (server stays loaded)
- ✅ Need maximum stability (more tested)
- ✅ Custom server modifications

### You Can Use Both!
The architectures are **fully compatible**. Try SmolAgents in parallel, compare results, migrate when ready.

---

## 📊 At a Glance

| Aspect | Original | SmolAgents | Docs |
|--------|----------|------------|------|
| Setup complexity | 2 steps | 1 step | [ARCHITECTURE_COMPARISON.md](./ARCHITECTURE_COMPARISON.md#deployment-comparison) |
| Code (infrastructure) | ~450 LOC | ~530 LOC | [SIMPLIFICATION_SUMMARY.md](./SIMPLIFICATION_SUMMARY.md#net-impact) |
| Processes | 2 | 1 | [ARCHITECTURE_COMPARISON.md](./ARCHITECTURE_COMPARISON.md#visual-overview) |
| API support | 3 | 100+ | [ARCHITECTURE_COMPARISON.md](./ARCHITECTURE_COMPARISON.md#api-support-matrix) |
| Core algorithm | ✓ | ✓ Same | [SIMPLIFICATION_SUMMARY.md](./SIMPLIFICATION_SUMMARY.md#preserved-strengths) |

---

## 🎓 Learning Path

### Beginner
1. [QUICKSTART_SMOLAGENTS.md](./QUICKSTART_SMOLAGENTS.md) - Sections 1-3
2. Run one example
3. Check logs with TensorBoard

### Intermediate
1. [SMOLAGENTS_MIGRATION.md](./SMOLAGENTS_MIGRATION.md) - Overview + Benefits
2. [ARCHITECTURE_COMPARISON.md](./ARCHITECTURE_COMPARISON.md) - Visual Overview
3. Try both local and API models

### Advanced
1. All of Intermediate
2. [IMPLEMENTATION_NOTES.md](./IMPLEMENTATION_NOTES.md) - Full document
3. Review source code
4. Experiment with tools, planning mode

---

## 🔗 External Resources

- **SmolAgents GitHub**: https://github.com/huggingface/smolagents
- **SmolAgents Docs**: (linked in GitHub repo)
- **Original LLM-SR Paper**: https://arxiv.org/abs/2404.18400
- **HuggingFace Models**: https://huggingface.co/models

---

## 💡 Tips

### First Time Running?
👉 Use `run_smolagents.sh` - it's interactive and guides you through options

### Comparing Performance?
👉 Run same problem with both `main.py` and `main_smolagents.py`, compare logs

### Debugging?
👉 Start with `--max_samples 10` to fail fast

### Production?
👉 Use API models (OpenAI/Gemini) for faster iteration, local models for cost savings

---

## 📧 Getting Help

1. **Quick questions**: Check [QUICKSTART_SMOLAGENTS.md](./QUICKSTART_SMOLAGENTS.md#-troubleshooting)
2. **Migration issues**: See [SMOLAGENTS_MIGRATION.md](./SMOLAGENTS_MIGRATION.md#troubleshooting)
3. **Technical details**: Review [IMPLEMENTATION_NOTES.md](./IMPLEMENTATION_NOTES.md#known-limitations)
4. **Still stuck**: Open GitHub issue with:
   - Command you ran
   - Error message
   - Relevant section from logs

---

## 📝 Summary

**What you need to know:**
- SmolAgents = simpler deployment, same science
- All original code still works
- 5 new modules, 5 new docs
- 1 command instead of 2 processes
- 100+ AI models supported

**Where to start:**
- New user? → [QUICKSTART_SMOLAGENTS.md](./QUICKSTART_SMOLAGENTS.md)
- Migrating? → [SMOLAGENTS_MIGRATION.md](./SMOLAGENTS_MIGRATION.md)
- Curious? → [ARCHITECTURE_COMPARISON.md](./ARCHITECTURE_COMPARISON.md)

---

**Happy equation discovering! 🧮✨**

*Last updated: October 2025*

