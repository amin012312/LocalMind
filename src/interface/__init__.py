"""
Interface Package for LocalMind

Contains CLI and GUI interface components.
"""

from .cli import LocalMindCLI
from .gui import LocalMindGUI

__all__ = ['LocalMindCLI', 'LocalMindGUI']
