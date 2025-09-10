#!/usr/bin/env python3
"""
LocalMind - LIVE-OFFLINE AI Assistant Setup Script

This setup script initializes LocalMind for offline operation including:
- Model download and quantization
- Knowledge base initialization
- Resource optimization configuration
- Security setup
"""

from setuptools import setup, find_packages
import os
import sys
import subprocess
import platform
from pathlib import Path

# Project metadata
PROJECT_NAME = "LocalMind"
VERSION = "1.0.0"
DESCRIPTION = "LIVE-OFFLINE AI Assistant for Education and Healthcare"
AUTHOR = "LocalMind Development Team"
LICENSE = "Apache 2.0"

# Minimum system requirements
MIN_PYTHON_VERSION = (3, 8)
MIN_RAM_GB = 8
RECOMMENDED_RAM_GB = 16
MIN_STORAGE_GB = 20

def check_system_requirements():
    """Check if system meets minimum requirements for LocalMind."""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"❌ Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ required, found {sys.version}")
        sys.exit(1)
    
    # Check available RAM
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024**3)
        if ram_gb < MIN_RAM_GB:
            print(f"⚠️  Warning: {ram_gb:.1f}GB RAM detected, {MIN_RAM_GB}GB minimum required")
            print("   LocalMind will use resource-constrained mode")
        elif ram_gb >= RECOMMENDED_RAM_GB:
            print(f"✅ {ram_gb:.1f}GB RAM detected - optimal for LocalMind")
        else:
            print(f"✅ {ram_gb:.1f}GB RAM detected - sufficient for LocalMind")
    except ImportError:
        print("⚠️  Could not check RAM - install psutil for full system check")
    
    # Check available storage
    try:
        disk_usage = os.statvfs('.')
        free_gb = (disk_usage.f_bavail * disk_usage.f_frsize) / (1024**3)
        if free_gb < MIN_STORAGE_GB:
            print(f"❌ {free_gb:.1f}GB free space, {MIN_STORAGE_GB}GB minimum required")
            sys.exit(1)
        else:
            print(f"✅ {free_gb:.1f}GB free space available")
    except AttributeError:
        # Windows doesn't have statvfs
        print("✅ Storage check skipped on Windows")
    
    print("✅ System requirements check complete\n")

def create_directory_structure():
    """Create necessary directories for LocalMind operation."""
    print("📁 Creating directory structure...")
    
    directories = [
        "data/knowledge/embeddings",
        "data/knowledge/documents", 
        "data/models/quantized",
        "data/user/profiles",
        "data/user/history",
        "logs",
        "cache"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   Created: {directory}")
    
    print("✅ Directory structure created\n")

def download_models():
    """Download and prepare offline models."""
    print("🤖 Setting up offline models...")
    
    # This would typically download models from Hugging Face
    # For demo purposes, we'll create placeholder files
    
    models_dir = Path("data/models")
    
    # Create model configuration files
    model_configs = {
        "mistral-7b-instruct-v0.1": {
            "size": "7B",
            "quantization": "4bit",
            "domains": ["general", "education", "healthcare"],
            "languages": ["en", "es", "fr", "pt", "ar"]
        },
        "llama-2-7b-chat": {
            "size": "7B", 
            "quantization": "8bit",
            "domains": ["general", "education"],
            "languages": ["en", "es", "zh"]
        }
    }
    
    for model_name, config in model_configs.items():
        config_path = models_dir / f"{model_name}.json"
        with open(config_path, 'w') as f:
            import json
            json.dump(config, f, indent=2)
        print(f"   Configured: {model_name}")
    
    print("✅ Model setup complete\n")

def initialize_knowledge_base():
    """Initialize the local knowledge base with essential content."""
    print("📚 Initializing knowledge base...")
    
    knowledge_dir = Path("data/knowledge")
    
    # Create sample knowledge base entries
    educational_content = {
        "mathematics": [
            "Basic arithmetic operations and properties",
            "Algebra fundamentals and equation solving",
            "Geometry principles and theorems",
            "Statistics and probability concepts"
        ],
        "science": [
            "Scientific method and inquiry",
            "Biology basics and human anatomy",
            "Chemistry fundamentals",
            "Physics principles and laws"
        ],
        "languages": [
            "Grammar rules and sentence structure",
            "Vocabulary building techniques",
            "Reading comprehension strategies",
            "Writing and communication skills"
        ]
    }
    
    healthcare_content = {
        "first_aid": [
            "Basic wound care and cleaning",
            "CPR and emergency response",
            "Recognition of common symptoms",
            "When to seek medical attention"
        ],
        "preventive_care": [
            "Hygiene and sanitation practices",
            "Nutrition and healthy eating",
            "Exercise and physical activity",
            "Mental health and stress management"
        ],
        "common_conditions": [
            "Cold and flu management",
            "Digestive health basics",
            "Skin care and common issues",
            "Pain management techniques"
        ]
    }
    
    # Save knowledge base content
    import json
    with open(knowledge_dir / "educational_base.json", 'w') as f:
        json.dump(educational_content, f, indent=2)
    
    with open(knowledge_dir / "healthcare_base.json", 'w') as f:
        json.dump(healthcare_content, f, indent=2)
    
    print("   Educational knowledge base: ✅")
    print("   Healthcare knowledge base: ✅")
    print("✅ Knowledge base initialization complete\n")

def configure_security():
    """Set up security and privacy configurations."""
    print("🔒 Configuring security settings...")
    
    # Create security configuration
    security_config = {
        "encryption": {
            "enabled": True,
            "algorithm": "AES-256",
            "key_derivation": "PBKDF2"
        },
        "privacy": {
            "data_retention_days": 30,
            "anonymize_logs": True,
            "local_only": True
        },
        "content_filtering": {
            "enabled": True,
            "strict_mode": True,
            "blocked_categories": ["adult", "violence", "harmful"]
        }
    }
    
    import json
    with open("data/user/security_config.json", 'w') as f:
        json.dump(security_config, f, indent=2)
    
    print("✅ Security configuration complete\n")

def main():
    """Main setup function."""
    print("=" * 60)
    print("🧠 LocalMind - LIVE-OFFLINE AI Assistant Setup")
    print("=" * 60)
    print()
    
    try:
        check_system_requirements()
        create_directory_structure()
        download_models()
        initialize_knowledge_base()
        configure_security()
        
        print("🎉 LocalMind setup complete!")
        print()
        print("Next steps:")
        print("1. Run: python src/app.py --cli (for command-line interface)")
        print("2. Run: python src/app.py --gui (for graphical interface)")
        print("3. Check config.yaml for customization options")
        print()
        print("LocalMind is now ready for LIVE-OFFLINE operation! 🚀")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("Please check the error and try again.")
        sys.exit(1)

if __name__ == "__main__":
    # Standard setuptools configuration
    setup(
        name=PROJECT_NAME,
        version=VERSION,
        description=DESCRIPTION,
        author=AUTHOR,
        license=LICENSE,
        packages=find_packages(),
        python_requires=f">={MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}",
        install_requires=[
            line.strip() for line in open('requirements.txt').readlines()
            if line.strip() and not line.startswith('#')
        ],
        entry_points={
            'console_scripts': [
                'localmind=src.app:main',
            ],
        },
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Education',
            'Intended Audience :: Healthcare Industry', 
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Topic :: Scientific/Engineering :: Artificial Intelligence',
            'Topic :: Education',
            'Topic :: Scientific/Engineering :: Medical Science Apps.',
        ],
    )
    
    # Run setup if called directly
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        main()
