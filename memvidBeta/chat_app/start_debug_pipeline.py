"""
Modified script to start the bot with the full pipeline debugging enabled.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(script_dir)
sys.path.append(project_root)

# Import the debug pipeline patcher first
import debug_pipeline

# Import the main module
from main import main

if __name__ == "__main__":
    print("Starting app with full pipeline debugging enabled...")
    main()
