"""
Main script to start the application with debugging enabled.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(script_dir)
sys.path.append(project_root)

# Import the debug interceptor first to patch the function
import core.llm_debug

# Then import the main app
from main import main

if __name__ == "__main__":
    print("Starting app with debugging enabled...")
    main()
