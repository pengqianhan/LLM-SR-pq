"""
Main entry point for LLMSR using SmolAgents.
This simplified version replaces the custom LLM engine with SmolAgents models.

Usage:
    # Local model (no server needed):
    python main_smolagents.py --problem_name oscillator1 \
        --spec_path specs/specification_oscillator1_numpy.txt \
        --log_path logs/oscillator1_smolagents \
        --local_model_id Qwen/Qwen2.5-Coder-32B-Instruct

    # API model (OpenAI/Gemini/HF):
    python main_smolagents.py --problem_name oscillator1 \
        --spec_path specs/specification_oscillator1_numpy.txt \
        --log_path logs/oscillator1_smolagents \
        --use_api True --api_model gpt-3.5-turbo

    # Gemini API:
    export GEMINI_API_KEY=your_key
    python main_smolagents.py --problem_name oscillator1 \
        --spec_path specs/specification_oscillator1_numpy.txt \
        --log_path logs/oscillator1_smolagents \
        --use_api True --api_model gemini-2.5-flash-latest
"""

import os
from argparse import ArgumentParser
import numpy as np
import torch
import pandas as pd

from llmsr import smolagents_pipeline as pipeline
from llmsr import config
from llmsr import evaluator


# Parse arguments
parser = ArgumentParser()
parser.add_argument('--use_api', type=bool, default=False, help='Use API-based model')
parser.add_argument('--api_model', type=str, default="gpt-3.5-turbo", help='API model name')
parser.add_argument('--api_type', type=str, default="auto", help='API type: openai, gemini, or auto')
parser.add_argument('--local_model_id', type=str, default=None, help='Local model ID for TransformersModel')
parser.add_argument('--spec_path', type=str, required=True, help='Path to specification file')
parser.add_argument('--log_path', type=str, default="./logs/smolagents_run", help='Path to log directory')
parser.add_argument('--problem_name', type=str, default="oscillator1", help='Problem name')
parser.add_argument('--run_id', type=int, default=1, help='Run ID')
parser.add_argument('--max_samples', type=int, default=10000, help='Maximum samples to generate')
parser.add_argument('--samples_per_prompt', type=int, default=4, help='Samples per prompt')
parser.add_argument('--use_planning', type=bool, default=False, help='Enable agent planning')
args = parser.parse_args()


if __name__ == '__main__':
    print("=" * 80)
    print("LLMSR with SmolAgents - Simplified Architecture")
    print("=" * 80)
    print(f"Problem: {args.problem_name}")
    print(f"Specification: {args.spec_path}")
    print(f"Log path: {args.log_path}")
    
    if args.use_api:
        print(f"Using API model: {args.api_model} (type: {args.api_type})")
    else:
        model_id = args.local_model_id or "Qwen/Qwen3-8B"
        print(f"Using local model: {model_id}")
    
    print("=" * 80)
    print()
    
    # Load configuration
    # Note: We don't need to specify llm_class anymore - SmolAgents handles it
    class_config = config.ClassConfig(
        llm_class=None,  # Not used with SmolAgents
        sandbox_class=evaluator.LocalSandbox
    )
    
    cfg = config.Config(
        use_api=args.use_api,
        api_model=args.api_model,
        api_type=args.api_type,
        samples_per_prompt=args.samples_per_prompt
    )
    
    # Load prompt specification
    with open(args.spec_path, encoding="utf-8") as f:
        specification = f.read()
    
    # Load dataset
    problem_name = args.problem_name
    df = pd.read_csv(f'./data/{problem_name}/train.csv')
    data = np.array(df)
    X = data[:, :-1]
    y = data[:, -1].reshape(-1)
    
    # Convert to torch if needed
    if 'torch' in args.spec_path:
        X = torch.Tensor(X)
        y = torch.Tensor(y)
    
    data_dict = {'inputs': X, 'outputs': y}
    dataset = {'data': data_dict}
    
    print(f"Dataset loaded: {X.shape[0]} samples, {X.shape[1]} features")
    print()
    
    # Run the SmolAgents pipeline
    pipeline.main(
        specification=specification,
        inputs=dataset,
        config=cfg,
        max_sample_nums=args.max_samples,
        class_config=class_config,
        log_dir=args.log_path,
        local_model_id=args.local_model_id,
        use_planning=args.use_planning
    )
    
    print()
    print("=" * 80)
    print("Experiment completed!")
    print(f"Check logs at: {args.log_path}")
    print("=" * 80)

