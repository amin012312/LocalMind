#!/usr/bin/env python3
"""
LocalMind Integration Test

Simple test to verify all components can be imported and initialized.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all major components can be imported."""
    print("🧪 Testing LocalMind component imports...")
    
    try:
        # Test configuration loading
        import yaml
        print("   ✅ YAML configuration support")
        
        # Test core components
        from model.engine import ModelEngine
        print("   ✅ Model Engine")
        
        from knowledge.vector_db import VectorDatabase
        print("   ✅ Vector Database")
        
        from utils.resource_manager import ResourceManager
        print("   ✅ Resource Manager")
        
        from utils.security import SecurityManager
        print("   ✅ Security Manager")
        
        # Test domain modules
        from domains.education import EducationDomain
        print("   ✅ Education Domain")
        
        from domains.healthcare import HealthcareDomain
        print("   ✅ Healthcare Domain")
        
        from domains.general import GeneralDomain
        print("   ✅ General Domain")
        
        # Test interfaces
        try:
            from interface.cli import LocalMindCLI
            print("   ✅ CLI Interface")
        except ImportError as e:
            print(f"   ⚠️  CLI Interface (missing dependencies: {e})")
        
        try:
            from interface.gui import LocalMindGUI
            print("   ✅ GUI Interface")
        except ImportError as e:
            print(f"   ⚠️  GUI Interface (missing dependencies: {e})")
        
        # Test main app
        from app import LocalMindApp
        print("   ✅ Main Application")
        
        print("\n✅ All core components imported successfully!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    print("\n🧪 Testing configuration loading...")
    
    try:
        config_path = Path(__file__).parent / "src" / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                import yaml
                config = yaml.safe_load(f)
            
            # Check key configuration sections
            required_sections = ['model', 'domains', 'interface', 'security', 'resources']
            missing_sections = []
            
            for section in required_sections:
                if section in config:
                    print(f"   ✅ {section} configuration")
                else:
                    missing_sections.append(section)
                    print(f"   ❌ {section} configuration missing")
            
            if not missing_sections:
                print("\n✅ Configuration file is complete!")
                return True
            else:
                print(f"\n⚠️  Missing configuration sections: {missing_sections}")
                return False
        else:
            print("   ❌ config.yaml not found")
            return False
            
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without model loading."""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Import main app
        from app import LocalMindApp
        
        # Try to initialize (without actually loading models)
        config_path = Path(__file__).parent / "src" / "config.yaml"
        if config_path.exists():
            app = LocalMindApp(str(config_path))
            print("   ✅ Application initialization")
            
            # Test that domains can be initialized
            if hasattr(app, 'domains'):
                print("   ✅ Domain structure ready")
            
            print("\n✅ Basic functionality test passed!")
            return True
        else:
            print("   ❌ Configuration file not found")
            return False
            
    except Exception as e:
        print(f"\n❌ Functionality test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 LocalMind Integration Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_basic_functionality
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 All tests passed! LocalMind is ready to use.")
        print("\nNext steps:")
        print("1. Run: python src/app.py --setup")
        print("2. Then: python src/app.py --cli")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        print("\nTroubleshooting:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Check Python version: python --version (3.8+ required)")
        print("3. Verify file structure in src/ directory")
        return 1

if __name__ == "__main__":
    sys.exit(main())
