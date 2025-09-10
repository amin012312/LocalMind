"""
LocalMind Model Engine

Core engine for running quantized language models offline with resource optimization.
Implements the LIVE-OFFLINE paradigm with automatic model selection and quantization.
"""

import logging
import torch
import gc
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, 
        BitsAndBytesConfig, GenerationConfig
    )
    from accelerate import Accelerator
except ImportError as e:
    logging.error(f"Required transformers/accelerate not installed: {e}")
    raise

from .loader import ModelLoader
from .optimizer import ModelOptimizer

# Import GPT4All engine as fallback
try:
    from .gpt4all_engine import GPT4AllEngine
    GPT4ALL_AVAILABLE = True
except ImportError:
    GPT4AllEngine = None
    GPT4ALL_AVAILABLE = False

class ModelEngine:
    """
    Core model engine for LocalMind's LIVE-OFFLINE operation.
    
    Features:
    - Automatic resource detection and optimization
    - Quantization support (4-bit, 8-bit) 
    - Multiple model backends
    - Memory-efficient loading
    - Offline-only operation
    """
    
    def __init__(self, config: Dict[str, Any], resource_manager=None):
        self.config = config
        self.resource_manager = resource_manager
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.tokenizer = None
        self.model = None
        self.accelerator = None
        self.loader = ModelLoader(config)
        self.optimizer = ModelOptimizer(config, resource_manager)
        
        # GPT4All fallback engine
        self.gpt4all_engine = None
        if GPT4ALL_AVAILABLE:
            self.gpt4all_engine = GPT4AllEngine(config)
            self.logger.info("GPT4All fallback engine available")
            # Mark as loaded if Simple AI is available as fallback
            if hasattr(self.gpt4all_engine, 'simple_ai') and self.gpt4all_engine.simple_ai:
                self.is_loaded = True
                self.current_model_name = "simple_ai"
                self.logger.info("Simple AI immediately available")
        
        # Model state
        self.current_model_name = None
        self.is_loaded = False
        self.device = self._determine_device()
        
        # Generation configuration
        self.generation_config = self._create_generation_config()
        
        self.logger.info("ModelEngine initialized for LIVE-OFFLINE operation")
    
    def _determine_device(self) -> str:
        """Determine the best device for model execution."""
        if torch.cuda.is_available() and self.config['resources']['gpu']['enabled']:
            device = f"cuda:{self.config['resources']['gpu']['device_id']}"
            self.logger.info(f"GPU detected: {device}")
            return device
        else:
            self.logger.info("Using CPU for model execution")
            return "cpu"
    
    def _create_generation_config(self) -> GenerationConfig:
        """Create generation configuration from config."""
        gen_config = self.config['model']['generation']
        return GenerationConfig(
            max_new_tokens=gen_config['max_new_tokens'],
            temperature=gen_config['temperature'],
            top_p=gen_config['top_p'],
            top_k=gen_config['top_k'],
            do_sample=gen_config['do_sample'],
            repetition_penalty=gen_config['repetition_penalty'],
            pad_token_id=None,  # Will be set after tokenizer loading
            eos_token_id=None   # Will be set after tokenizer loading
        )
    
    def load_model(self, model_name: Optional[str] = None) -> bool:
        """
        Load model with automatic resource optimization.
        First tries to load transformer models, falls back to GPT4All.
        
        Args:
            model_name: Specific model to load, or None for auto-selection
            
        Returns:
            bool: Success status
        """
        try:
            # Try to load transformer models first
            success = self._load_transformer_model(model_name)
            if success:
                return True
            
            # Fall back to GPT4All if available
            if self.gpt4all_engine:
                self.logger.info("Falling back to GPT4All engine")
                success = self.gpt4all_engine.load_model()
                if success:
                    self.is_loaded = True
                    self.current_model_name = "gpt4all"
                    self.logger.info("GPT4All model loaded successfully")
                    return True
                
                # If GPT4All fails but Simple AI is available, use it
                if hasattr(self.gpt4all_engine, 'simple_ai') and self.gpt4all_engine.simple_ai:
                    self.is_loaded = True
                    self.current_model_name = "simple_ai"
                    self.logger.info("Using Simple AI as fallback")
                    return True
            
            self.logger.error("Failed to load any model")
            return False
            
        except Exception as e:
            self.logger.error(f"Model loading failed: {e}")
            return False
    
    def _load_transformer_model(self, model_name: Optional[str] = None) -> bool:
        """Load transformer-based models."""
        try:
            # Determine model to load
            if model_name is None:
                model_name = self._select_optimal_model()
            
            self.logger.info(f"Loading transformer model: {model_name}")
            
            # Clear previous model if loaded
            if self.is_loaded:
                self.unload_model()
            
            # Load tokenizer first
            self.tokenizer = self.loader.load_tokenizer(model_name)
            if self.tokenizer is None:
                self.logger.warning("Failed to load tokenizer")
                return False
            
            # Load model with quantization
            self.model = self.loader.load_model(model_name, self.device)
            if self.model is None:
                self.logger.warning("Failed to load transformer model")
                return False
            
            # Setup generation config with tokenizer info
            self.generation_config.pad_token_id = self.tokenizer.pad_token_id
            self.generation_config.eos_token_id = self.tokenizer.eos_token_id
            
            # Apply optimizations
            self.model = self.optimizer.optimize_model(self.model)
            
            # Update state
            self.current_model_name = model_name
            self.is_loaded = True
            
            self.logger.info(f"Transformer model {model_name} loaded successfully")
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to load transformer model: {e}")
            return False
    
    def _select_optimal_model(self) -> str:
        """Select optimal model based on available resources."""
        if self.config['model']['default_model'] != 'auto':
            return self.config['model']['default_model']
        
        # Auto-select based on available resources
        if self.resource_manager:
            available_ram = self.resource_manager.get_available_ram_gb()
            has_gpu = self.resource_manager.has_gpu()
            
            if available_ram >= 16 and has_gpu:
                return "mistral-7b-instruct-v0.1"
            elif available_ram >= 12:
                return "llama-2-7b-chat"
            else:
                return "mistral-7b-instruct-v0.1"  # Heavily quantized
        
        # Fallback to default
        return "mistral-7b-instruct-v0.1"
    
    def generate_response(self, prompt: str, max_length: Optional[int] = None) -> Optional[str]:
        """
        Generate response from the loaded model.
        
        Args:
            prompt: Input prompt
            max_length: Maximum response length
            
        Returns:
            Generated response or None if failed
        """
        if not self.is_loaded:
            self.logger.error("No model loaded")
            return None
        
        try:
            # Use GPT4All engine (including Simple AI fallback)
            if (self.current_model_name == "gpt4all" or self.current_model_name == "simple_ai") and self.gpt4all_engine:
                max_tokens = max_length if max_length else 512
                return self.gpt4all_engine.generate_response(prompt, max_tokens)
            
            # Use transformer model
            if self.tokenizer and self.model:
                # Tokenize input
                inputs = self.tokenizer(
                    prompt, 
                    return_tensors="pt", 
                    padding=True, 
                    truncation=True,
                    max_length=self.config['domains']['general']['max_context_length']
                ).to(self.device)
                
                # Generate response
                with torch.no_grad():
                    generation_config = self.generation_config
                    if max_length:
                        generation_config.max_new_tokens = min(max_length, generation_config.max_new_tokens)
                    
                    outputs = self.model.generate(
                        **inputs,
                        generation_config=generation_config,
                        use_cache=True
                    )
                
                # Decode response
                generated_tokens = outputs[0][inputs['input_ids'].shape[1]:]
                response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
                
                # Clean up tensors
                del inputs, outputs, generated_tokens
                if self.device.startswith('cuda'):
                    torch.cuda.empty_cache()
                gc.collect()
                
                return response.strip()
            
            self.logger.error("No valid model available for generation")
            return None
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            return None
    
    def generate_streaming_response(self, prompt: str, callback=None):
        """
        Generate streaming response (for future implementation).
        
        Args:
            prompt: Input prompt
            callback: Callback function for streaming tokens
        """
        # Placeholder for streaming implementation
        response = self.generate_response(prompt)
        if callback and response:
            callback(response)
        return response
    
    def unload_model(self):
        """Unload current model to free memory."""
        if self.is_loaded:
            self.logger.info("Unloading model...")
            
            del self.model
            del self.tokenizer
            
            if self.device.startswith('cuda'):
                torch.cuda.empty_cache()
            gc.collect()
            
            self.model = None
            self.tokenizer = None
            self.is_loaded = False
            self.current_model_name = None
            
            self.logger.info("Model unloaded")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the currently loaded model."""
        if not self.is_loaded:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "model_name": self.current_model_name,
            "device": self.device,
            "quantization": self.config['model']['quantization'],
            "memory_usage": self._get_memory_usage()
        }
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage."""
        memory_info = {}
        
        if self.device.startswith('cuda'):
            memory_info['gpu_allocated'] = torch.cuda.memory_allocated() / 1024**3
            memory_info['gpu_cached'] = torch.cuda.memory_reserved() / 1024**3
        
        # CPU memory would require psutil
        return memory_info
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the model engine."""
        status = {
            "engine_status": "healthy" if self.is_loaded else "no_model_loaded",
            "model_loaded": self.is_loaded,
            "device": self.device,
            "memory_info": self._get_memory_usage()
        }
        
        # Test generation if model is loaded
        if self.is_loaded:
            try:
                test_response = self.generate_response("Hello")
                status["generation_test"] = "passed" if test_response else "failed"
            except Exception as e:
                status["generation_test"] = f"failed: {e}"
        
        return status
    
    def __del__(self):
        """Cleanup when engine is destroyed."""
        if hasattr(self, 'is_loaded') and self.is_loaded:
            self.unload_model()
