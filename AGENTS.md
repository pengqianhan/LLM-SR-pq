# Repository Guidelines

## Project Structure & Module Organization
Core pipeline code lives in `llmsr/` (sampler, evaluator, config, pipeline). The Hugging Face inference server sits in `llm_engine/engine.py`. Datasets are organized under `data/<problem>/` with `train.csv` files, while prompt specifications live in `specs/*.txt`. Generated artefacts and metrics should go to `logs/` (create one subfolder per experiment). Use `run_llmsr.sh` and `run_server.sh` as references when adding new workflows or automation.

## Build, Test, and Development Commands
Create the environment with `conda create -n llmsr python=3.11.7` followed by `pip install -r requirements.txt`. Start a local model endpoint via `bash run_server.sh` or `python llm_engine/engine.py --model_path mistralai/Mixtral-8x7B-Instruct-v0.1 --gpu_ids 0 --port 8000 --quantization`. Run the search loop locally with `python main.py --problem_name oscillator1 --spec_path specs/specification_oscillator1_numpy.txt --log_path logs/oscillator1`. To exercise the Gemini flow, call `python main_gemini.py --use_api True --api_model gemini-pro` after exporting `API_KEY`.

## Coding Style & Naming Conventions
Write Python using PEP 8 defaults (4-space indent, `snake_case` for functions and variables, `PascalCase` for classes). Keep imports grouped stdlib/third-party/local as seen in `main.py`. Prefer explicit type hints for public functions and keep docstrings concise. When editing specification templates, leave the `@evaluate.run` and `@equation.evolve` decorations intact and align indentation with surrounding code.

## Testing Guidelines
There is no standalone test suite; treat end-to-end runs as validations. For a regression check, run `python main.py` against a small dataset (e.g., `oscillator1`) and inspect `logs/<run>/samples/*.json` alongside the `events.out.tfevents.*` files (viewable with `tensorboard --logdir logs`). When introducing new specs or optimizers, add the exact replay command to your PR description and stash exploratory notebooks or notes under `learningnotes/`.

## Commit & Pull Request Guidelines
Recent history favors imperative, descriptive commit subjects (e.g., `Add support for Google Gen AI`). Provide context in the body when touching multiple areas or changing defaults. Every PR should explain the experiment configuration, include reproduction commands, and link related issues. Attach diffs of key output logs or screenshots when the change affects generated artefacts. Ensure configuration files and sample scripts stay in sync with documented commands before requesting review.

## Security & Configuration Tips
Never hard-code API secrets; set `API_KEY` (or cloud equivalents) through environment variables or `.env` files excluded from version control. Review `llmsr/config.py` before changing defaults to avoid leaking internal endpoints. If you upload new datasets, anonymize filenames and values as needed and document provenance in `learningnotes/`.
