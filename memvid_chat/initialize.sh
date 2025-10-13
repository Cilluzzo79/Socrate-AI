#!/bin/bash

# Memvid Chat System Initialization Script

echo "==================================="
echo " MEMVID CHAT SYSTEM INITIALIZATION"
echo "==================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies."
    exit 1
fi

# Initialize database
echo "Initializing database..."
python -c "from database.models import init_db; init_db()"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to initialize database."
    exit 1
fi

# Sync documents
echo "Synchronizing documents..."
python -c "from database.operations import sync_documents; sync_documents()"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to synchronize documents."
    exit 1
fi

echo
echo "Initialization complete!"
echo
echo "To start the bot, run: ./start_bot.sh"
echo
