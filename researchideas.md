// Research Plan v2: Multimodal LLM → Hybrid Automata (HA)

## 1) Objectives (Refined)
- Build a reproducible agent that converts CSV trajectories + PNG plots in `LLM_HA_bench/automata_Dataset` into valid HA JSON (Dainarx schema) and benchmarks against ground truth in `LLM_HA_bench/automata`.
- Use `pre_works/LLM-SR_code` as the main orchestration/search framework (samplers + islands) and integrate `pre_works/Dainarx_code` for HA definition, simulation, and evaluation.
- Provide an iterative error-driven loop: generate → simulate → diagnose → refine, with PNG-only initial seeding and image-based comparative refinement.
- The PNG is used to guide the generation of the JSON file, and the CSV is used to guide the refinement of the JSON file.

## 2) Grounding in Codebases
- Dainarx (pre_works/Dainarx_code)
  - JSON schema: `automaton.var`, `automaton.mode[].eq` (difference/NARX-style equations like `x[2] = …`), `automaton.edge[]` with `direction`, `condition` (Python expr over state symbols), optional `reset`. See examples such as `pre_works/Dainarx_code/automata/non_linear/duffing.json`.
  - Built-in pipeline (change-points → slicing → clustering → SVM guards → assembly → evaluation) is used here strictly for simulation/evaluation of LLM-generated JSON, not for learning the JSON itself.
  - Programmatic entrypoints already exist: `run(data_list, input_data, config, evaluation)` and utilities in `src/` allow batch evaluation without shelling out.
- LLM-SR (pre_works/LLM-SR_code)
  - Provides a robust LLM sampling and evaluation loop with templates, buffers, and guardrails (see `llmsr/`).
  - Gemini multimodal API supported via `main_gemini.py` and `llmsr/sampler.LocalLLM` (auto-detects `api_type` from `api_model`).
  - We will borrow (a) the prompt-template discipline and (b) iterative sampling/evaluation concepts to drive JSON generation and refinement (not necessarily reuse the exact decorator-based evaluator).
  - Importantly, we adopt the island model via `llmsr/buffer.ExperienceBuffer` to manage diverse JSON hypotheses across multiple islands with periodic resets and temperature-controlled sampling.
  - For image-driven JSON, adapt `pre_works/Dainarx_code/prompts/image2ha.md` to enforce Dainarx-compatible outputs.

Key alignment details:
- Dainarx expects discrete-time NARX equations and guard conditions bound to variables listed in `automaton.var` (it compiles `lambda <vars>: <condition>`). LLM prompts must produce consistent variable names and indices.
- During simulation, always reset with only the initial state and the first `order` input samples from CSV: `sys.reset(init_state, input_list[:, :config['order']])`.

## 3) Data & Splits
- Per task family (`linear`, `non_linear`, `ATVA`, `FaMoS`):
  - Multimodal extraction (training signal): feed ONLY `sample_0.csv` columns `time` + variable columns (`[x1,x2,...]`) + input columns (`[u1,u2,...]`) and the corresponding `sample_0.png` to the multimodal LLM to extract the HA JSON. Do NOT expose `mode` or `mode_switch` to the LLM.
  - Evaluation: assess the single JSON extracted from `sample_0` on all other samples `sample_1,sample_2,...,sample_n` in the same task using Dainarx metrics (`mean_diff`, `max_diff`, `tc`, `clustering_error`).
- CSV schema assumptions: `time,[x1,x2...],[u1,u2...],mode,mode_switch`. Before prompting, assert the presence of `time` + variable + input columns; ignore `mode` and `mode_switch` columns during generation in sample_0, but keep them for downstream metric computation.
- Optional pre-prompt summarization (derived only from allowed columns): compute basic stats (ranges, variance), lightweight change-point hints from `time/variable/input` (no mode labels), and the first `order` windows needed for `sys.reset`. Include these summaries in text form alongside the PNG to guide generation within token limits.
 - Refinement visuals: generate a comparison PNG per candidate on `sample_0` that juxtaposes real-data plot vs. simulated plot (consistent axes/legends). Use this image, plus the previous JSON, as inputs to the refinement prompts.

