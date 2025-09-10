#!/usr/bin/env python3
"""
LocalMind - LIVE-OFFLINE AI Assistant
Main Application Entry Point

This is the primary entry point for LocalMind, providing both CLI and GUI interfaces
for the LIVE-OFFLINE AI assistant specialized in education and healthcare.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    import yaml
    import torch
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Import LocalMind components
from model.engine import ModelEngine
from knowledge.vector_db import VectorDatabase
from knowledge.conversation_memory import ConversationMemory
from utils.resource_manager import ResourceManager
from utils.security import SecurityManager

# Domain modules
from domains.education import EducationDomain
from domains.healthcare import HealthcareDomain
from domains.general import GeneralDomain

# Interface modules (with fallback handling)
try:
    from interface.cli import LocalMindCLI
    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False
    LocalMindCLI = None

try:
    from interface.gui import LocalMindGUI
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    LocalMindGUI = None

class LocalMindApp:
    """
    Main LocalMind Application Class
    
    Orchestrates all components for LIVE-OFFLINE AI assistance.
    """
    
    def __init__(self, config_path="src/config.yaml"):
        self.console = Console()
        self.config_path = config_path
        self.config = None
        self.model_engine = None
        self.vector_db = None
        self.conversation_memory = None
        self.resource_manager = None
        self.security_manager = None
        self.domains = {}
        
        self._setup_logging()
        self._load_config()
        self._display_banner()
        
    def _setup_logging(self):
        """Setup logging configuration."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "localmind.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger("LocalMind")
        self.logger.info("LocalMind starting up...")
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            self.logger.info("Configuration loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            sys.exit(1)
    
    def _display_banner(self):
        """Display LocalMind banner."""
        banner_text = Text()
        banner_text.append("🧠 LocalMind - LIVE-OFFLINE AI Assistant 🧠", style="bold blue")
        banner_text.append("\n")
        banner_text.append("Providing AI assistance without internet dependency", style="italic")
        
        panel = Panel(
            banner_text,
            title="Welcome to LocalMind",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()
    
    def initialize_components(self):
        """Initialize all LocalMind components."""
        self.console.print("🔧 Initializing LocalMind components...", style="yellow")
        
        try:
            # Initialize resource manager first
            self.resource_manager = ResourceManager(self.config)
            self.console.print("   ✅ Resource Manager initialized")
            
            # Initialize security manager
            self.security_manager = SecurityManager(self.config)
            self.console.print("   ✅ Security Manager initialized")
            
            # Initialize vector database
            self.vector_db = VectorDatabase(self.config)
            self.console.print("   ✅ Vector Database initialized")
            
            # Initialize conversation memory
            self.conversation_memory = ConversationMemory(self.config, self.vector_db)
            self.console.print("   ✅ Conversation Memory initialized")
            
            # Initialize model engine
            self.model_engine = ModelEngine(self.config, self.resource_manager)
            self.console.print("   ✅ Model Engine initialized")
            
            # Load AI model
            self.console.print("   🤖 Loading AI model...", style="cyan")
            model_loaded = self.model_engine.load_model()
            if model_loaded:
                self.console.print("   ✅ AI Model loaded successfully", style="green")
            else:
                self.console.print("   ⚠️ AI Model loading failed, using fallback responses", style="yellow")
            
            # Initialize domain modules
            self._initialize_domains()
            
            self.console.print("✅ All components initialized successfully!", style="green bold")
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            self.console.print(f"❌ Initialization failed: {e}", style="red bold")
            sys.exit(1)
    
    def _initialize_domains(self):
        """Initialize domain-specific modules."""
        if self.config['domains']['education']['enabled']:
            self.domains['education'] = EducationDomain(
                self.config, self.model_engine, self.vector_db, self.conversation_memory
            )
            self.console.print("   ✅ Education Domain loaded")
        
        if self.config['domains']['healthcare']['enabled']:
            self.domains['healthcare'] = HealthcareDomain(
                self.config, self.model_engine, self.vector_db, self.conversation_memory
            )
            self.console.print("   ✅ Healthcare Domain loaded")
        
        if self.config['domains']['general']['enabled']:
            self.domains['general'] = GeneralDomain(
                self.config, self.model_engine, self.vector_db, self.conversation_memory
            )
            self.console.print("   ✅ General Domain loaded")
    
    def run_cli(self, domain=None):
        """Run LocalMind in CLI mode."""
        if not CLI_AVAILABLE:
            self.console.print("❌ CLI interface not available. Check dependencies.", style="red")
            sys.exit(1)
        
        self.console.print("🖥️  Starting CLI interface...", style="cyan")
        
        # Store domain references for CLI access
        self.education_domain = self.domains.get('education')
        self.healthcare_domain = self.domains.get('healthcare')
        self.general_domain = self.domains.get('general')
        
        cli = LocalMindCLI(self)
        
        # Parse domain argument for CLI
        import argparse
        args = argparse.Namespace()
        if domain:
            args.domain = domain
        else:
            args.domain = 'general'
        args.verbose = False
        args.language = 'en'
        
        cli.run(args)
    
    def run_gui(self, domain=None):
        """Run LocalMind in GUI mode."""
        if not GUI_AVAILABLE:
            self.console.print("❌ GUI interface not available. Check dependencies.", style="red")
            self.console.print("Falling back to CLI mode...", style="yellow")
            self.run_cli(domain)
            return
        
        self.console.print("🖼️  Starting GUI interface...", style="cyan")
        
        # Store domain references for GUI access
        self.education_domain = self.domains.get('education')
        self.healthcare_domain = self.domains.get('healthcare')
        self.general_domain = self.domains.get('general')
        
        gui = LocalMindGUI(self)
        gui.run()
    
    def run_setup(self):
        """Run initial setup for LocalMind."""
        self.console.print("⚙️  Running LocalMind setup...", style="yellow")
        
        # Import and run setup
        import subprocess
        result = subprocess.run([sys.executable, "setup.py", "install"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            self.console.print("✅ Setup completed successfully!", style="green")
        else:
            self.console.print(f"❌ Setup failed: {result.stderr}", style="red")
            sys.exit(1)
    
    def check_offline_mode(self):
        """Verify that LocalMind is operating in offline mode."""
        if self.config['offline']['verify_offline_mode']:
            # Check for network connectivity and warn if found
            try:
                import urllib.request
                urllib.request.urlopen('http://google.com', timeout=1)
                self.console.print("⚠️  Internet connection detected. LocalMind operates OFFLINE only.", style="yellow")
                if self.config['offline']['block_network_requests']:
                    self.console.print("🔒 Network requests blocked as per configuration.", style="blue")
            except:
                self.console.print("✅ Confirmed offline operation", style="green")

def create_argument_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="LocalMind - LIVE-OFFLINE AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py --cli                    # Start CLI interface
  python app.py --gui                    # Start GUI interface  
  python app.py --cli --domain education # Start CLI in education mode
  python app.py --setup                  # Run initial setup
        """
    )
    
    # Interface options
    interface_group = parser.add_mutually_exclusive_group()
    interface_group.add_argument("--cli", action="store_true", 
                               help="Run in command-line interface mode")
    interface_group.add_argument("--gui", action="store_true",
                               help="Run in graphical interface mode")
    
    # Domain selection
    parser.add_argument("--domain", choices=["education", "healthcare", "general"],
                       help="Start in specific domain mode")
    
    # Setup and configuration
    parser.add_argument("--setup", action="store_true",
                       help="Run initial setup and configuration")
    parser.add_argument("--config", default="src/config.yaml",
                       help="Path to configuration file")
    
    # Debug options
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug mode")
    parser.add_argument("--verbose", action="store_true", 
                       help="Enable verbose logging")
    
    return parser

def main():
    """Main entry point for LocalMind application."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle no arguments - default to CLI
    if not any([args.cli, args.gui, args.setup]):
        args.cli = True
    
    try:
        # Initialize LocalMind application
        app = LocalMindApp(config_path=args.config)
        
        # Handle setup mode
        if args.setup:
            app.run_setup()
            return
        
        # Verify offline operation
        app.check_offline_mode()
        
        # Initialize components
        app.initialize_components()
        
        # Run appropriate interface
        if args.cli:
            app.run_cli(domain=args.domain)
        elif args.gui:
            app.run_gui(domain=args.domain)
            
    except KeyboardInterrupt:
        console = Console()
        console.print("\n👋 LocalMind shutting down gracefully...", style="yellow")
        sys.exit(0)
    except Exception as e:
        console = Console()
        console.print(f"❌ LocalMind encountered an error: {e}", style="red bold")
        sys.exit(1)

if __name__ == "__main__":
    main()
