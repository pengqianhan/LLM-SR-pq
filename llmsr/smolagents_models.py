"""
SmolAgents-based model wrappers that replace the custom LLM engine.
This module provides unified model access via SmolAgents abstractions.
"""
from __future__ import annotations

import os
from typing import Optional
from smolagents import InferenceClientModel, TransformersModel, LiteLLMModel


class UnifiedModel:
    """
    Unified model interface that wraps SmolAgents models.
    Replaces the custom LocalLLM and API-based sampling logic.
    """
    
    def __init__(
        self,
        use_api: bool = False,
        api_model: str = "gpt-3.5-turbo",
        api_type: str = "auto",
        local_model_id: Optional[str] = None,
        temperature: float = 0.8,
        max_new_tokens: int = 512,
        device_map: str = "auto"
    ):
        """
        Initialize a unified model wrapper.
        
        Args:
            use_api: If True, use API-based models (HF Inference, OpenAI, Gemini, etc.)
            api_model: Model identifier for API calls
            api_type: Type of API ('openai', 'gemini', 'auto')
            local_model_id: Model ID for local inference (if use_api=False)
            temperature: Sampling temperature
            max_new_tokens: Maximum tokens to generate
            device_map: Device mapping for local models
        """
        self.use_api = use_api
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        
        if use_api:
            self.model = self._initialize_api_model(api_model, api_type)
        else:
            self.model = self._initialize_local_model(
                local_model_id, max_new_tokens, device_map
            )
    
    def _initialize_api_model(self, api_model: str, api_type: str):
        """Initialize API-based model using SmolAgents."""
        # Determine API type
        if api_type == "auto":
            api_type = self._detect_api_type(api_model)
        
        if api_type == "gemini":
            # For Gemini, use LiteLLMModel which supports many providers
            api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('API_KEY')
            if not api_key:
                raise ValueError("Please set GEMINI_API_KEY or API_KEY environment variable")
            
            return LiteLLMModel(
                model_id=f"gemini/{api_model}",
                temperature=self.temperature,
                api_key=api_key
            )
        
        elif api_type == "openai":
            # For OpenAI and compatible APIs, use LiteLLMModel
            api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('API_KEY')
            return LiteLLMModel(
                model_id=api_model,
                temperature=self.temperature,
                api_key=api_key
            )
        
        else:
            # Default: use HuggingFace Inference API
            return InferenceClientModel(
                model_id=api_model,
                temperature=self.temperature
            )
    
    def _initialize_local_model(
        self, 
        model_id: Optional[str], 
        max_new_tokens: int, 
        device_map: str
    ):
        """Initialize local model using SmolAgents TransformersModel."""
        if model_id is None:
            model_id = "Qwen/Qwen2.5-Coder-32B-Instruct"  # Default
        
        return TransformersModel(
            model_id=model_id,
            max_new_tokens=max_new_tokens,
            device_map=device_map
        )
    
    def _detect_api_type(self, api_model: str) -> str:
        """Auto-detect API type from model name."""
        model_lower = api_model.lower()
        
        if 'gemini' in model_lower:
            return 'gemini'
        elif any(name in model_lower for name in ['gpt', 'chatgpt', 'davinci', 'curie']):
            return 'openai'
        else:
            return 'huggingface'
    
    def generate(self, prompt: str, num_samples: int = 1) -> list[str]:
        """
        Generate text completions from the model.
        
        Args:
            prompt: Input prompt text
            num_samples: Number of samples to generate
            
        Returns:
            List of generated text strings
        """
        samples = []
        
        for _ in range(num_samples):
            # Format as chat message for SmolAgents models
            messages = [{"role": "user", "content": prompt}]
            
            try:
                # SmolAgents models expect chat messages
                response = self.model(messages)
                samples.append(response)
            except Exception as e:
                print(f"Generation error: {e}")
                # Return empty string on error, filter later
                samples.append("")
        
        # Filter out empty responses
        samples = [s for s in samples if s.strip()]
        
        return samples