## 4) JSON Schema Requirements (Dainarx-compatible)
- Variables and inputs
  - `automaton.var`: comma-separated variable names (e.g., `"x"` or `"x1, x2"`).
  - Optional `automaton.input`: comma-separated input names (e.g., `"u"` or `"u1, u2"`).
- Mode dynamics
  - Use difference form indexed by order: e.g., for `order=2`, write `x[2] = f(x[1], x[0], u, ...)`.
  - Nonlinearities allowed; when helpful for NARX feature extraction, set `config.other_items` (e.g., `"x[?] ** 3"`).
- Edges
  - `direction`: string like `"1 -> 2"`.
  - `condition`: valid Python expression over `var` names (e.g., `abs(x) >= 1.2` for single variable; or `x1 >= 0.5 and x2 <= 0.1`).
  - Optional `reset`: map per-variable arrays for new `x[k]` values (length = `order`).
- Config
  - `dt`, `total_time`, `order`, `need_reset`, `kernel`/`svm_c` for SVM guards, `self_loop` as needed.

## 5) Agent Pipeline (Concrete)
1) Ingest & validate
- Load `sample_0.csv` and `sample_0.png` per task. Assert columns exist; infer `var` and `input` variable counts from CSV headers.
- Summarize statistics (ranges; change-points computed only from time/variable/input) to enrich prompts. Do not use `mode`/`mode_switch` during generation and refinement in sample_0.

2) Prompt construction (multimodal)
- System prompt baseline from `LLM_HA_Agent/SystemPrompt.md` augmented with Dainarx’s schema constraints and strict output rules (valid JSON only, correct `order`, correct variable names, equation indexing).
- Guard rail: restate that `condition` is over `var` symbols, not indices; ensure consistency between `var`, `input`, and equation symbols. Explicitly state that `mode` and `mode_switch` are not provided to the LLM during generation and refinement in sample_0.
 - Initial seeding: PNG-only prompt using `sample_0.png` to elicit diverse JSONs.
 - Refinement prompts: include the previous JSON and a single combined PNG that juxtaposes the real-data plot and the simulated plot from the previous JSON (side-by-side or overlay with identical axes/legends). Instruct the LLM to produce a minimally edited, improved JSON.

3) Initial JSON synthesis (PNG-first seeding)
- PNG-only seeds: Call Gemini with an image-only prompt to generate a large, diverse pool of JSON seeds (e.g., `png_seed_count = 64–128`). Encourage diversity in: mode count (1–4), guard forms (thresholds on magnitudes/signs), `order ∈ {1,2,3}`, and input presence. Require strictly valid JSON; no prose.
- Optional constrain pass: For top seeds, add minimal textual hints allowed from CSV (variable count, input count, rough `dt` inferred from `time` deltas) to nudge gross properties while preserving image-driven diversity.
- Validate, dedupe, gate: Schema/syntax check; deduplicate by normalized JSON; gate with simple numeric sanity checks (e.g., order matches reset length). Discard inconsistent specs.
- Seed islands: Distribute survivors across islands; if fewer than `num_islands`, replicate best-diverse seeds to fill.

4) Simulation & scoring (Dainarx)
- Convert the candidate JSON to `HybridAutomata` with `HybridAutomata.from_json`.
- Refinement-on-sample_0: simulate on the `sample_0` time grid using its input series; compute trajectory-only metrics (e.g., RMSE/MAE, `mean_diff`, `max_diff`) without using `mode` and `mode_switch`. Optionally compare LLM guard crossings to change-points detected from time/variable/input to generate guard diagnostics (no ground-truth modes).
- Note: `mode` and `mode_switch` are not used during generation and refinement in sample_0.
- Final evaluation: reuse bench CSVs as reference and compute Dainarx metrics on `sample_1,sample_2,...,sample_n`, including `tc` and `clustering_error` which may use ground-truth modes.
- Aggregate a scalar score for selection during refinement (trajectory-only), e.g., `score_refine = mean_diff + 0.1 * max_diff`. Use full Dainarx metrics for reporting.

