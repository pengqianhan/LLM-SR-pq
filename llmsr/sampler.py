# Copyright 2023 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

""" Class for sampling new program skeletons. """
from __future__ import annotations
from abc import ABC, abstractmethod

from typing import Collection, Sequence, Type
import numpy as np
import time

from llmsr import evaluator
from llmsr import buffer
from llmsr import config as config_lib
import requests
import json
import http.client
import os



class LLM(ABC):
    def __init__(self, samples_per_prompt: int) -> None:
        self._samples_per_prompt = samples_per_prompt

    def _draw_sample(self, prompt: str) -> str:
        """ Return a predicted continuation of `prompt`."""
        raise NotImplementedError('Must provide a language model.')

    @abstractmethod
    def draw_samples(self, prompt: str) -> Collection[str]:
        """ Return multiple predicted continuations of `prompt`. """
        return [self._draw_sample(prompt) for _ in range(self._samples_per_prompt)]



class Sampler:
    """ Node that samples program skeleton continuations and sends them for analysis. """
    _global_samples_nums: int = 1 

    def __init__(
            self,
            database: buffer.ExperienceBuffer,
            evaluators: Sequence[evaluator.Evaluator],
            samples_per_prompt: int,
            config: config_lib.Config,
            max_sample_nums: int | None = None,
            llm_class: Type[LLM] = LLM,
    ):
        self._samples_per_prompt = samples_per_prompt
        self._database = database
        self._evaluators = evaluators
        self._llm = llm_class(samples_per_prompt)
        self._max_sample_nums = max_sample_nums
        self.config = config

    
    def sample(self, **kwargs):
        """ Continuously gets prompts, samples programs, sends them for analysis. """
        while True:
            # stop the search process if hit global max sample nums
            if self._max_sample_nums and self.__class__._global_samples_nums >= self._max_sample_nums:
                break
            
            prompt = self._database.get_prompt()
            # print('prompt.code:',prompt.code)
            '''
            """
            Find the mathematical function skeleton that represents acceleration in a damped nonlinear oscillator system with driving force, given data on position, and velocity. 
            """


            import numpy as np

            #Initialize parameters
            MAX_NPARAMS = 10
            params = [1.0]*MAX_NPARAMS


            def equation_v0(x: np.ndarray, v: np.ndarray, params: np.ndarray) -> np.ndarray:
                """ Mathematical function for acceleration in a damped nonlinear oscillator

                Args:
                    x: A numpy array representing observations of current position.
                    v: A numpy array representing observations of velocity.
                    params: Array of numeric constants or parameters to be optimized

                Return:
                    A numpy array representing acceleration as the result of applying the mathematical function to the inputs.
                """
                dv = params[0] * x  +  params[1] * v  + params[2]
                return dv


            def equation_v1(x: np.ndarray, v: np.ndarray, params: np.ndarray) -> np.ndarray:
                """Improved version of `equation_v0`."""
            
            
            '''
            
            reset_time = time.time()
            samples = self._llm.draw_samples(prompt.code,self.config)
            sample_time = (time.time() - reset_time) / self._samples_per_prompt

            # This loop can be executed in parallel on remote evaluator machines.
            for sample in samples:
                # print('============sample====================:\n',sample)
                '''
                    """ Mathematical function for acceleration in a damped nonlinear oscillator

                    Args:
                        x: A numpy array representing observations of current position.
                        v: A numpy array representing observations of velocity.
                        params: Array of numeric constants or parameters to be optimized

                    Return:
                        A numpy array representing acceleration as the result of applying the mathematical function to the inputs.
                    """
                    dv = params[0] * x  +  params[1] * v  + params[2]
                    return dv


                def equation_v1(x: np.ndarray, v: np.ndarray, params: np.ndarray) -> np.ndarray:
                    """Improved version of `equation_v0`.

                    This version introduces a nonlinear term for damping and a driving force term.
                    The general form of the equation of motion for a damped nonlinear oscillator
                    with a driving force is:
                    m * d^2x/dt^2 + f(dx/dt) + g(x) = F(t)

                    where:
                    m is mass (can be absorbed into parameters if not explicitly known)
                    d^2x/dt^2 is acceleration
                    f(dx/dt) is the damping force (can be linear or nonlinear)
                    g(x) is the restoring force (can be linear or nonlinear)
                    F(t) is the driving force (can be time-dependent or position/velocity dependent)

                    In this improved version, we'll model:
                    - Linear damping: params[1] * v
                    - Nonlinear damping: params[3] * v**3 (e.g., cubic damping)
                    - Nonlinear restoring force: params[0] * x + params[4] * x**3 (e.g., hardening spring)
                    - A constant driving force: params[2]
                    - A velocity-dependent driving force: params[5] * v
                    - A position-dependent driving force: params[6] * x

                    Thus, acceleration (d^2x/dt^2) will be:
                    acceleration
                '''

                self._global_sample_nums_plus_one()
                cur_global_sample_nums = self._get_global_sample_nums()
                chosen_evaluator: evaluator.Evaluator = np.random.choice(self._evaluators)
                chosen_evaluator.analyse(
                    sample,
                    prompt.island_id,
                    prompt.version_generated,
                    **kwargs,
                    global_sample_nums=cur_global_sample_nums,
                    sample_time=sample_time
                )

    def _get_global_sample_nums(self) -> int:
        return self.__class__._global_samples_nums

    def set_global_sample_nums(self, num):
        self.__class__._global_samples_nums = num

    def _global_sample_nums_plus_one(self):
        self.__class__._global_samples_nums += 1






