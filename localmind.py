#!/usr/bin/env python3
"""
LocalMind Launcher

Simple launcher script for LocalMind with dependency checking.
"""

import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []
    
    try:
        import yaml
    except ImportError:
        missing_deps.append('PyYAML')
    
    try:
        import rich
    except ImportError:
        missing_deps.append('rich')
    
    try:
        import torch
    except ImportError:
        missing_deps.append('torch')
    
    try:
        import transformers
    except ImportError:
        missing_deps.append('transformers')
    
    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n💡 Please install dependencies:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main launcher function."""
    print("🧠 LocalMind - LIVE-OFFLINE AI Assistant")
    print("=========================================")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Add src to path
    src_path = Path(__file__).parent / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
    else:
        print("❌ src directory not found. Please run from LocalMind root directory.")
        sys.exit(1)
    
    # Import and run the main app
    try:
        from app import main as app_main
        app_main()
    except ImportError as e:
        print(f"❌ Failed to import LocalMind app: {e}")
        print("💡 Try running the integration test: python test_integration.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting LocalMind: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
