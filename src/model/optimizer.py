"""
LocalMind Model Optimizer

Runtime optimization for loaded models including memory management,
performance tuning, and resource-adaptive configurations.
"""

import logging
import torch
import gc
from typing import Any, Dict, Optional

class ModelOptimizer:
    """
    Model optimizer for LocalMind's efficient operation.
    
    Features:
    - Runtime model optimization
    - Memory management
    - Performance tuning based on hardware
    - Resource-adaptive configurations
    """
    
    def __init__(self, config: Dict[str, Any], resource_manager=None):
        self.config = config
        self.resource_manager = resource_manager
        self.logger = logging.getLogger(__name__)
        
        # Optimization settings
        self.optimization_level = config['resources']['cpu']['optimization_level']
        self.max_ram_usage = config['resources']['memory']['max_ram_usage_percent']
        
        self.logger.info("ModelOptimizer initialized")
    
    def optimize_model(self, model: Any) -> Any:
        """
        Apply optimizations to the loaded model.
        
        Args:
            model: The loaded model to optimize
            
        Returns:
            Optimized model
        """
        try:
            self.logger.info("Applying model optimizations...")
            
            # Set model to evaluation mode
            model.eval()
            
            # Apply memory optimizations
            model = self._apply_memory_optimizations(model)
            
            # Apply performance optimizations  
            model = self._apply_performance_optimizations(model)
            
            # Apply device-specific optimizations
            model = self._apply_device_optimizations(model)
            
            self.logger.info("Model optimization completed")
            return model
            
        except Exception as e:
            self.logger.error(f"Model optimization failed: {e}")
            return model  # Return original model if optimization fails
    
    def _apply_memory_optimizations(self, model: Any) -> Any:
        """Apply memory-specific optimizations."""
        try:
            # Enable gradient checkpointing if configured
            if self.config['performance']['gradient_checkpointing']:
                if hasattr(model, 'gradient_checkpointing_enable'):
                    model.gradient_checkpointing_enable()
                    self.logger.info("Gradient checkpointing enabled")
            
            # CPU offloading if enabled
            if self.config['resources']['memory']['enable_cpu_offload']:
                # This would implement CPU offloading for large models
                self.logger.info("CPU offloading considered")
            
            return model
            
        except Exception as e:
            self.logger.error(f"Memory optimization failed: {e}")
            return model
    
    def _apply_performance_optimizations(self, model: Any) -> Any:
        """Apply performance optimizations based on hardware."""
        try:
            # Model compilation (optional, can be unstable)
            if self.config['performance']['compile_model']:
                try:
                    if hasattr(torch, 'compile'):
                        model = torch.compile(model)
                        self.logger.info("Model compilation enabled")
                except Exception as e:
                    self.logger.warning(f"Model compilation failed: {e}")
            
            # Flash attention (if supported)
            if self.config['performance']['use_flash_attention']:
                # This would enable flash attention if available
                self.logger.info("Flash attention considered")
            
            return model
            
        except Exception as e:
            self.logger.error(f"Performance optimization failed: {e}")
            return model
    
    def _apply_device_optimizations(self, model: Any) -> Any:
        """Apply device-specific optimizations."""
        try:
            device = next(model.parameters()).device
            
            if device.type == 'cuda':
                # GPU optimizations
                model = self._optimize_for_gpu(model)
            else:
                # CPU optimizations
                model = self._optimize_for_cpu(model)
            
            return model
            
        except Exception as e:
            self.logger.error(f"Device optimization failed: {e}")
            return model
    
    def _optimize_for_gpu(self, model: Any) -> Any:
        """Apply GPU-specific optimizations."""
        try:
            # Enable memory efficient attention
            if hasattr(model.config, 'use_memory_efficient_attention'):
                model.config.use_memory_efficient_attention = True
            
            # Set optimal GPU settings
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
            
            self.logger.info("GPU optimizations applied")
            return model
            
        except Exception as e:
            self.logger.error(f"GPU optimization failed: {e}")
            return model
    
    def _optimize_for_cpu(self, model: Any) -> Any:
        """Apply CPU-specific optimizations."""
        try:
            # Set optimal number of threads
            max_threads = self.config['resources']['cpu']['max_threads']
            if max_threads == 'auto':
                max_threads = torch.get_num_threads()
            
            torch.set_num_threads(int(max_threads))
            
            # Enable CPU-specific optimizations
            if hasattr(torch.backends, 'mkldnn'):
                torch.backends.mkldnn.enabled = True
            
            self.logger.info(f"CPU optimizations applied (threads: {max_threads})")
            return model
            
        except Exception as e:
            self.logger.error(f"CPU optimization failed: {e}")
            return model
    
    def cleanup_memory(self):
        """Perform memory cleanup."""
        try:
            gc.collect()
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            self.logger.debug("Memory cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Memory cleanup failed: {e}")
    
    def get_optimization_info(self) -> Dict[str, Any]:
        """Get information about current optimizations."""
        return {
            "optimization_level": self.optimization_level,
            "max_ram_usage_percent": self.max_ram_usage,
            "gradient_checkpointing": self.config['performance']['gradient_checkpointing'],
            "cpu_threads": torch.get_num_threads(),
            "cuda_available": torch.cuda.is_available(),
            "mkldnn_enabled": getattr(torch.backends, 'mkldnn', {}).get('enabled', False)
        }
    
    def monitor_resource_usage(self) -> Dict[str, Any]:
        """Monitor current resource usage."""
        usage_info = {}
        
        try:
            # CPU information
            usage_info['cpu_threads'] = torch.get_num_threads()
            
            # GPU information
            if torch.cuda.is_available():
                usage_info['gpu_memory_allocated'] = torch.cuda.memory_allocated() / 1024**3
                usage_info['gpu_memory_cached'] = torch.cuda.memory_reserved() / 1024**3
                usage_info['gpu_memory_total'] = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            # Memory information (if psutil available)
            if self.resource_manager:
                usage_info['system_ram_usage'] = self.resource_manager.get_memory_usage()
            
        except Exception as e:
            self.logger.error(f"Resource monitoring failed: {e}")
        
        return usage_info
    
    def adaptive_optimization(self, model: Any) -> Any:
        """
        Apply adaptive optimizations based on current resource usage.
        
        Args:
            model: Model to optimize
            
        Returns:
            Optimized model
        """
        try:
            usage = self.monitor_resource_usage()
            
            # Adaptive memory management
            if 'gpu_memory_allocated' in usage:
                gpu_usage_percent = (usage['gpu_memory_allocated'] / usage['gpu_memory_total']) * 100
                
                if gpu_usage_percent > 85:
                    self.logger.warning("High GPU memory usage, applying aggressive cleanup")
                    self.cleanup_memory()
                    
                    # Consider reducing batch size or other optimizations
                    if hasattr(model.generation_config, 'max_new_tokens'):
                        model.generation_config.max_new_tokens = min(
                            model.generation_config.max_new_tokens, 256
                        )
            
            # Adaptive CPU optimization
            if self.resource_manager:
                cpu_usage = self.resource_manager.get_cpu_usage()
                if cpu_usage > 90:
                    self.logger.warning("High CPU usage detected")
                    # Could implement CPU throttling or other adaptations
            
            return model
            
        except Exception as e:
            self.logger.error(f"Adaptive optimization failed: {e}")
            return model
    
    def optimize_for_inference(self, model: Any) -> Any:
        """
        Optimize model specifically for inference (not training).
        
        Args:
            model: Model to optimize
            
        Returns:
            Inference-optimized model
        """
        try:
            # Ensure model is in eval mode
            model.eval()
            
            # Disable gradients for inference
            for param in model.parameters():
                param.requires_grad = False
            
            # Apply inference-specific optimizations
            if hasattr(model, 'half') and torch.cuda.is_available():
                model = model.half()  # Use half precision on GPU
                self.logger.info("Half precision enabled for inference")
            
            self.logger.info("Inference optimizations applied")
            return model
            
        except Exception as e:
            self.logger.error(f"Inference optimization failed: {e}")
            return model
