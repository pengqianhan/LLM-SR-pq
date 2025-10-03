"""
SmolAgents-based sampler that uses CodeAgent for equation discovery.
This replaces the custom Sampler with a cleaner agent-based architecture.
"""
from __future__ import annotations

import time
from typing import Any, Sequence, Optional
import numpy as np

from smolagents import CodeAgent, ToolCallingAgent

from llmsr import buffer
from llmsr import evaluator
from llmsr import code_manipulation
from llmsr.smolagents_models import UnifiedModel
from llmsr.smolagents_tools import evaluate_equation_code, extract_function_body


class SmolAgentsSampler:
    """
    Simplified sampler using SmolAgents CodeAgent.
    Replaces the custom LLM sampling loop with agent-based generation.
    """
    
    _global_samples_nums: int = 1
    
    def __init__(
        self,
        database: buffer.ExperienceBuffer,
        evaluators: Sequence[evaluator.Evaluator],
        model: UnifiedModel,
        samples_per_prompt: int = 4,
        max_sample_nums: Optional[int] = None,
        use_planning: bool = False,
        planning_interval: int = 3
    ):
        """
        Initialize the SmolAgents-based sampler.
        
        Args:
            database: Experience buffer for storing and retrieving programs
            evaluators: List of evaluator instances
            model: Unified model wrapper
            samples_per_prompt: Number of samples to generate per prompt
            max_sample_nums: Maximum total samples (None = unlimited)
            use_planning: Whether to enable planning in CodeAgent
            planning_interval: Steps between planning phases
        """
        self._database = database
        self._evaluators = evaluators
        self._model = model
        self._samples_per_prompt = samples_per_prompt
        self._max_sample_nums = max_sample_nums
        self._use_planning = use_planning
        self._planning_interval = planning_interval
        
        # Build instruction prompt
        self._instruction_prompt = (
            "You are a helpful assistant tasked with discovering mathematical function structures "
            "for scientific systems. Complete the 'equation' function below, considering the "
            "physical meaning and relationships of inputs.\n\n"
        )
    
    def sample(self, **kwargs):
        """
        Main sampling loop - continuously generates and evaluates equations.
        """
        profiler = kwargs.get('profiler', None)
        
        while True:
            # Check stopping condition
            if self._max_sample_nums and self._global_samples_nums >= self._max_sample_nums:
                break
            
            # Get prompt from experience buffer
            prompt = self._database.get_prompt()
            
            # Prepare full prompt with instruction
            full_prompt = self._instruction_prompt + prompt.code
            
            # Generate samples using the model
            reset_time = time.time()
            samples = self._generate_samples(full_prompt)
            sample_time = (time.time() - reset_time) / len(samples) if samples else 0
            
            # Evaluate each sample
            for sample in samples:
                self._global_sample_nums_plus_one()
                cur_global_sample_nums = self._get_global_sample_nums()
                
                # Randomly assign to an evaluator
                chosen_evaluator = np.random.choice(self._evaluators)
                chosen_evaluator.analyse(
                    sample,
                    prompt.island_id,
                    prompt.version_generated,
                    profiler=profiler,
                    global_sample_nums=cur_global_sample_nums,
                    sample_time=sample_time
                )
    
    def _generate_samples(self, prompt: str) -> list[str]:
        """
        Generate multiple equation samples from the prompt.
        
        Args:
            prompt: Full prompt including instruction and context
            
        Returns:
            List of generated equation function bodies
        """
        all_samples = []
        
        for _ in range(self._samples_per_prompt):
            try:
                # Use the model's generate method
                responses = self._model.generate(prompt, num_samples=1)
                
                if responses:
                    response = responses[0]
                    # Extract the function body
                    body = self._extract_body(response)
                    if body:
                        all_samples.append(body)
            except Exception as e:
                print(f"Sample generation error: {e}")
                continue
        
        return all_samples
    
    def _extract_body(self, sample: str) -> str:
        """
        Extract the function body from a response sample.
        
        Args:
            sample: Raw LLM response
            
        Returns:
            Cleaned function body
        """
        lines = sample.splitlines()
        func_body_lineno = 0
        find_def_declaration = False
        
        for lineno, line in enumerate(lines):
            if line.strip().startswith('def '):
                func_body_lineno = lineno
                find_def_declaration = True
                break
        
        if find_def_declaration:
            code = ''
            indent = '    '
            for line in lines[func_body_lineno + 1:]:
                # Ensure consistent indentation
                if line and not line.startswith(indent) and line.strip():
                    line = indent + line
                code += line + '\n'
            return code
        
        # If no def found, return original
        return sample
    
    def _get_global_sample_nums(self) -> int:
        """Get current global sample count."""
        return self.__class__._global_samples_nums
    
    def _global_sample_nums_plus_one(self):
        """Increment global sample counter."""
        self.__class__._global_samples_nums += 1


