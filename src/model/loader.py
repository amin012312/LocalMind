"""
LocalMind Model Loader

Handles loading of quantized models with resource-adaptive configuration.
Ensures all model loading happens offline with no external dependencies.
"""

import logging
import torch
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM,
        BitsAndBytesConfig
    )
except ImportError as e:
    logging.error(f"Transformers library not available: {e}")
    raise

class ModelLoader:
    """
    Model loader for LocalMind's LIVE-OFFLINE operation.
    
    Features:
    - Offline model loading from local cache
    - Automatic quantization configuration
    - Resource-adaptive model selection
    - Security-conscious loading (no remote code execution)
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.models_dir = Path("data/models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Model registry with offline paths
        self.model_registry = {
            "mistral-7b-instruct-v0.1": {
                "path": self.models_dir / "mistral-7b-instruct-v0.1",
                "tokenizer_path": self.models_dir / "mistral-7b-instruct-v0.1",
                "size_gb": 7,
                "min_ram_gb": 8,
                "quantizable": True
            },
            "llama-2-7b-chat": {
                "path": self.models_dir / "llama-2-7b-chat", 
                "tokenizer_path": self.models_dir / "llama-2-7b-chat",
                "size_gb": 7,
                "min_ram_gb": 8,
                "quantizable": True
            }
        }
        
        self.logger.info("ModelLoader initialized for offline operation")
    
    def load_tokenizer(self, model_name: str) -> Optional[Any]:
        """
        Load tokenizer for the specified model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Loaded tokenizer or None if failed
        """
        try:
            if model_name not in self.model_registry:
                self.logger.error(f"Unknown model: {model_name}")
                return None
            
            model_info = self.model_registry[model_name]
            tokenizer_path = model_info["tokenizer_path"]
            
            # Try to load from local path first
            if tokenizer_path.exists():
                self.logger.info(f"Loading tokenizer from local path: {tokenizer_path}")
                tokenizer = AutoTokenizer.from_pretrained(
                    str(tokenizer_path),
                    local_files_only=True,
                    trust_remote_code=False  # Security: never execute remote code
                )
            else:
                # Fallback to model name (for initial download/cache)
                self.logger.info(f"Loading tokenizer for model: {model_name}")
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=False,
                    cache_dir=str(self.models_dir)
                )
                
                # Save for future offline use
                tokenizer.save_pretrained(str(tokenizer_path))
                self.logger.info(f"Tokenizer saved to: {tokenizer_path}")
            
            # Ensure pad token is set
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            self.logger.info(f"Tokenizer loaded successfully: {model_name}")
            return tokenizer
            
        except Exception as e:
            self.logger.error(f"Failed to load tokenizer for {model_name}: {e}")
            return None
    
    def load_model(self, model_name: str, device: str) -> Optional[Any]:
        """
        Load model with quantization configuration.
        
        Args:
            model_name: Name of the model to load
            device: Target device (cpu/cuda)
            
        Returns:
            Loaded model or None if failed
        """
        try:
            if model_name not in self.model_registry:
                self.logger.error(f"Unknown model: {model_name}")
                return None
            
            model_info = self.model_registry[model_name]
            model_path = model_info["path"]
            
            # Configure quantization
            quantization_config = self._create_quantization_config()
            
            # Configure model loading parameters
            model_kwargs = {
                "trust_remote_code": False,  # Security: never execute remote code
                "torch_dtype": torch.float16 if device.startswith('cuda') else torch.float32,
                "low_cpu_mem_usage": self.config['model']['loading']['low_cpu_mem_usage'],
                "device_map": self._get_device_map(device)
            }
            
            # Add quantization if enabled and on GPU
            if (quantization_config is not None and 
                device.startswith('cuda') and 
                model_info["quantizable"]):
                model_kwargs["quantization_config"] = quantization_config
                self.logger.info("Quantization enabled for GPU loading")
            
            # Try to load from local path first
            if model_path.exists():
                self.logger.info(f"Loading model from local path: {model_path}")
                model = AutoModelForCausalLM.from_pretrained(
                    str(model_path),
                    local_files_only=True,
                    **model_kwargs
                )
            else:
                # Fallback to model name (for initial download/cache)
                self.logger.info(f"Loading model: {model_name}")
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    cache_dir=str(self.models_dir),
                    **model_kwargs
                )
                
                # Save for future offline use
                model.save_pretrained(str(model_path))
                self.logger.info(f"Model saved to: {model_path}")
            
            self.logger.info(f"Model loaded successfully: {model_name}")
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {e}")
            return None
    
    def _create_quantization_config(self) -> Optional[BitsAndBytesConfig]:
        """Create quantization configuration based on settings."""
        quant_config = self.config['model']['quantization']
        
        if not quant_config['enabled']:
            return None
        
        try:
            if quant_config['load_in_4bit']:
                return BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=getattr(torch, quant_config['bnb_4bit_compute_dtype']),
                    bnb_4bit_use_double_quant=quant_config['bnb_4bit_use_double_quant'],
                    bnb_4bit_quant_type="nf4"
                )
            elif quant_config['load_in_8bit']:
                return BitsAndBytesConfig(
                    load_in_8bit=True
                )
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to create quantization config: {e}")
            return None
    
    def _get_device_map(self, device: str) -> str:
        """Get device map configuration."""
        device_map_setting = self.config['model']['loading']['device_map']
        
        if device_map_setting == 'auto':
            return 'auto'
        elif device.startswith('cuda'):
            return device
        else:
            return 'cpu'
    
    def list_available_models(self) -> Dict[str, Any]:
        """List all available models and their status."""
        models_status = {}
        
        for model_name, model_info in self.model_registry.items():
            status = {
                "size_gb": model_info["size_gb"],
                "min_ram_gb": model_info["min_ram_gb"],
                "quantizable": model_info["quantizable"],
                "downloaded": model_info["path"].exists(),
                "tokenizer_available": model_info["tokenizer_path"].exists()
            }
            models_status[model_name] = status
        
        return models_status
    
    def download_model(self, model_name: str) -> bool:
        """
        Download model for offline use.
        
        Args:
            model_name: Name of the model to download
            
        Returns:
            Success status
        """
        if model_name not in self.model_registry:
            self.logger.error(f"Unknown model: {model_name}")
            return False
        
        try:
            self.logger.info(f"Downloading model for offline use: {model_name}")
            
            # Load and save tokenizer
            tokenizer = self.load_tokenizer(model_name)
            if tokenizer is None:
                return False
            
            # Load and save model (this will trigger download if not cached)
            model = self.load_model(model_name, "cpu")
            if model is None:
                return False
            
            # Clean up memory
            del model, tokenizer
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
            self.logger.info(f"Model {model_name} downloaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download model {model_name}: {e}")
            return False
    
    def get_model_requirements(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get resource requirements for a specific model."""
        if model_name not in self.model_registry:
            return None
        
        model_info = self.model_registry[model_name]
        quant_config = self.config['model']['quantization']
        
        # Estimate memory requirements based on quantization
        base_size = model_info["size_gb"]
        if quant_config['enabled'] and quant_config['load_in_4bit']:
            estimated_size = base_size * 0.25  # 4-bit quantization
        elif quant_config['enabled'] and quant_config['load_in_8bit']:
            estimated_size = base_size * 0.5   # 8-bit quantization
        else:
            estimated_size = base_size          # Full precision
        
        return {
            "model_size_gb": base_size,
            "estimated_memory_gb": estimated_size,
            "min_ram_gb": model_info["min_ram_gb"],
            "quantizable": model_info["quantizable"],
            "quantization_enabled": quant_config['enabled']
        }