5) Iterative refinement (Island model)
- Maintain `num_islands` parallel populations in an experience buffer. For each iteration:
  - Compose comparison PNG: simulate each candidate on sample_0, render its sim plot, then compose a single PNG combining the real-data plot and the sim plot (side-by-side or overlay with identical axes/legends). Optionally annotate change-points and simulated guard crossings.
  - Per-island prompting: provide the previous JSON and its comparison PNG; prepend succinct diagnostics (trajectory error stats; change-point vs. guard-crossing discrepancies) derived only from allowed signals in sample_0.
  - Mutations via LLM: request targeted edits (e.g., adjust guard thresholds, modify coefficients, add/remove weak nonlinear terms, tweak `order` within bounds) rather than full rewrites when diagnostics are localized.
  - Scoring: evaluate on sample_0 trajectory-only metrics to get `score_refine`; register into the buffer.
  - Selection: softmax over clustered candidates within island using a temperature schedule (as in `cluster_sampling_temperature_*`).
  - Migration/reset: periodically reset weakest islands to the global elites or diversify by re-seeding with perturbed elites; migrate top candidates between islands on a fixed schedule.
- Continue until convergence (no improvement over patience), or budget is exhausted.

6) Test set evaluation & reporting
- Freeze the best JSON per task family using only `sample_0` as seed; evaluate on `sample_1,sample_2,...,sample_n` and export per-task JSON + metrics and overlay plots.

## 6) Implementation Plan
- Phase 0: Env setup
  - Use Python ≥3.9. Install Dainarx deps: `numpy scikit-learn matplotlib networkx`.
  - For Gemini, set `GEMINI_API_KEY` (or `API_KEY`). Default model: `models/gemini-flash-lite-latest`.

- Phase 1: Orchestrator (new module e.g., `LLM_HA_Agent/runner.py`)
  - `load_case(root) → (csv_df, png_path, meta)`
  - `summarize_csv(df, allowed_cols=[time, states, inputs]) → stats`
  - `build_prompt(meta, stats, png)`
  - `llm_generate_png_seeds(png, n) → [json_candidates]` (image-only seeds)
  - `llm_constrain_top_seeds(cands, hints) → [json_candidates]` (optional, minimal CSV-derived hints)
  - `validate_and_fix(json_text) → parsed_spec | error`
  - `simulate_and_score_refine(spec, df_sample0) → traj_metrics, score_refine` (trajectory-only)
  - `simulate_and_plot(spec, df_sample0) → sim_png`
  - `compose_comparison(real_png, sim_png) → combined_png`
  - `build_refine_prompt(prev_json, combined_png, diagnostics) → prompt`
  - `evaluate_spec_final(spec, df_tests, gt_modes) → dainarx_metrics` (for reporting)
  - `refine(prompt, diagnostics) → new_prompt`

- Phase 2: Dainarx bridge
  - Import modules from `pre_works/Dainarx_code/src/…` to avoid subprocess overhead.
  - Implement `json_to_system(spec)` using `HybridAutomata.from_json`; simulate on CSV time grids with inputs; ensure `sys.reset(init_state, input[:, :order])` (init state taken from CSV first `order` samples).
  - For refinement, compute trajectory metrics directly (no gt modes). For final evaluation, use `Evaluation` to compute `mean_diff`, `max_diff`, `tc`, `clustering_error`.

- Phase 3: Search loop (Island model)
  - Configure `num_islands` (e.g., 8–12), `samples_per_prompt` (e.g., 4), `functions_per_prompt` (e.g., 2), reset period, and temperature schedule from LLM-SR’s `Config` and `ExperienceBufferConfig`.
  - Per-iteration, per-island: prompt → generate targeted edits (not full rewrites) → validate → score (`score_refine`) → register.
  - Every `reset_period` seconds or K iterations: reset weakest island(s) to promote exploration; optionally migrate top-1 between islands.
  - Early-stop on convergence window or budget.

- Phase 4: Batch + reporting
  - Sweep across families; save: generated JSON, per-sample metrics, aggregated tables, and overlay plots under `LLM_HA_Agent/result/<family>/<task>/`.

