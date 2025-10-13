"""
Utility functions for the Memvid Chat system.
"""

import re
import os
from pathlib import Path
import sys
import logging
from typing import List, Dict, Any, Optional

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))


def format_message_for_console(message: str, sender: str = "User", max_width: int = 80) -> str:
    """
    Format a message for console display with wrapping.
    
    Args:
        message: The message to format
        sender: The sender of the message
        max_width: Maximum width for wrapping
        
    Returns:
        str: Formatted message
    """
    lines = []
    
    # Add header
    header = f"=== {sender} " + "=" * (max_width - len(sender) - 5)
    lines.append(header)
    
    # Wrap message
    current_line = ""
    for word in message.split():
        if len(current_line + " " + word) <= max_width:
            current_line += (" " + word if current_line else word)
        else:
            lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    # Add footer
    footer = "=" * max_width
    lines.append(footer)
    
    return "\n".join(lines)


def clean_telegram_markdown(text: str) -> str:
    """
    Clean text for Telegram Markdown.
    Escapes characters that have special meaning in Markdown.
    
    Args:
        text: The text to clean
        
    Returns:
        str: Cleaned text
    """
    # Characters to escape in Markdown
    special_chars = ['_', '*', '`', '[']
    
    for char in special_chars:
        text = text.replace(char, '\\' + char)
    
    return text


def truncate_text(text: str, max_length: int = 4000, truncate_suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: The text to truncate
        max_length: Maximum length
        truncate_suffix: Suffix to add when truncating
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(truncate_suffix)] + truncate_suffix


def initialize_project_directories():
    """
    Initialize project directories.
    Creates necessary directories if they don't exist.
    """
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Directories to create
    directories = [
        project_root / "database",
        project_root / "logs",
        project_root / "config" / "user_settings"
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
