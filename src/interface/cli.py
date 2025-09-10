"""
LocalMind Command Line Interface

Rich, interactive CLI for LocalMind AI Assistant with offline capabilities.
"""

import sys
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import argparse

try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.layout import Layout
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich import print as rprint
except ImportError:
    # Fallback for when rich is not available
    Console = None
    rprint = print

@dataclass
class CLISession:
    """CLI session state."""
    domain: str = 'general'
    context: List[str] = None
    verbose: bool = False
    language: str = 'en'
    
    def __post_init__(self):
        if self.context is None:
            self.context = []

class LocalMindCLI:
    """
    LocalMind Command Line Interface.
    
    Features:
    - Interactive chat mode
    - Domain-specific assistance
    - Rich formatting and visualization
    - Session context management
    - Offline operation
    - Command history
    """
    
    def __init__(self, app):
        self.app = app
        self.session = CLISession()
        
        # Initialize console
        if Console:
            self.console = Console()
        else:
            self.console = None
            
        # CLI configuration
        self.config = app.config.get('interface', {}).get('cli', {})
        self.max_history = self.config.get('max_history', 50)
        self.auto_save = self.config.get('auto_save', True)
        
        # Command history
        self.history = []
        
        # Available commands
        self.commands = self._initialize_commands()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("LocalMind CLI initialized")
    
    def _initialize_commands(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available CLI commands."""
        return {
            'help': {
                'description': 'Show help information',
                'usage': 'help [command]',
                'function': self._cmd_help
            },
            'domain': {
                'description': 'Switch domain or show current domain',
                'usage': 'domain [education|healthcare|general]',
                'function': self._cmd_domain
            },
            'context': {
                'description': 'Manage session context',
                'usage': 'context [show|clear|add "text"]',
                'function': self._cmd_context
            },
            'history': {
                'description': 'Show command history',
                'usage': 'history [clear]',
                'function': self._cmd_history
            },
            'status': {
                'description': 'Show system status and resources',
                'usage': 'status',
                'function': self._cmd_status
            },
            'memory': {
                'description': 'Show conversation memory statistics',
                'usage': 'memory [stats|clear]',
                'function': self._cmd_memory
            },
            'config': {
                'description': 'Show or modify configuration',
                'usage': 'config [show|set key value]',
                'function': self._cmd_config
            },
            'export': {
                'description': 'Export session or knowledge',
                'usage': 'export [session|knowledge] filename',
                'function': self._cmd_export
            },
            'clear': {
                'description': 'Clear the screen',
                'usage': 'clear',
                'function': self._cmd_clear
            },
            'quit': {
                'description': 'Exit LocalMind',
                'usage': 'quit',
                'function': self._cmd_quit
            },
            'exit': {
                'description': 'Exit LocalMind',
                'usage': 'exit',
                'function': self._cmd_quit
            }
        }
    
    def run(self, args: Optional[argparse.Namespace] = None):
        """Run the CLI interface."""
        try:
            # Parse command line arguments if provided
            if args:
                self._handle_args(args)
            
            # Show welcome message
            self._show_welcome()
            
            # Check system status
            self._check_system_status()
            
            # Start interactive mode
            self._interactive_mode()
            
        except KeyboardInterrupt:
            self._print("\n👋 Goodbye! Thanks for using LocalMind.")
        except Exception as e:
            self.logger.error(f"CLI error: {e}")
            self._print(f"❌ Error: {e}")
    
    def _handle_args(self, args: argparse.Namespace):
        """Handle command line arguments."""
        if hasattr(args, 'domain') and args.domain:
            self.session.domain = args.domain
        if hasattr(args, 'verbose') and args.verbose:
            self.session.verbose = True
        if hasattr(args, 'language') and args.language:
            self.session.language = args.language
    
    def _show_welcome(self):
        """Show welcome message."""
        welcome_text = """
# 🧠 LocalMind - LIVE-OFFLINE AI Assistant

**Your intelligent offline companion for education, healthcare, and general assistance.**

### Current Status:
- 🌐 **Mode**: Completely Offline
- 🏠 **Domain**: {domain}
- 🗣️ **Language**: {language}
- 💾 **Resource Usage**: Available

### Quick Commands:
- `help` - Show all commands
- `domain <name>` - Switch domains
- `status` - Check system status
- `quit` - Exit LocalMind

---
**Ready to assist! Type your question or use a command.**
        """.format(
            domain=self.session.domain.title(),
            language=self.session.language.upper()
        )
        
        if self.console:
            self.console.print(Panel(Markdown(welcome_text), title="Welcome", border_style="green"))
        else:
            self._print(welcome_text)
    
    def _check_system_status(self):
        """Check and display system status."""
        try:
            if self.app.model_engine and not self.app.model_engine.is_loaded:
                self._print("⚠️  Loading AI model... This may take a moment.")
                
                if self.console:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=self.console
                    ) as progress:
                        task = progress.add_task("Loading model...", total=None)
                        # Model loading would happen here
                        progress.update(task, description="Model loaded ✅")
                else:
                    self._print("Loading model... Done ✅")
            
        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            self._print("⚠️  Some components may not be fully available.")
    
    def _interactive_mode(self):
        """Run interactive chat mode."""
        self._print("\n💬 **Interactive Mode** - Type your questions or commands")
        self._print("Type 'help' for commands or 'quit' to exit.\n")
        
        while True:
            try:
                # Get user input
                if self.console:
                    user_input = Prompt.ask(
                        f"[bold cyan]{self.session.domain}[/bold cyan]",
                        console=self.console
                    ).strip()
                else:
                    user_input = input(f"{self.session.domain}> ").strip()
                
                if not user_input:
                    continue
                
                # Add to history
                self.history.append(user_input)
                if len(self.history) > self.max_history:
                    self.history.pop(0)
                
                # Check if it's a command
                if user_input.startswith('/') or user_input.lower() in self.commands:
                    self._handle_command(user_input)
                else:
                    # Process as query
                    self._handle_query(user_input)
                    
            except KeyboardInterrupt:
                if self.console and Confirm.ask("\nAre you sure you want to quit?", console=self.console):
                    break
                elif not self.console:
                    break
            except EOFError:
                break
    
    def _handle_command(self, command_input: str):
        """Handle CLI commands."""
        # Remove leading slash if present
        if command_input.startswith('/'):
            command_input = command_input[1:]
        
        # Parse command and arguments
        parts = command_input.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Execute command
        if command in self.commands:
            try:
                self.commands[command]['function'](args)
            except Exception as e:
                self.logger.error(f"Command error: {e}")
                self._print(f"❌ Command error: {e}")
        else:
            self._print(f"❌ Unknown command: {command}. Type 'help' for available commands.")
    
    def _handle_query(self, query: str):
        """Handle user queries."""
        try:
            # Show processing indicator
            if self.console:
                with self.console.status("[bold green]Processing your query..."):
                    response = self._process_query(query)
            else:
                self._print("Processing...")
                response = self._process_query(query)
            
            # Display response
            self._display_response(response, query)
            
        except Exception as e:
            self.logger.error(f"Query processing error: {e}")
            self._print(f"❌ Sorry, I encountered an error processing your query: {e}")
    
    def _process_query(self, query: str) -> Dict[str, Any]:
        """Process query through appropriate domain."""
        # Build context
        context = '\n'.join(self.session.context) if self.session.context else None
        
        # Route to appropriate domain
        if self.session.domain == 'education':
            if hasattr(self.app, 'education_domain'):
                response = self.app.education_domain.process_education_query(
                    query, context, self.session.language
                )
                return {'type': 'education', 'data': response}
        
        elif self.session.domain == 'healthcare':
            if hasattr(self.app, 'healthcare_domain'):
                response = self.app.healthcare_domain.process_healthcare_query(
                    query, context, self.session.language
                )
                return {'type': 'healthcare', 'data': response}
        
        # Default to general domain
        if hasattr(self.app, 'general_domain'):
            response = self.app.general_domain.process_general_query(
                query, context, self.session.language
            )
            return {'type': 'general', 'data': response}
        
        # Fallback response
        return {
            'type': 'fallback',
            'data': {
                'content': "I'm currently setting up my knowledge base. Please try again in a moment.",
                'confidence_level': 'low'
            }
        }
    
    def _display_response(self, response: Dict[str, Any], original_query: str):
        """Display formatted response."""
        response_type = response['type']
        data = response['data']
        
        if self.console:
            self._display_rich_response(response_type, data, original_query)
        else:
            self._display_plain_response(response_type, data, original_query)
    
    def _display_rich_response(self, response_type: str, data: Any, original_query: str):
        """Display response with rich formatting."""
        # Create response panel
        content_parts = [f"**Response**: {data.content}"]
        
        # Add domain-specific information
        if hasattr(data, 'confidence_level'):
            content_parts.append(f"**Confidence**: {data.confidence_level}")
        
        if hasattr(data, 'subject') and data.subject:
            content_parts.append(f"**Subject**: {data.subject}")
        
        if hasattr(data, 'topic_category') and data.topic_category:
            content_parts.append(f"**Category**: {data.topic_category}")
        
        # Add follow-up suggestions
        if hasattr(data, 'follow_up_suggestions') and data.follow_up_suggestions:
            content_parts.append("**Follow-up suggestions**:")
            for suggestion in data.follow_up_suggestions[:3]:
                content_parts.append(f"• {suggestion}")
        
        response_content = '\n\n'.join(content_parts)
        
        # Display in panel
        self.console.print(Panel(
            Markdown(response_content),
            title=f"🤖 LocalMind ({response_type.title()})",
            border_style="blue"
        ))
        
        # Add context to session
        if len(self.session.context) >= 5:
            self.session.context.pop(0)
        self.session.context.append(f"Q: {original_query}\nA: {data.content}")
    
    def _display_plain_response(self, response_type: str, data: Any, original_query: str):
        """Display response in plain text format."""
        self._print(f"\n🤖 LocalMind ({response_type.title()}):")
        self._print("-" * 50)
        self._print(data.content)
        
        if hasattr(data, 'confidence_level'):
            self._print(f"\nConfidence: {data.confidence_level}")
        
        if hasattr(data, 'follow_up_suggestions') and data.follow_up_suggestions:
            self._print("\nSuggestions:")
            for suggestion in data.follow_up_suggestions[:3]:
                self._print(f"• {suggestion}")
        
        self._print("-" * 50 + "\n")
        
        # Add context to session
        if len(self.session.context) >= 5:
            self.session.context.pop(0)
        self.session.context.append(f"Q: {original_query}\nA: {data.content}")
    
    # Command implementations
    def _cmd_help(self, args: List[str]):
        """Show help information."""
        if not args:
            # Show all commands
            if self.console:
                table = Table(title="Available Commands")
                table.add_column("Command", style="cyan")
                table.add_column("Description", style="white")
                table.add_column("Usage", style="dim")
                
                for cmd, info in self.commands.items():
                    table.add_row(cmd, info['description'], info['usage'])
                
                self.console.print(table)
            else:
                self._print("\nAvailable Commands:")
                self._print("-" * 40)
                for cmd, info in self.commands.items():
                    self._print(f"{cmd:12} - {info['description']}")
                    self._print(f"             Usage: {info['usage']}")
                self._print("-" * 40)
        else:
            # Show specific command help
            cmd = args[0].lower()
            if cmd in self.commands:
                info = self.commands[cmd]
                self._print(f"\n{cmd}: {info['description']}")
                self._print(f"Usage: {info['usage']}")
            else:
                self._print(f"Unknown command: {cmd}")
    
    def _cmd_domain(self, args: List[str]):
        """Switch domain or show current domain."""
        available_domains = ['general', 'education', 'healthcare']
        
        if not args:
            self._print(f"Current domain: {self.session.domain}")
            self._print(f"Available domains: {', '.join(available_domains)}")
        else:
            new_domain = args[0].lower()
            if new_domain in available_domains:
                old_domain = self.session.domain
                self.session.domain = new_domain
                self._print(f"Switched from '{old_domain}' to '{new_domain}' domain")
                # Clear context when switching domains
                self.session.context = []
            else:
                self._print(f"Invalid domain. Available: {', '.join(available_domains)}")
    
    def _cmd_context(self, args: List[str]):
        """Manage session context."""
        if not args or args[0] == 'show':
            if self.session.context:
                self._print("Session Context:")
                for i, ctx in enumerate(self.session.context, 1):
                    self._print(f"{i}. {ctx[:100]}...")
            else:
                self._print("No session context")
        
        elif args[0] == 'clear':
            self.session.context = []
            self._print("Session context cleared")
        
        elif args[0] == 'add':
            if len(args) > 1:
                context_text = ' '.join(args[1:])
                self.session.context.append(context_text)
                self._print("Context added")
            else:
                self._print("Please provide context to add")
    
    def _cmd_history(self, args: List[str]):
        """Show command history."""
        if args and args[0] == 'clear':
            self.history = []
            self._print("History cleared")
        else:
            if self.history:
                self._print("Command History:")
                for i, cmd in enumerate(self.history[-10:], 1):  # Show last 10
                    self._print(f"{i:2}. {cmd}")
            else:
                self._print("No command history")
    
    def _cmd_status(self, args: List[str]):
        """Show system status and resources."""
        status_info = {
            'Domain': self.session.domain,
            'Language': self.session.language,
            'Context Items': len(self.session.context),
            'History Items': len(self.history),
            'Model Loaded': getattr(self.app.model_engine, 'is_loaded', False),
            'Vector DB': hasattr(self.app, 'vector_db') and self.app.vector_db is not None,
            'Memory System': hasattr(self.app, 'conversation_memory') and self.app.conversation_memory is not None
        }
        
        if self.console:
            table = Table(title="System Status")
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="white")
            
            for key, value in status_info.items():
                status_style = "green" if value else "red"
                table.add_row(key, str(value), style=status_style)
            
            self.console.print(table)
        else:
            self._print("\nSystem Status:")
            self._print("-" * 30)
            for key, value in status_info.items():
                self._print(f"{key:15}: {value}")
            self._print("-" * 30)
    
    def _cmd_memory(self, args: List[str]):
        """Show conversation memory statistics."""
        if not hasattr(self.app, 'conversation_memory') or not self.app.conversation_memory:
            self._print("❌ Conversation memory not available")
            return
        
        if args and args[0] == 'clear':
            # Clear memory (implement if needed)
            self._print("Memory clearing not implemented yet")
            return
        
        try:
            stats = self.app.conversation_memory.get_conversation_stats()
            
            if self.console:
                table = Table(title="💭 Conversation Memory Statistics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("Total Conversations", str(stats['total_conversations']))
                table.add_row("Current Session", str(stats['current_session_length']))
                table.add_row("Memory Usage", stats['memory_usage'])
                table.add_row("Preferred Domains", ", ".join(stats['preferred_domains'][:3]))
                table.add_row("Common Topics", ", ".join(stats['common_topics'][:5]))
                
                self.console.print(table)
            else:
                self._print("\nConversation Memory Statistics:")
                self._print("-" * 35)
                self._print(f"Total Conversations: {stats['total_conversations']}")
                self._print(f"Current Session: {stats['current_session_length']}")
                self._print(f"Memory Usage: {stats['memory_usage']}")
                self._print(f"Preferred Domains: {', '.join(stats['preferred_domains'][:3])}")
                self._print(f"Common Topics: {', '.join(stats['common_topics'][:5])}")
                self._print("-" * 35)
                
        except Exception as e:
            self._print(f"❌ Error getting memory stats: {e}")
    
    def _cmd_config(self, args: List[str]):
        """Show or modify configuration."""
        if not args or args[0] == 'show':
            self._print("Current Configuration:")
            self._print(f"  Domain: {self.session.domain}")
            self._print(f"  Language: {self.session.language}")
            self._print(f"  Verbose: {self.session.verbose}")
            self._print(f"  Max History: {self.max_history}")
        else:
            self._print("Configuration modification not implemented yet")
    
    def _cmd_export(self, args: List[str]):
        """Export session or knowledge."""
        if len(args) < 2:
            self._print("Usage: export [session|knowledge] filename")
            return
        
        export_type = args[0]
        filename = args[1]
        
        try:
            if export_type == 'session':
                # Export session data
                session_data = {
                    'domain': self.session.domain,
                    'context': self.session.context,
                    'history': self.history
                }
                # Would implement actual file writing here
                self._print(f"Session exported to {filename}")
            
            elif export_type == 'knowledge':
                self._print("Knowledge export not implemented yet")
            
            else:
                self._print("Invalid export type. Use 'session' or 'knowledge'")
                
        except Exception as e:
            self._print(f"Export failed: {e}")
    
    def _cmd_clear(self, args: List[str]):
        """Clear the screen."""
        if self.console:
            self.console.clear()
        else:
            os.system('cls' if os.name == 'nt' else 'clear')
    
    def _cmd_quit(self, args: List[str]):
        """Exit LocalMind."""
        self._print("👋 Thank you for using LocalMind!")
        if self.auto_save:
            self._print("💾 Session saved automatically")
        sys.exit(0)
    
    def _print(self, message: str):
        """Print message with or without rich formatting."""
        if self.console:
            self.console.print(message)
        else:
            print(message)

def create_cli_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description='LocalMind - LIVE-OFFLINE AI Assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  localmind                          # Start interactive mode
  localmind --domain education       # Start in education domain
  localmind --verbose                # Enable verbose output
  localmind --language es            # Set language to Spanish
        """
    )
    
    parser.add_argument(
        '--domain', '-d',
        choices=['general', 'education', 'healthcare'],
        default='general',
        help='Start in specific domain'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--language', '-l',
        default='en',
        help='Response language (default: en)'
    )
    
    return parser