def _extract_body(sample: str, config: config_lib.Config) -> str:
    """
    Extract the function body from a response sample, removing any preceding descriptions
    and the function signature. Preserves indentation.
    ------------------------------------------------------------------------------------------------------------------
    Input example:
    ```
    This is a description...
    def function_name(...):
        return ...
    Additional comments...
    ```
    ------------------------------------------------------------------------------------------------------------------
    Output example:
    ```
        return ...
    Additional comments...
    ```
    ------------------------------------------------------------------------------------------------------------------
    If no function definition is found, returns the original sample.
    """
    lines = sample.splitlines()
    func_body_lineno = 0
    find_def_declaration = False
    
    for lineno, line in enumerate(lines):
        # find the first 'def' program statement in the response
        if line[:3] == 'def':
            func_body_lineno = lineno
            find_def_declaration = True
            break
    
    if find_def_declaration:
        # for gpt APIs
        if config.use_api:
            code = ''
            for line in lines[func_body_lineno + 1:]:
                code += line + '\n'
        
        # for mixtral
        else:
            code = ''
            indent = '    '
            for line in lines[func_body_lineno + 1:]:
                if line[:4] != indent:
                    line = indent + line
                code += line + '\n'
        
        return code
    
    return sample



class LocalLLM(LLM):
    def __init__(self, samples_per_prompt: int, batch_inference: bool = True, trim=True) -> None:
        """
        Args:
            batch_inference: Use batch inference when sample equation program skeletons. The batch size equals to the samples_per_prompt.
        """
        super().__init__(samples_per_prompt)

        url = "http://127.0.0.1:5000/completions"
        instruction_prompt = ("You are a helpful assistant tasked with discovering mathematical function structures for scientific systems. \
                             Complete the 'equation' function below, considering the physical meaning and relationships of inputs.\n\n")
        self._batch_inference = batch_inference
        self._url = url
        self._instruction_prompt = instruction_prompt
        self._trim = trim


    def draw_samples(self, prompt: str, config: config_lib.Config) -> Collection[str]:
        """Returns multiple equation program skeleton hypotheses for the given `prompt`."""
        if config.use_api:
            # 确定使用哪种API
            api_type = self._determine_api_type(config)
            
            if api_type == 'gemini':
                return self._draw_samples_api_gemini(prompt, config)
            else:  # 默认使用OpenAI
                return self._draw_samples_api(prompt, config)
        else:
            return self._draw_samples_local(prompt, config)

    def _determine_api_type(self, config: config_lib.Config) -> str:
        """根据配置确定使用哪种API类型"""
        # 如果明确指定了api_type且不是auto，直接使用
        if hasattr(config, 'api_type') and config.api_type and config.api_type != 'auto':
            return config.api_type.lower()
        
        # 否则根据模型名称自动判断
        if config.api_model:
            model_name = config.api_model.lower()
            if 'gemini' in model_name:
                return 'gemini'
            elif any(openai_model in model_name for openai_model in ['gpt', 'chatgpt', 'davinci', 'curie', 'babbage', 'ada']):
                return 'openai'
        
        # 默认返回openai
        return 'openai'


    def _draw_samples_local(self, prompt: str, config: config_lib.Config) -> Collection[str]:    
        # instruction
        prompt = '\n'.join([self._instruction_prompt, prompt])
        while True:
            try:
                all_samples = []
                # response from llm server
                if self._batch_inference:
                    response = self._do_request(prompt)
                    for res in response:
                        all_samples.append(res)
                else:
                    for _ in range(self._samples_per_prompt):
                        response = self._do_request(prompt)
                        all_samples.append(response)

                # trim equation program skeleton body from samples
                if self._trim:
                    all_samples = [_extract_body(sample, config) for sample in all_samples]
                
                return all_samples
            except Exception:
                continue


    def _draw_samples_api(self, prompt: str, config: config_lib.Config) -> Collection[str]:
        all_samples = []
        prompt = '\n'.join([self._instruction_prompt, prompt])
        
        for _ in range(self._samples_per_prompt):
            while True:
                try:
                    conn = http.client.HTTPSConnection("api.openai.com")
                    payload = json.dumps({
                        "max_tokens": 512,
                        "model": config.api_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    })
                    headers = {
                        'Authorization': f"Bearer {os.environ['API_KEY']}",
                        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                        'Content-Type': 'application/json'
                    }
                    conn.request("POST", "/v1/chat/completions", payload, headers)
                    res = conn.getresponse()
                    data = json.loads(res.read().decode("utf-8"))
                    response = data['choices'][0]['message']['content']
                    
                    if self._trim:
                        response = _extract_body(response, config)
                    
                    all_samples.append(response)
                    break

                except Exception:
                    continue
        
        return all_samples


    def _draw_samples_api_gemini(self, prompt: str, config: config_lib.Config) -> Collection[str]:
        """使用最新的Google Gen AI Python SDK生成样本"""
        all_samples = []
        prompt = '\n'.join([self._instruction_prompt, prompt])
        
        # 导入最新的Google Gen AI库
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError("请安装最新的google-genai库: pip install google-genai")
        
        # 配置API密钥 - 优先使用GEMINI_API_KEY，否则使用API_KEY
        api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('API_KEY')
        if not api_key:
            raise ValueError("请设置环境变量GEMINI_API_KEY或GOOGLE_API_KEY")
        
        # 创建客户端
        client = genai.Client(api_key=api_key)
        
        # 处理模型名称（移除可能的"models/"前缀）
        model_name = config.api_model
        if model_name.startswith("models/"):
            model_name = model_name[7:]  # 移除"models/"前缀
        if model_name.startswith("gemini-flash-lite-latest") or model_name.startswith("gemini-2.5-flash-lite"):
            thinking_budget = 24576
        elif model_name.startswith("gemini-flash-latest") or model_name.startswith("gemini-2.5-flash"):
            thinking_budget = 24576
        elif model_name.startswith("gemini-2.5-pro"):
            thinking_budget = 32768
        else:
            thinking_budget = None

        generation_config_kwargs = {
            'max_output_tokens': 512,
            'temperature': 0.8,
            'top_p': 0.9,
            'top_k': 40,
        }

        if thinking_budget is not None:
            generation_config_kwargs['thinking_config'] = types.ThinkingConfig(
                thinking_budget=thinking_budget
            )

        for i in range(self._samples_per_prompt):
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    # 使用新的API生成内容
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(**generation_config_kwargs)
                    )
                    # print('=================response====================:\n',response)

                    # print('=================response.text====================:\n',response.text)
                    
                    if response.text:
                        response_text = response.text
                        
                        if self._trim:
                            response_text = _extract_body(response_text, config)
                        # print('=================response_text====================:\n',response_text)
                        all_samples.append(response_text)

                        candidate = next(iter(getattr(response, 'candidates', [])), None)
                        if candidate is not None:
                            thinking_output = getattr(candidate, 'thinking', None)
                            if thinking_output is not None:
                                print('thinking_output:', thinking_output)
                        break
                    else:
                        print(f"Gemini API返回空响应 (样本 {i+1}/{self._samples_per_prompt})")
                        retry_count += 1
                        
                except Exception as e:
                    retry_count += 1
                    print(f"Gemini API调用失败 (样本 {i+1}/{self._samples_per_prompt}, 重试 {retry_count}/{max_retries}): {e}")
                    
                    if retry_count < max_retries:
                        import time
                        time.sleep(1)  # 短暂延迟后重试
                    else:
                        # 如果所有重试都失败，添加一个默认的空响应
                        print(f"样本 {i+1} 生成失败，跳过")
                        all_samples.append("")
                        break
        
        # 过滤掉空响应
        all_samples = [sample for sample in all_samples if sample.strip()]
        
        # 如果没有成功生成任何样本，抛出异常
        if not all_samples:
            raise RuntimeError("Gemini API未能生成任何有效样本")
        
        return all_samples
    
    
    def _do_request(self, content: str) -> str:
        content = content.strip('\n').strip()
        # repeat the prompt for batch inference
        repeat_prompt: int = self._samples_per_prompt if self._batch_inference else 1
        
        data = {
            'prompt': content,
            'repeat_prompt': repeat_prompt,
            'params': {
                'do_sample': True,
                'temperature': None,
                'top_k': None,
                'top_p': None,
                'add_special_tokens': False,
                'skip_special_tokens': True,
            }
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self._url, data=json.dumps(data), headers=headers)
        
        if response.status_code == 200: #Server status code 200 indicates successful HTTP request! 
            response = response.json()["content"]
            
            return response if self._batch_inference else response[0]

