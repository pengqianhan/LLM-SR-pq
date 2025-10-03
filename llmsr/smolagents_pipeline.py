"""
Simplified LLMSR pipeline using SmolAgents.
This module provides a streamlined version of the main pipeline.
"""
from __future__ import annotations

from typing import Any, Sequence

from llmsr import code_manipulation
from llmsr import config as config_lib
from llmsr import evaluator
from llmsr import buffer
from llmsr import profile
from llmsr.smolagents_models import UnifiedModel
from llmsr.smolagents_sampler import SmolAgentsSampler


def _extract_function_names(specification: str) -> tuple[str, str]:
    """
    Extract the names of the function to evolve and the evaluation function.
    
    Args:
        specification: Template code with @evaluate.run and @equation.evolve decorators
        
    Returns:
        Tuple of (function_to_evolve, function_to_run)
    """
    run_functions = list(code_manipulation.yield_decorated(specification, 'evaluate', 'run'))
    if len(run_functions) != 1:
        raise ValueError('Expected 1 function decorated with `@evaluate.run`.')
    
    evolve_functions = list(code_manipulation.yield_decorated(specification, 'equation', 'evolve'))
    if len(evolve_functions) != 1:
        raise ValueError('Expected 1 function decorated with `@equation.evolve`.')
    
    return evolve_functions[0], run_functions[0]


def main(
    specification: str,
    inputs: Sequence[Any],
    config: config_lib.Config,
    max_sample_nums: int | None,
    class_config: config_lib.ClassConfig,
    **kwargs
):
    """
    Launch a simplified LLMSR experiment using SmolAgents.
    
    Args:
        specification: The boilerplate code template for the problem
        inputs: The data instances for the problem
        config: Configuration object
        max_sample_nums: Maximum samples to generate (None = unlimited)
        class_config: Class configuration (sandbox_class still used)
        **kwargs: Additional arguments (log_dir, etc.)
    """
    # Extract function names from specification
    function_to_evolve, function_to_run = _extract_function_names(specification)
    template = code_manipulation.text_to_program(specification)
    
    # Initialize experience buffer (multi-island evolutionary algorithm)
    database = buffer.ExperienceBuffer(
        config.experience_buffer,
        template,
        function_to_evolve
    )
    
    # Setup profiler
    log_dir = kwargs.get('log_dir', None)
    profiler = profile.Profiler(log_dir) if log_dir else None
    
    # Create evaluators (still use the original evaluator with sandbox)
    evaluators = []
    for _ in range(config.num_evaluators):
        evaluators.append(evaluator.Evaluator(
            database,
            template,
            function_to_evolve,
            function_to_run,
            inputs,
            timeout_seconds=config.evaluate_timeout_seconds,
            sandbox_class=class_config.sandbox_class
        ))
    
    # Evaluate initial template
    initial = template.get_function(function_to_evolve).body
    evaluators[0].analyse(
        initial,
        island_id=None,
        version_generated=None,
        profiler=profiler
    )
    
    # Initialize SmolAgents model
    model = UnifiedModel(
        use_api=config.use_api,
        api_model=config.api_model,
        api_type=config.api_type,
        local_model_id=kwargs.get('local_model_id', None),
        temperature=0.8,
        max_new_tokens=512
    )
    
    # Create SmolAgents-based samplers
    samplers = []
    for _ in range(config.num_samplers):
        samplers.append(SmolAgentsSampler(
            database=database,
            evaluators=evaluators,
            model=model,
            samples_per_prompt=config.samples_per_prompt,
            max_sample_nums=max_sample_nums,
            use_planning=kwargs.get('use_planning', False),
            planning_interval=kwargs.get('planning_interval', 3)
        ))
    
    # Run sampling loop
    # Note: In production, this could be parallelized
    for sampler_instance in samplers:
        sampler_instance.sample(profiler=profiler)

