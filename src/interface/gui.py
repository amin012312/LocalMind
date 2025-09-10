"""
LocalMind Graphical User Interface

Simple, user-friendly GUI for LocalMind AI Assistant with offline capabilities.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinter.font import Font
import threading
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json
import os

@dataclass
class GUISession:
    """GUI session state."""
    domain: str = 'general'
    language: str = 'en'
    font_size: int = 11
    theme: str = 'light'
    auto_scroll: bool = True

class LocalMindGUI:
    """
    LocalMind Graphical User Interface.
    
    Features:
    - Clean, intuitive interface
    - Domain switching
    - Chat-like conversation view
    - Real-time response streaming
    - Session management
    - Settings configuration
    - Export capabilities
    """
    
    def __init__(self, app):
        self.app = app
        self.session = GUISession()
        self.logger = logging.getLogger(__name__)
        
        # GUI configuration
        self.config = app.config.get('interface', {}).get('gui', {})
        
        # Initialize main window
        self.root = None
        self.conversation_history = []
        
        # UI Components
        self.chat_display = None
        self.input_entry = None
        self.domain_var = None
        self.status_label = None
        
        # Styling
        self.colors = self._get_color_scheme()
        self.fonts = None  # Will be initialized after root window creation
        
        self.logger.info("LocalMind GUI initialized")
    
    def _get_color_scheme(self) -> Dict[str, str]:
        """Get color scheme based on theme."""
        themes = {
            'light': {
                'bg': '#FFFFFF',
                'fg': '#000000',
                'accent': '#0066CC',
                'secondary': '#F0F0F0',
                'user_msg': '#E3F2FD',
                'ai_msg': '#F3E5F5',
                'button': '#2196F3',
                'button_hover': '#1976D2'
            },
            'dark': {
                'bg': '#2B2B2B',
                'fg': '#FFFFFF',
                'accent': '#BB86FC',
                'secondary': '#3C3C3C',
                'user_msg': '#1E3A8A',
                'ai_msg': '#4C1D95',
                'button': '#BB86FC',
                'button_hover': '#9C64C4'
            }
        }
        return themes.get(self.session.theme, themes['light'])
    
    def _get_fonts(self) -> Dict[str, Font]:
        """Get font configuration."""
        base_size = self.session.font_size
        return {
            'default': Font(family='Segoe UI', size=base_size),
            'bold': Font(family='Segoe UI', size=base_size, weight='bold'),
            'small': Font(family='Segoe UI', size=base_size-2),
            'large': Font(family='Segoe UI', size=base_size+2, weight='bold'),
            'monospace': Font(family='Consolas', size=base_size-1)
        }
    
    def run(self):
        """Start the GUI application."""
        try:
            self._create_main_window()
            self._create_menu()
            self._create_layout()
            self._setup_bindings()
            self._check_system_status()
            
            # Start the GUI event loop
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"GUI error: {e}")
            if self.root:
                messagebox.showerror("Error", f"GUI Error: {e}")
    
    def _create_main_window(self):
        """Create the main application window."""
        self.root = tk.Tk()
        self.root.title("LocalMind - LIVE-OFFLINE AI Assistant")
        self.root.geometry("900x700")
        self.root.minsize(600, 400)
        
        # Initialize fonts after root window is created
        self.fonts = self._get_fonts()
        
        # Set icon (if available)
        try:
            # icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
            # if os.path.exists(icon_path):
            #     self.root.iconbitmap(icon_path)
            pass
        except:
            pass
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure colors
        self.root.configure(bg=self.colors['bg'])
    
    def _create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Session", command=self._new_session)
        file_menu.add_command(label="Save Session", command=self._save_session)
        file_menu.add_command(label="Load Session", command=self._load_session)
        file_menu.add_separator()
        file_menu.add_command(label="Export Chat", command=self._export_chat)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Domain menu
        domain_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Domain", menu=domain_menu)
        domain_menu.add_command(label="General", command=lambda: self._switch_domain('general'))
        domain_menu.add_command(label="Education", command=lambda: self._switch_domain('education'))
        domain_menu.add_command(label="Healthcare", command=lambda: self._switch_domain('healthcare'))
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="System Status", command=self._show_status)
        tools_menu.add_command(label="Clear Chat", command=self._clear_chat)
        tools_menu.add_command(label="Settings", command=self._show_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="User Guide", command=self._show_help)
    
    def _create_layout(self):
        """Create the main layout."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top frame for domain and status
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Domain selection
        ttk.Label(top_frame, text="Domain:", font=self.fonts['default']).pack(side=tk.LEFT)
        
        self.domain_var = tk.StringVar(value=self.session.domain)
        domain_combo = ttk.Combobox(
            top_frame, 
            textvariable=self.domain_var,
            values=['general', 'education', 'healthcare'],
            state='readonly',
            width=15
        )
        domain_combo.pack(side=tk.LEFT, padx=(5, 20))
        domain_combo.bind('<<ComboboxSelected>>', self._on_domain_change)
        
        # Status indicator
        self.status_label = ttk.Label(
            top_frame, 
            text="● Offline Ready", 
            foreground='green',
            font=self.fonts['small']
        )
        self.status_label.pack(side=tk.RIGHT)
        
        # Chat display area
        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Chat display with scrollbar
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=self.fonts['default'],
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            selectbackground=self.colors['accent'],
            relief=tk.FLAT,
            borderwidth=1
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for styling
        self._configure_text_tags()
        
        # Input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X)
        
        # Input entry
        self.input_entry = tk.Text(
            input_frame,
            height=3,
            wrap=tk.WORD,
            font=self.fonts['default'],
            relief=tk.SOLID,
            borderwidth=1
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Send button
        send_button = tk.Button(
            input_frame,
            text="Send",
            command=self._send_message,
            bg=self.colors['button'],
            fg='white',
            font=self.fonts['default'],
            relief=tk.FLAT,
            padx=20,
            cursor='hand2'
        )
        send_button.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add hover effect to button
        def on_enter(e):
            send_button.configure(bg=self.colors['button_hover'])
        def on_leave(e):
            send_button.configure(bg=self.colors['button'])
        
        send_button.bind("<Enter>", on_enter)
        send_button.bind("<Leave>", on_leave)
        
        # Welcome message
        self._add_system_message("Welcome to LocalMind! Your offline AI assistant is ready.")
        self._add_system_message(f"Current domain: {self.session.domain.title()}")
        self._add_system_message("Type your question below and press Send or Ctrl+Enter.")
    
    def _configure_text_tags(self):
        """Configure text tags for message styling."""
        self.chat_display.tag_configure('user', 
            background=self.colors['user_msg'], 
            lmargin1=20, lmargin2=20, rmargin=20,
            spacing1=5, spacing3=5
        )
        self.chat_display.tag_configure('ai', 
            background=self.colors['ai_msg'], 
            lmargin1=20, lmargin2=20, rmargin=20,
            spacing1=5, spacing3=5
        )
        self.chat_display.tag_configure('system', 
            foreground='gray', 
            font=self.fonts['small'],
            lmargin1=10, lmargin2=10
        )
        self.chat_display.tag_configure('bold', font=self.fonts['bold'])
        self.chat_display.tag_configure('code', font=self.fonts['monospace'], background='#F5F5F5')
    
    def _setup_bindings(self):
        """Setup keyboard and event bindings."""
        # Ctrl+Enter to send message
        self.input_entry.bind('<Control-Return>', lambda e: self._send_message())
        
        # Enter to send message (optional)
        # self.input_entry.bind('<Return>', lambda e: self._send_message())
        
        # Window closing
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Focus on input
        self.input_entry.focus_set()
    
    def _check_system_status(self):
        """Check and update system status."""
        try:
            # Check if model is loaded
            if hasattr(self.app, 'model_engine') and self.app.model_engine:
                if self.app.model_engine.is_loaded:
                    self.status_label.config(text="● Model Ready", foreground='green')
                else:
                    self.status_label.config(text="● Loading Model...", foreground='orange')
                    # Start model loading in background
                    threading.Thread(target=self._load_model_async, daemon=True).start()
            else:
                self.status_label.config(text="● Setting Up...", foreground='orange')
                
        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            self.status_label.config(text="● System Error", foreground='red')
    
    def _load_model_async(self):
        """Load model asynchronously."""
        try:
            # Model loading would happen here
            # For now, just simulate loading
            import time
            time.sleep(2)  # Simulate loading time
            
            # Update UI from main thread
            self.root.after(0, lambda: self.status_label.config(
                text="● Model Ready", foreground='green'
            ))
            
        except Exception as e:
            self.logger.error(f"Model loading failed: {e}")
            self.root.after(0, lambda: self.status_label.config(
                text="● Model Error", foreground='red'
            ))
    
    def _send_message(self):
        """Send user message and get AI response."""
        # Get user input
        user_input = self.input_entry.get("1.0", tk.END).strip()
        if not user_input:
            return
        
        # Clear input
        self.input_entry.delete("1.0", tk.END)
        
        # Add user message to chat
        self._add_user_message(user_input)
        
        # Process response in background thread
        threading.Thread(target=self._process_message_async, args=(user_input,), daemon=True).start()
    
    def _process_message_async(self, user_input: str):
        """Process message asynchronously."""
        try:
            # Show typing indicator
            self.root.after(0, lambda: self._add_typing_indicator())
            
            # Get response from appropriate domain
            response = self._get_ai_response(user_input)
            
            # Remove typing indicator and add response
            self.root.after(0, lambda: self._remove_typing_indicator())
            self.root.after(0, lambda: self._add_ai_message(response, user_input))
            
        except Exception as e:
            self.logger.error(f"Message processing failed: {e}")
            self.root.after(0, lambda: self._remove_typing_indicator())
            self.root.after(0, lambda: self._add_error_message(str(e)))
    
    def _get_ai_response(self, user_input: str) -> Dict[str, Any]:
        """Get AI response from appropriate domain."""
        try:
            # Route to appropriate domain
            if self.session.domain == 'education':
                if hasattr(self.app, 'education_domain'):
                    response = self.app.education_domain.process_education_query(
                        user_input, language=self.session.language
                    )
                    return {'type': 'education', 'data': response}
            
            elif self.session.domain == 'healthcare':
                if hasattr(self.app, 'healthcare_domain'):
                    response = self.app.healthcare_domain.process_healthcare_query(
                        user_input, language=self.session.language
                    )
                    return {'type': 'healthcare', 'data': response}
            
            # Default to general domain
            if hasattr(self.app, 'general_domain'):
                response = self.app.general_domain.process_general_query(
                    user_input, language=self.session.language
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
            
        except Exception as e:
            self.logger.error(f"AI response failed: {e}")
            return {
                'type': 'error',
                'data': {
                    'content': f"I encountered an error: {e}",
                    'confidence_level': 'low'
                }
            }
    
    def _add_user_message(self, message: str):
        """Add user message to chat display."""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp and user label
        self.chat_display.insert(tk.END, "\nYou: ", 'bold')
        self.chat_display.insert(tk.END, f"{message}\n", 'user')
        
        self.chat_display.config(state=tk.DISABLED)
        if self.session.auto_scroll:
            self.chat_display.see(tk.END)
        
        # Store in conversation history
        self.conversation_history.append({'type': 'user', 'content': message})
    
    def _add_ai_message(self, response: Dict[str, Any], original_query: str):
        """Add AI message to chat display."""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add AI label
        domain_name = response['type'].title()
        self.chat_display.insert(tk.END, f"\nLocalMind ({domain_name}): ", 'bold')
        
        # Add response content
        data = response['data']
        content = data.content if hasattr(data, 'content') else str(data.get('content', 'No response'))
        self.chat_display.insert(tk.END, f"{content}\n", 'ai')
        
        # Add confidence level if available
        if hasattr(data, 'confidence_level') and data.confidence_level:
            self.chat_display.insert(tk.END, f"Confidence: {data.confidence_level}\n", 'system')
        
        # Add follow-up suggestions if available
        if hasattr(data, 'follow_up_suggestions') and data.follow_up_suggestions:
            self.chat_display.insert(tk.END, "Suggestions: ", 'system')
            suggestions = ', '.join(data.follow_up_suggestions[:2])
            self.chat_display.insert(tk.END, f"{suggestions}\n", 'system')
        
        self.chat_display.config(state=tk.DISABLED)
        if self.session.auto_scroll:
            self.chat_display.see(tk.END)
        
        # Store in conversation history
        self.conversation_history.append({
            'type': 'ai',
            'domain': response['type'],
            'content': content,
            'query': original_query
        })
    
    def _add_system_message(self, message: str):
        """Add system message to chat display."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{message}\n", 'system')
        self.chat_display.config(state=tk.DISABLED)
        if self.session.auto_scroll:
            self.chat_display.see(tk.END)
    
    def _add_error_message(self, error: str):
        """Add error message to chat display."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\n❌ Error: {error}\n", 'system')
        self.chat_display.config(state=tk.DISABLED)
        if self.session.auto_scroll:
            self.chat_display.see(tk.END)
    
    def _add_typing_indicator(self):
        """Add typing indicator."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\nLocalMind is thinking...\n", 'system')
        self.chat_display.config(state=tk.DISABLED)
        if self.session.auto_scroll:
            self.chat_display.see(tk.END)
    
    def _remove_typing_indicator(self):
        """Remove typing indicator."""
        self.chat_display.config(state=tk.NORMAL)
        
        # Find and remove the last "thinking" message
        content = self.chat_display.get("1.0", tk.END)
        lines = content.split('\n')
        
        # Remove the typing indicator line
        if lines and "thinking" in lines[-2]:
            # Calculate position to delete
            line_start = f"{len(lines)-2}.0"
            line_end = f"{len(lines)-1}.0"
            self.chat_display.delete(line_start, line_end)
        
        self.chat_display.config(state=tk.DISABLED)
    
    def _on_domain_change(self, event):
        """Handle domain change."""
        new_domain = self.domain_var.get()
        if new_domain != self.session.domain:
            self.session.domain = new_domain
            self._add_system_message(f"Switched to {new_domain.title()} domain")
    
    def _switch_domain(self, domain: str):
        """Switch to specified domain."""
        self.domain_var.set(domain)
        self.session.domain = domain
        self._add_system_message(f"Switched to {domain.title()} domain")
    
    # Menu command implementations
    def _new_session(self):
        """Start a new session."""
        if messagebox.askyesno("New Session", "Start a new session? Current chat will be cleared."):
            self._clear_chat()
            self.conversation_history = []
            self._add_system_message("New session started")
    
    def _save_session(self):
        """Save current session."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                session_data = {
                    'domain': self.session.domain,
                    'conversation': self.conversation_history,
                    'settings': {
                        'language': self.session.language,
                        'theme': self.session.theme,
                        'font_size': self.session.font_size
                    }
                }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Session saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save session: {e}")
    
    def _load_session(self):
        """Load a session."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Restore session
                self.session.domain = session_data.get('domain', 'general')
                self.domain_var.set(self.session.domain)
                
                if 'settings' in session_data:
                    settings = session_data['settings']
                    self.session.language = settings.get('language', 'en')
                    self.session.theme = settings.get('theme', 'light')
                    self.session.font_size = settings.get('font_size', 11)
                
                # Clear and restore conversation
                self._clear_chat()
                self.conversation_history = session_data.get('conversation', [])
                
                # Redisplay conversation
                for item in self.conversation_history:
                    if item['type'] == 'user':
                        self._add_user_message(item['content'])
                    elif item['type'] == 'ai':
                        # Reconstruct response format
                        response = {
                            'type': item.get('domain', 'general'),
                            'data': type('obj', (object,), {'content': item['content']})()
                        }
                        self._add_ai_message(response, item.get('query', ''))
                
                messagebox.showinfo("Success", f"Session loaded from {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load session: {e}")
    
    def _export_chat(self):
        """Export chat to text file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"LocalMind Chat Export\n")
                    f.write(f"Domain: {self.session.domain}\n")
                    f.write(f"Date: {tk.datetime.datetime.now()}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for item in self.conversation_history:
                        if item['type'] == 'user':
                            f.write(f"You: {item['content']}\n\n")
                        elif item['type'] == 'ai':
                            domain = item.get('domain', 'general')
                            f.write(f"LocalMind ({domain.title()}): {item['content']}\n\n")
                
                messagebox.showinfo("Success", f"Chat exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export chat: {e}")
    
    def _clear_chat(self):
        """Clear chat display."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def _show_status(self):
        """Show system status dialog."""
        status_text = f"""LocalMind System Status

Domain: {self.session.domain.title()}
Language: {self.session.language.upper()}
Theme: {self.session.theme.title()}

Model Status: {"Loaded" if hasattr(self.app, 'model_engine') and getattr(self.app.model_engine, 'is_loaded', False) else "Not Loaded"}
Vector DB: {"Available" if hasattr(self.app, 'vector_db') and self.app.vector_db else "Not Available"}

Conversation Items: {len(self.conversation_history)}
Session Domain: {self.session.domain}
"""
        messagebox.showinfo("System Status", status_text)
    
    def _show_settings(self):
        """Show settings dialog."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        
        # Center the window
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Settings content would go here
        ttk.Label(settings_window, text="Settings", font=self.fonts['large']).pack(pady=20)
        ttk.Label(settings_window, text="Settings interface coming soon!").pack(pady=20)
        
        ttk.Button(settings_window, text="Close", command=settings_window.destroy).pack(pady=20)
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """LocalMind - LIVE-OFFLINE AI Assistant

Version: 1.0.0
An intelligent offline AI assistant for education, healthcare, and general assistance.

Features:
• Complete offline operation
• Domain-specific expertise
• Quantized AI models
• Secure local processing
• Multi-language support

Built with Python and Tkinter
© 2024 LocalMind Project"""
        
        messagebox.showinfo("About LocalMind", about_text)
    
    def _show_help(self):
        """Show help dialog."""
        help_text = """LocalMind User Guide

Getting Started:
1. Select your domain (General, Education, Healthcare)
2. Type your question in the input box
3. Press Send or Ctrl+Enter to submit

Domains:
• General: General assistance and information
• Education: Academic help and tutoring
• Healthcare: Medical information and guidance

Tips:
• Use clear, specific questions for best results
• Switch domains based on your topic
• Save sessions to resume later
• Export chats for reference

Keyboard Shortcuts:
• Ctrl+Enter: Send message
• Ctrl+N: New session
• Ctrl+S: Save session"""
        
        messagebox.showinfo("LocalMind Help", help_text)
    
    def _on_closing(self):
        """Handle window closing."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit LocalMind?"):
            self.root.destroy()
