#!/bin/bash

# Memvid Chat System Launcher Script

echo "==================================="
echo " MEMVID CHAT SYSTEM LAUNCHER"
echo "==================================="
echo

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Start the bot
echo "Starting Memvid Chat system..."
python main.py
