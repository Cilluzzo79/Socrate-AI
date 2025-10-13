"""
Main entry point for the Memvid Chat system.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Setup logging first
from config.logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

# Import local modules
from utils.helpers import initialize_project_directories
from database.models import init_db
from database.operations import sync_documents
from config.config import validate_env_vars, MEMVID_OUTPUT_DIR


def initialize_system():
    """Initialize the system."""
    logger.info("Initializing Memvid Chat system...")
    
    # Initialize project directories
    try:
        logger.info("Initializing project directories...")
        initialize_project_directories()
        logger.info("Project directories initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize project directories: {e}", exc_info=True)
        return False
    
    # Validate environment variables
    logger.info("Validating environment variables...")
    missing_vars = validate_env_vars()
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in the .env file or environment.")
        return False
    
    # Verify output directory exists
    output_dir = Path(MEMVID_OUTPUT_DIR)
    logger.info(f"Checking output directory: {output_dir}")
    if not output_dir.exists():
        logger.warning(f"Output directory does not exist: {output_dir}")
        try:
            logger.info("Attempting to create output directory...")
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        except Exception as e:
            logger.error(f"Failed to create output directory: {e}", exc_info=True)
            print(f"ERROR: Failed to create output directory: {e}")
            return False
    
    # Verify output directory is accessible
    try:
        files = list(output_dir.iterdir())
        logger.info(f"Output directory exists and contains {len(files)} files")
    except PermissionError:
        logger.error(f"Permission denied when accessing output directory: {output_dir}")
        print(f"ERROR: Permission denied when accessing output directory: {output_dir}")
        return False
    except Exception as e:
        logger.error(f"Error accessing output directory: {e}", exc_info=True)
        print(f"ERROR: Error accessing output directory: {e}")
        return False
    
    # Initialize database
    try:
        logger.info("Initializing database...")
        engine = init_db()
        logger.info("Database initialized successfully")
        print("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        print(f"ERROR: Failed to initialize database: {e}")
        return False
    
    # Sync documents
    try:
        logger.info("Synchronizing documents...")
        documents = sync_documents()
        logger.info(f"Synchronized {len(documents)} documents")
        print(f"Synchronized {len(documents)} documents.")
    except Exception as e:
        logger.error(f"Failed to synchronize documents: {e}", exc_info=True)
        print(f"ERROR: Failed to synchronize documents: {e}")
        return False
    
    logger.info("System initialization completed successfully")
    return True


def main():
    """Main entry point."""
    print("Initializing Memvid Chat system...")
    if not initialize_system():
        logger.error("Initialization failed. Exiting...")
        print("Initialization failed. Check the logs for details.")
        return
    
    # Start Telegram bot
    try:
        logger.info("Starting Telegram bot...")
        print("Starting Telegram bot...")
        # Import the bot module from telegram_bot directory
        from telegram_bot.bot import run_bot
        run_bot()
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}", exc_info=True)
        print(f"ERROR: Failed to start Telegram bot: {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
