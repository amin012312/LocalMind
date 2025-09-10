"""
LocalMind Resource Manager

Monitors and optimizes system resources for efficient LIVE-OFFLINE operation.
Provides hardware detection, memory management, and performance optimization.
"""

import logging
import platform
import os
from typing import Dict, Any, Optional, Tuple

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - limited resource monitoring")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False

class ResourceManager:
    """
    Resource management system for LocalMind.
    
    Features:
    - Hardware detection and monitoring
    - Memory usage optimization
    - Performance recommendations
    - Resource-adaptive configurations
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Resource configuration
        self.auto_detect = config['resources']['auto_detect']
        self.max_ram_usage = config['resources']['memory']['max_ram_usage_percent']
        
        # System information
        self.system_info = self._detect_system_info()
        self.gpu_info = self._detect_gpu_info()
        
        # Resource limits
        self.memory_limits = self._calculate_memory_limits()
        
        self.logger.info("ResourceManager initialized")
        self.logger.info(f"System: {self.system_info['os']} {self.system_info['architecture']}")
        self.logger.info(f"CPU: {self.system_info['cpu_count']} cores")
        self.logger.info(f"RAM: {self.system_info['total_memory_gb']:.1f} GB")
        
        if self.gpu_info['available']:
            self.logger.info(f"GPU: {self.gpu_info['name']}")
    
    def _detect_system_info(self) -> Dict[str, Any]:
        """Detect basic system information."""
        info = {
            'os': platform.system(),
            'os_version': platform.version(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'cpu_count': os.cpu_count() or 1,
            'total_memory_gb': 8.0  # Default fallback
        }
        
        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                info['total_memory_gb'] = memory.total / (1024**3)
                info['cpu_freq'] = psutil.cpu_freq()
                info['cpu_model'] = platform.processor()
            except Exception as e:
                self.logger.warning(f"Failed to get detailed system info: {e}")
        
        return info
    
    def _detect_gpu_info(self) -> Dict[str, Any]:
        """Detect GPU information."""
        gpu_info = {
            'available': False,
            'count': 0,
            'name': None,
            'memory_total': 0,
            'cuda_available': False
        }
        
        # Check PyTorch CUDA availability
        if TORCH_AVAILABLE:
            gpu_info['cuda_available'] = torch.cuda.is_available()
            if gpu_info['cuda_available']:
                gpu_info['available'] = True
                gpu_info['count'] = torch.cuda.device_count()
                gpu_info['name'] = torch.cuda.get_device_name(0)
                gpu_info['memory_total'] = torch.cuda.get_device_properties(0).total_memory
        
        # Try GPUtil for additional info
        if GPUTIL_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_info['available'] = True
                    gpu_info['count'] = len(gpus)
                    gpu_info['name'] = gpu.name
                    gpu_info['memory_total'] = gpu.memoryTotal * 1024 * 1024  # Convert to bytes
                    gpu_info['driver_version'] = gpu.driver
            except Exception as e:
                self.logger.warning(f"GPUtil detection failed: {e}")
        
        return gpu_info
    
    def _calculate_memory_limits(self) -> Dict[str, float]:
        """Calculate memory usage limits based on system resources."""
        total_ram = self.system_info['total_memory_gb']
        
        # Calculate limits based on total RAM
        if total_ram >= 32:
            # High-end system
            limits = {
                'model_memory_gb': min(16, total_ram * 0.6),
                'vector_db_memory_gb': 4,
                'system_reserved_gb': 8
            }
        elif total_ram >= 16:
            # Mid-range system
            limits = {
                'model_memory_gb': min(8, total_ram * 0.5),
                'vector_db_memory_gb': 2,
                'system_reserved_gb': 4
            }
        else:
            # Low-end system
            limits = {
                'model_memory_gb': min(4, total_ram * 0.4),
                'vector_db_memory_gb': 1,
                'system_reserved_gb': 2
            }
        
        return limits
    
    def get_available_ram_gb(self) -> float:
        """Get currently available RAM in GB."""
        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                return memory.available / (1024**3)
            except Exception as e:
                self.logger.error(f"Failed to get available RAM: {e}")
        
        # Fallback estimate
        return self.system_info['total_memory_gb'] * 0.6
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        usage = {}
        
        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                usage['total_gb'] = memory.total / (1024**3)
                usage['available_gb'] = memory.available / (1024**3)
                usage['used_gb'] = memory.used / (1024**3)
                usage['usage_percent'] = memory.percent
            except Exception as e:
                self.logger.error(f"Failed to get memory usage: {e}")
        
        return usage
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        if PSUTIL_AVAILABLE:
            try:
                return psutil.cpu_percent(interval=1)
            except Exception as e:
                self.logger.error(f"Failed to get CPU usage: {e}")
        
        return 0.0
    
    def get_gpu_usage(self) -> Dict[str, Any]:
        """Get current GPU usage statistics."""
        gpu_usage = {
            'available': self.gpu_info['available'],
            'memory_used_gb': 0,
            'memory_total_gb': 0,
            'utilization_percent': 0
        }
        
        if not self.gpu_info['available']:
            return gpu_usage
        
        # PyTorch GPU memory
        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                gpu_usage['memory_used_gb'] = torch.cuda.memory_allocated() / (1024**3)
                gpu_usage['memory_total_gb'] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            except Exception as e:
                self.logger.error(f"Failed to get PyTorch GPU usage: {e}")
        
        # GPUtil information
        if GPUTIL_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_usage['memory_used_gb'] = gpu.memoryUsed / 1024
                    gpu_usage['memory_total_gb'] = gpu.memoryTotal / 1024
                    gpu_usage['utilization_percent'] = gpu.load * 100
            except Exception as e:
                self.logger.error(f"Failed to get GPUtil GPU usage: {e}")
        
        return gpu_usage
    
    def has_gpu(self) -> bool:
        """Check if GPU is available for computation."""
        return self.gpu_info['available'] and self.config['resources']['gpu']['enabled']
    
    def recommend_model_config(self) -> Dict[str, Any]:
        """Recommend model configuration based on available resources."""
        recommendations = {}
        
        available_ram = self.get_available_ram_gb()
        has_gpu = self.has_gpu()
        
        # Model selection recommendation
        if available_ram >= 16 and has_gpu:
            recommendations['model'] = 'mistral-7b-instruct-v0.1'
            recommendations['quantization'] = '4bit'
            recommendations['device'] = 'cuda'
        elif available_ram >= 12:
            recommendations['model'] = 'llama-2-7b-chat'
            recommendations['quantization'] = '8bit'
            recommendations['device'] = 'cuda' if has_gpu else 'cpu'
        elif available_ram >= 8:
            recommendations['model'] = 'mistral-7b-instruct-v0.1'
            recommendations['quantization'] = '4bit'
            recommendations['device'] = 'cpu'
        else:
            recommendations['model'] = 'distilled-model'  # Would need smaller model
            recommendations['quantization'] = '4bit'
            recommendations['device'] = 'cpu'
            recommendations['warning'] = 'Limited RAM - consider upgrading hardware'
        
        # Memory allocation recommendations
        recommendations['max_new_tokens'] = min(512, int(available_ram * 50))
        recommendations['batch_size'] = 1  # Keep minimal for memory efficiency
        
        return recommendations
    
    def check_resource_health(self) -> Dict[str, Any]:
        """Check overall system resource health."""
        health = {
            'status': 'healthy',
            'warnings': [],
            'recommendations': []
        }
        
        # Memory health
        memory_usage = self.get_memory_usage()
        if memory_usage.get('usage_percent', 0) > 90:
            health['status'] = 'warning'
            health['warnings'].append('High memory usage detected')
            health['recommendations'].append('Consider closing other applications')
        
        # CPU health
        cpu_usage = self.get_cpu_usage()
        if cpu_usage > 90:
            health['status'] = 'warning'
            health['warnings'].append('High CPU usage detected')
            health['recommendations'].append('System may be under heavy load')
        
        # GPU health (if available)
        if self.has_gpu():
            gpu_usage = self.get_gpu_usage()
            gpu_memory_percent = (gpu_usage['memory_used_gb'] / gpu_usage['memory_total_gb']) * 100
            if gpu_memory_percent > 90:
                health['status'] = 'warning'
                health['warnings'].append('High GPU memory usage')
                health['recommendations'].append('Consider reducing model size or batch size')
        
        # Storage health
        available_storage = self._get_available_storage_gb()
        if available_storage < 5:
            health['status'] = 'critical'
            health['warnings'].append('Low disk space')
            health['recommendations'].append('Free up disk space for optimal operation')
        
        return health
    
    def _get_available_storage_gb(self) -> float:
        """Get available storage space in GB."""
        try:
            if PSUTIL_AVAILABLE:
                usage = psutil.disk_usage('.')
                return usage.free / (1024**3)
            else:
                # Fallback for systems without psutil
                import shutil
                total, used, free = shutil.disk_usage('.')
                return free / (1024**3)
        except Exception as e:
            self.logger.error(f"Failed to get storage info: {e}")
            return 50.0  # Assume 50GB free as fallback
    
    def optimize_for_current_resources(self) -> Dict[str, Any]:
        """Get optimization settings for current resource state."""
        optimizations = {}
        
        memory_usage = self.get_memory_usage()
        cpu_usage = self.get_cpu_usage()
        
        # Memory optimizations
        if memory_usage.get('usage_percent', 0) > 80:
            optimizations['aggressive_cleanup'] = True
            optimizations['reduce_cache_size'] = True
            optimizations['limit_concurrent_operations'] = True
        
        # CPU optimizations
        if cpu_usage > 80:
            optimizations['reduce_cpu_threads'] = True
            optimizations['lower_generation_speed'] = True
        
        # GPU optimizations
        if self.has_gpu():
            gpu_usage = self.get_gpu_usage()
            gpu_memory_percent = (gpu_usage['memory_used_gb'] / gpu_usage['memory_total_gb']) * 100
            if gpu_memory_percent > 80:
                optimizations['reduce_gpu_batch_size'] = True
                optimizations['enable_cpu_offload'] = True
        
        return optimizations
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get comprehensive system resource summary."""
        summary = {
            'system_info': self.system_info,
            'gpu_info': self.gpu_info,
            'current_usage': {
                'memory': self.get_memory_usage(),
                'cpu_percent': self.get_cpu_usage(),
                'gpu': self.get_gpu_usage() if self.has_gpu() else None
            },
            'limits': self.memory_limits,
            'health': self.check_resource_health(),
            'recommendations': self.recommend_model_config()
        }
        
        return summary