class SmolAgentsCodeAgentSampler:
    """
    Advanced sampler that uses CodeAgent for iterative reasoning.
    This variant uses the full agent capabilities including planning.
    """
    
    _global_samples_nums: int = 1
    
    def __init__(
        self,
        database: buffer.ExperienceBuffer,
        evaluators: Sequence[evaluator.Evaluator],
        model: UnifiedModel,
        samples_per_prompt: int = 4,
        max_sample_nums: Optional[int] = None,
        enable_planning: bool = True,
        planning_interval: int = 3
    ):
        """
        Initialize CodeAgent-based sampler with tool support.
        
        Args:
            database: Experience buffer
            evaluators: List of evaluators
            model: Unified model wrapper
            samples_per_prompt: Samples per prompt
            max_sample_nums: Maximum samples
            enable_planning: Enable agent planning
            planning_interval: Planning frequency
        """
        self._database = database
        self._evaluators = evaluators
        self._model = model
        self._samples_per_prompt = samples_per_prompt
        self._max_sample_nums = max_sample_nums
        
        # Create CodeAgent with tools
        # Note: CodeAgent requires an actual SmolAgents model instance
        agent_kwargs = {
            'tools': [extract_function_body],
            'model': model.model,  # Use the underlying SmolAgents model
            'max_steps': 5
        }
        
        if enable_planning:
            agent_kwargs['planning_interval'] = planning_interval
        
        self._agent = CodeAgent(**agent_kwargs)
    
    def sample(self, **kwargs):
        """
        Sample using CodeAgent for more sophisticated generation.
        """
        profiler = kwargs.get('profiler', None)
        
        while True:
            if self._max_sample_nums and self._global_samples_nums >= self._max_sample_nums:
                break
            
            prompt = self._database.get_prompt()
            
            # Build task for the agent
            task = (
                f"Generate {self._samples_per_prompt} improved mathematical equation functions "
                f"based on the following context. Each function should be a valid Python function body.\n\n"
                f"{prompt.code}\n\n"
                f"Return only the function body (the code inside the function, properly indented)."
            )
            
            reset_time = time.time()
            
            try:
                # Run the agent
                result = self._agent.run(task)
                
                # Extract samples from agent result
                # The agent might return code or text; parse accordingly
                samples = self._parse_agent_result(result)
                
            except Exception as e:
                print(f"Agent execution error: {e}")
                samples = []
            
            sample_time = (time.time() - reset_time) / max(len(samples), 1)
            
            # Evaluate samples
            for sample in samples[:self._samples_per_prompt]:
                self._global_sample_nums_plus_one()
                cur_global_sample_nums = self._get_global_sample_nums()
                
                chosen_evaluator = np.random.choice(self._evaluators)
                chosen_evaluator.analyse(
                    sample,
                    prompt.island_id,
                    prompt.version_generated,
                    profiler=profiler,
                    global_sample_nums=cur_global_sample_nums,
                    sample_time=sample_time
                )
    
    def _parse_agent_result(self, result: Any) -> list[str]:
        """
        Parse the agent's result to extract equation bodies.
        
        Args:
            result: Agent execution result
            
        Returns:
            List of extracted function bodies
        """
        # Agent result is typically a string or dict
        if isinstance(result, str):
            # Try to extract function bodies from the result
            return [self._extract_body(result)]
        
        return []
    
    def _extract_body(self, sample: str) -> str:
        """Extract function body from sample."""
        lines = sample.splitlines()
        func_body_lineno = 0
        find_def = False
        
        for lineno, line in enumerate(lines):
            if line.strip().startswith('def '):
                func_body_lineno = lineno
                find_def = True
                break
        
        if find_def:
            code = ''
            indent = '    '
            for line in lines[func_body_lineno + 1:]:
                if line and not line.startswith(indent) and line.strip():
                    line = indent + line
                code += line + '\n'
            return code
        
        return sample
    
    def _get_global_sample_nums(self) -> int:
        """Get global sample count."""
        return self.__class__._global_samples_nums
    
    def _global_sample_nums_plus_one(self):
        """Increment global sample counter."""
        self.__class__._global_samples_nums += 1

