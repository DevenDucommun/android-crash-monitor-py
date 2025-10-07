"""
Android Crash Monitor

A modern, user-friendly Android crash monitoring tool with rich terminal interface.
"""

__version__ = "2.0.0"
__author__ = "Deven Ducommun"
__description__ = "A modern, user-friendly Android crash monitoring tool"

from .cli import main

__all__ = ['main']