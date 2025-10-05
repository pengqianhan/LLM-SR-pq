# python ./llm_engine/engine_qwen30a3.py --model_path Qwen/Qwen3-30B-A3B-Instruct-2507 --gpu_ids 0 1 2 --port 5000 --quantization
# python ./llm_engine/engine_qwen30a3.py --model_path Qwen/Qwen3-8B --gpu_ids 0 --port 5000
python ./llm_engine/engine_qwen3_8b.py --model_path Qwen/Qwen3-8B --gpu_ids 0 1 --port 5000
# python ./llm_engine/engine_qwen3_14b.py --model_path Qwen/Qwen3-14B --gpu_ids 0 1 2 --port 5000
