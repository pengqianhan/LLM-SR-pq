
import os
# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Load from .env file in the current directory
    print("dotenv loaded successfully from .env file")
except ImportError:
    # dotenv not available, continue without it
    print("dotenv not available, continuing without it")
    pass
except Exception:
    # .env file doesn't exist or other error, continue without raising exception
    print("Error loading .env file, continuing without it")
    pass

from argparse import ArgumentParser
import numpy as np
import torch
import pandas as pd

from llmsr import pipeline
from llmsr import config
from llmsr import sampler
from llmsr import evaluator


parser = ArgumentParser()
parser.add_argument('--port', type=int, default=None)
parser.add_argument('--use_api', type=bool, default=True)
parser.add_argument('--api_type', type=str, default="gemini", choices=['openai', 'gemini', 'auto'], help='API type to use')
parser.add_argument('--api_model', type=str, default="models/gemini-2.5-flash-lite", help='Model name for API calls')
parser.add_argument('--spec_path', type=str,default="./specs/specification_oscillator1_numpy.txt")
parser.add_argument('--log_path', type=str, default="./logs/oscillator1")
parser.add_argument('--problem_name', type=str, default="oscillator1")
parser.add_argument('--run_id', type=int, default=1)
args = parser.parse_args()




if __name__ == '__main__':
    # Load config and parameters
    class_config = config.ClassConfig(llm_class=sampler.LocalLLM, sandbox_class=evaluator.LocalSandbox)
    config = config.Config(use_api = args.use_api, 
                           api_type = args.api_type,
                           api_model = args.api_model,)
    # global_max_sample_num = 10000
    global_max_sample_num = 10000 # for test  

    # Load prompt specification
    with open(
        os.path.join(args.spec_path),
        encoding="utf-8",
    ) as f:
        specification = f.read()
    
    # Load dataset
    problem_name = args.problem_name
    df = pd.read_csv('./data/'+problem_name+'/train.csv')
    data = np.array(df)
    X = data[:, :-1]
    y = data[:, -1].reshape(-1)
    if 'torch' in args.spec_path:
        X = torch.Tensor(X)
        y = torch.Tensor(y)
    data_dict = {'inputs': X, 'outputs': y}
    dataset = {'data': data_dict} 
    
    
    pipeline.main(
        specification=specification,
        inputs=dataset,
        config=config,
        max_sample_nums=global_max_sample_num,
        class_config=class_config,
        # log_dir = 'logs/m1jobs-mixtral-v10',
        log_dir=args.log_path,
    )
