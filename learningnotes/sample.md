- 我们从 `Sampler` 的构造器看 `self._llm` 的诞生：它接收一个 `llm_class`（默认给的是 `LLM` 基类），然后用 `samples_per_prompt` 这个超参数实例化，生成 `self._llm`；这一行决定了后续采样用的具体 LLM 实现是谁  
```53:68:llmsr/sampler.py
class Sampler:
    ...
    def __init__(..., llm_class: Type[LLM] = LLM):
        ...
        self._llm = llm_class(samples_per_prompt)
```
- `LLM` 是一个抽象基类（继承自 `ABC`），负责统一接口：它记录每次 prompt 需要多少样本，并把 `draw_samples` 定义成抽象方法；这样任何子类都必须实现 `draw_samples`，才能告诉 `Sampler` 如何真正向模型取样  
```34:45:llmsr/sampler.py
class LLM(ABC):
    def __init__(self, samples_per_prompt: int) -> None:
        self._samples_per_prompt = samples_per_prompt
    @abstractmethod
    def draw_samples(self, prompt: str) -> Collection[str]:
        return [self._draw_sample(prompt) for _ in range(self._samples_per_prompt)]
```
- `LocalLLM` 这个子类继承自 `LLM`，在 `super().__init__` 里沿用父类对 `samples_per_prompt` 的保存，同时额外配置了本地或远程推理所需的 URL、指令前缀、是否批量推理、是否裁剪函数体等运行参数  
```242:258:llmsr/sampler.py
class LocalLLM(LLM):
    def __init__(self, samples_per_prompt: int, batch_inference: bool = True, trim=True) -> None:
        super().__init__(samples_per_prompt)
        url = "http://127.0.0.1:5000/completions"
        instruction_prompt = ("You are a helpful assistant ...")
        self._batch_inference = batch_inference
        self._url = url
        self._instruction_prompt = instruction_prompt
        self._trim = trim
```
- `LocalLLM` 重写了抽象方法 `draw_samples`，根据配置判断走哪条路径：如果 `config.use_api` 为真会进一步挑选 `OpenAI` 或 `Gemini` 的 API 调用，否则走本地推理；每条路径内部都用父类保存的 `self._samples_per_prompt` 控制生成次数  
```259:270:llmsr/sampler.py
    def draw_samples(self, prompt: str, config: config_lib.Config) -> Collection[str]:
        if config.use_api:
            api_type = self._determine_api_type(config)
            if api_type == 'gemini':
                return self._draw_samples_api_gemini(prompt, config)
            else:
                return self._draw_samples_api(prompt, config)
        else:
            return self._draw_samples_local(prompt, config)
```
- 总结一下继承链条：`Sampler` 并不关心具体 LLM 实现，只要求传入的 `llm_class` 遵循 `LLM` 抽象接口；`LocalLLM` 在继承时沿用了父类对采样规模的管理，补充了自己的请求逻辑；运行时 `self._llm` 因此是一个多态对象，既能符合统一接口，又能根据子类特性完成 API 调用或本地推理。