## 7) Prompting Details (LLM constraints that matter)
- Always match variable names: if CSV has `x1,x2`, then equations and `condition` must use `x1,x2` (not `x`).
- Use discrete-time indices: e.g., `x1[2] = a*x1[1] + b*x1[0] + c*u` for `order=2`.
- Prefer minimal, interpretable nonlinearities; if cubic terms are likely (e.g., Duffing), add `config.other_items: "x[?] ** 3"`.
- Guards should be threshold-like over variable(s); avoid time-dependent conditions unless clearly present in data.
- If resets are required (bouncing/impacts), provide arrays of length `order` for each var in `reset`.
- Do not include or rely on `mode` and `mode_switch` fields from CSV in prompts; generation is driven solely by time/variable/input and the PNG.
- Do not use `mode` and `mode_switch` during generation and refinement in sample_0.
- For island prompts, prepend concise “context packs” of the island’s elites (IDs, short diffs vs. data, and minimal JSON snippets limited to changed fields) to steer exploration without leaking ground-truth modes.
- PNG seeding guidance:
  - Ask for multiple plausible HA JSONs explaining visible behaviors (oscillation, saturation, impacts) with varied mode counts and guard thresholds.
  - Require explicit `order` (prefer 1–3). If periodic excitation is visually evident, include an input `u` with sinusoidal structure as a placeholder; parameters will be tuned by refinement.
  - Enforce Dainarx-compatible JSON; disallow any non-JSON output.
 - Refinement (comparative) guidance:
   - Provide the previous JSON and a combined comparison PNG (real vs. simulated) with identical axes and clear legends; ask for minimal, targeted JSON edits to reduce trajectory error and align switching.
   - Require JSON-only output; maintain variable names and keep `order` within predefined bounds.
   - If proposing guard changes, express `condition` over declared variables only; do not introduce time-dependent conditions.

## 8) Evaluation Metrics (pragmatic)
- Refinement stage (sample_0): trajectory-only metrics (RMSE/MAE, `mean_diff`, `max_diff`) computed against CSV variables; optional guard diagnostics from change-point detection on time/variable/input.
- Final reporting (sample_1,sample_2,...,sample_n): Dainarx outputs including `mean_diff`, `max_diff`, `tc`, and `clustering_error` (may use ground-truth modes). Report per-sample and per-task averages; include overlays for qualitative review.

## 12) Refinement Search Config (Island model)
- `num_islands`: 8–12 (diversity vs. compute)
- `samples_per_prompt`: 4 (per island per iteration)
- `functions_per_prompt`: 2 (top per-island exemplars in prompt)
- `cluster_sampling_temperature_init`: 0.1; `cluster_sampling_temperature_period`: 30,000 (iterations or scoring events)
- `reset_period`: 4 hours (or every K iterations in offline runs)
- `patience`: e.g., 10–20 iterations without improvement before early-stop/reset of an island
- `order_bounds`: {1,2,3}; restrict changes within bounds during refinement
 - `png_seed_count`: 64–128; generate image-only seeds up front; dedupe and distribute across islands

## 9) Risks & Mitigations
- Invalid JSON or schema drift → strict validator + auto-fix pass; re-prompt on persistent errors.
- Variable/guard mismatch → assert variables and re-bind `condition` lambdas to the declared `var` list.
- Input/guard mismatch → assert inputs and re-bind `condition` lambdas to the declared `input` list.
- Order mis-specification → try `order ∈ {1,2,3}` if residuals are high; reselect based on AIC-like criteria on `mean_diff`.
- Overfitting to sample_0 → hold-out evaluation with `sample_1,sample_2,...,sample_n`, plus regularization via simpler guards.
- Dainarx code quirk: `pre_works/Dainarx_code/main.py` starts with `cimport json` (typo); replace with `import json` in our bridge path or avoid importing that module directly.
 - PNG ambiguity (axes/scales/overplots) → use the optional constrain pass (variable count, dt) and seed gating; rely on sample_0 trajectory scoring to filter weak seeds.

## 10) Deliverables
- Code: orchestrator (`runner.py`) with bridges, validators, and plotting helpers.
- Artifacts: generated JSONs, metrics CSV/JSON, and overlays.
- Documentation: minimal README on how to run experiments and reproduce results.

## 11) Next Steps (actionable)
- Implement `LLM_HA_Agent/runner.py` skeleton and JSON validator.
- Wire Dainarx bridge for programmatic evaluation with one task (e.g., `non_linear/duffing`).
- Draft the first multimodal prompt using `sample_0` and iterate until valid JSON simulates.
- Generalize to batch execution and export results.
