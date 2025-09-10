"""
GPT4All Model Engine for LocalMind - Updated Version

Enhanced model engine using GPT4All for better offline AI responses.
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from gpt4all import GPT4All
except ImportError:
    GPT4All = None
    logging.error("GPT4All not available")

class GPT4AllEngine:
    """
    GPT4All-based model engine for LocalMind.
    
    Provides better AI responses using local GPT4All models.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.is_loaded = False
        
        # Model directory
        self.models_dir = Path("data/models/gpt4all")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Available models (verified working from GPT4All.list_models())
        self.available_models = {
            "llama-3.2-1b": {
                "filename": "Llama-3.2-1B-Instruct-Q4_0.gguf",
                "size_mb": 773,
                "description": "Small, fast Llama 3.2 model - good for basic tasks"
            },
            "llama-3.2-3b": {
                "filename": "Llama-3.2-3B-Instruct-Q4_0.gguf", 
                "size_mb": 1921,
                "description": "Medium Llama 3.2 model - balanced performance"
            },
            "mistral-7b": {
                "filename": "mistral-7b-instruct-v0.1.Q4_0.gguf",
                "size_mb": 4108,
                "description": "Mistral 7B - strong instruction following"
            },
            "nous-hermes": {
                "filename": "Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf",
                "size_mb": 4108,
                "description": "Nous Hermes 2 - good overall chat model"
            }
        }
        
        self.logger.info("GPT4All engine initialized")
    
    def load_model(self, model_name: Optional[str] = None) -> bool:
        """Load GPT4All model."""
        if not GPT4All:
            self.logger.error("GPT4All not available")
            return False
        
        try:
            # Select model - start with smallest for fast loading
            if model_name is None:
                model_name = "llama-3.2-1b"  # Default lightweight model
            
            if model_name not in self.available_models:
                self.logger.error(f"Unknown model: {model_name}")
                return False
            
            model_info = self.available_models[model_name]
            
            self.logger.info(f"Loading GPT4All model: {model_name}")
            self.logger.info(f"Model: {model_info['filename']}")
            self.logger.info(f"Size: {model_info['size_mb']} MB")
            
            # Load model (will download if not available)
            self.model = GPT4All(
                model_name=model_info["filename"],
                model_path=str(self.models_dir),
                allow_download=True,
                device='cpu'  # Use CPU for compatibility
            )
            
            self.is_loaded = True
            self.logger.info(f"GPT4All model {model_name} loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load GPT4All model: {e}")
            return False
    
    def generate_response(self, prompt: str, max_tokens: int = 512) -> Optional[str]:
        """Generate response using GPT4All."""
        if not self.is_loaded or not self.model:
            self.logger.error("No GPT4All model loaded")
            return None
        
        try:
            # Generate response with conversation context
            with self.model.chat_session():
                response = self.model.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temp=0.7,
                    top_p=0.9,
                    repeat_penalty=1.1,
                    streaming=False
                )
            
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"GPT4All generation failed: {e}")
            return None
    
    def unload_model(self):
        """Unload the current model."""
        if self.model:
            # GPT4All doesn't have explicit unload, just clear reference
            self.model = None
            self.is_loaded = False
            self.logger.info("GPT4All model unloaded")
