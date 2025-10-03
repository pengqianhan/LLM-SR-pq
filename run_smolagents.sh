#!/bin/bash

# SmolAgents-based LLMSR Runner
# This script demonstrates various ways to run LLMSR with the simplified SmolAgents architecture

echo "========================================================================"
echo "LLM-SR with SmolAgents - Quick Start Examples"
echo "========================================================================"
echo ""

# Set default values
PROBLEM_NAME="${PROBLEM_NAME:-oscillator1}"
SPEC_PATH="${SPEC_PATH:-specs/specification_oscillator1_numpy.txt}"
LOG_PATH="${LOG_PATH:-logs/${PROBLEM_NAME}_smolagents}"
MAX_SAMPLES="${MAX_SAMPLES:-100}"  # Lower default for testing

echo "Problem: $PROBLEM_NAME"
echo "Spec: $SPEC_PATH"
echo "Log path: $LOG_PATH"
echo "Max samples: $MAX_SAMPLES"
echo ""

# Prompt user to select mode
echo "Select execution mode:"
echo "1) Local model (Qwen/Qwen2.5-Coder-32B-Instruct)"
echo "2) Local model (smaller - Qwen/Qwen2.5-Coder-7B-Instruct)"
echo "3) OpenAI API (GPT-3.5-turbo)"
echo "4) OpenAI API (GPT-4)"
echo "5) Gemini API (gemini-2.5-flash-latest)"
echo "6) HuggingFace Inference API"
echo ""

read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo "Running with local Qwen 32B model..."
        python main_smolagents.py \
            --problem_name "$PROBLEM_NAME" \
            --spec_path "$SPEC_PATH" \
            --log_path "$LOG_PATH" \
            --max_samples "$MAX_SAMPLES" \
            --local_model_id "Qwen/Qwen2.5-Coder-32B-Instruct"
        ;;
    
    2)
        echo "Running with local Qwen 7B model (smaller, faster)..."
        python main_smolagents.py \
            --problem_name "$PROBLEM_NAME" \
            --spec_path "$SPEC_PATH" \
            --log_path "$LOG_PATH" \
            --max_samples "$MAX_SAMPLES" \
            --local_model_id "Qwen/Qwen2.5-Coder-7B-Instruct"
        ;;
    
    3)
        if [ -z "$OPENAI_API_KEY" ] && [ -z "$API_KEY" ]; then
            echo "Error: Please set OPENAI_API_KEY or API_KEY environment variable"
            exit 1
        fi
        echo "Running with OpenAI GPT-3.5-turbo..."
        python main_smolagents.py \
            --problem_name "$PROBLEM_NAME" \
            --spec_path "$SPEC_PATH" \
            --log_path "${LOG_PATH}_gpt35" \
            --max_samples "$MAX_SAMPLES" \
            --use_api True \
            --api_model "gpt-3.5-turbo"
        ;;
    
    4)
        if [ -z "$OPENAI_API_KEY" ] && [ -z "$API_KEY" ]; then
            echo "Error: Please set OPENAI_API_KEY or API_KEY environment variable"
            exit 1
        fi
        echo "Running with OpenAI GPT-4..."
        python main_smolagents.py \
            --problem_name "$PROBLEM_NAME" \
            --spec_path "$SPEC_PATH" \
            --log_path "${LOG_PATH}_gpt4" \
            --max_samples "$MAX_SAMPLES" \
            --use_api True \
            --api_model "gpt-4"
        ;;
    
    5)
        if [ -z "$GEMINI_API_KEY" ] && [ -z "$API_KEY" ]; then
            echo "Error: Please set GEMINI_API_KEY or API_KEY environment variable"
            exit 1
        fi
        echo "Running with Gemini 2.5 Flash..."
        python main_smolagents.py \
            --problem_name "$PROBLEM_NAME" \
            --spec_path "$SPEC_PATH" \
            --log_path "${LOG_PATH}_gemini" \
            --max_samples "$MAX_SAMPLES" \
            --use_api True \
            --api_model "gemini-2.5-flash-latest"
        ;;
    
    6)
        if [ -z "$HF_TOKEN" ]; then
            echo "Error: Please set HF_TOKEN environment variable"
            exit 1
        fi
        echo "Running with HuggingFace Inference API..."
        python main_smolagents.py \
            --problem_name "$PROBLEM_NAME" \
            --spec_path "$SPEC_PATH" \
            --log_path "${LOG_PATH}_hf" \
            --max_samples "$MAX_SAMPLES" \
            --use_api True \
            --api_model "Qwen/Qwen2.5-Coder-32B-Instruct"
        ;;
    
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "========================================================================"
echo "Execution completed!"
echo "Check results at: $LOG_PATH"
echo "View logs with: tensorboard --logdir $LOG_PATH"
echo "========================================================================"

