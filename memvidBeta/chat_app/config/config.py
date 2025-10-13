"""
Configuration management for the Memvid Chat system.
Handles loading of environment variables and configuration settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import json

# Determine the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from .env file
env_path = PROJECT_ROOT / "config" / ".env"
load_dotenv(dotenv_path=env_path)

# API Keys
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Paths
MEMVID_OUTPUT_DIR = os.getenv("MEMVID_OUTPUT_DIR", str(PROJECT_ROOT.parent / "encoder_app" / "outputs"))

# LLM Settings
# Updated model name to the correct format for OpenRouter
MODEL_NAME = os.getenv("MODEL_NAME", "anthropic/claude-3.7-sonnet")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1500"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Retrieval Settings
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "500"))
DEFAULT_OVERLAP = int(os.getenv("DEFAULT_OVERLAP", "50"))

# Database Settings
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT}/database/conversations.db")

# Telegram Settings
ADMIN_USER_IDS = [int(id.strip()) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id.strip()]
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "t", "yes")


class UserSettings:
    """Class to manage user-specific settings."""
    
    DEFAULT_SETTINGS = {
        "top_k": DEFAULT_TOP_K,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "current_document": None,
        "beta_mode": False
    }
    
    def __init__(self):
        self.settings_dir = PROJECT_ROOT / "config" / "user_settings"
        self.settings_dir.mkdir(exist_ok=True)
        self.user_settings = {}
        
    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get settings for a specific user."""
        if user_id in self.user_settings:
            return self.user_settings[user_id]
        
        # Try to load from file
        settings_file = self.settings_dir / f"{user_id}.json"
        if settings_file.exists():
            try:
                with open(settings_file, "r") as f:
                    settings = json.load(f)
                self.user_settings[user_id] = settings
                return settings
            except Exception as e:
                print(f"Error loading settings for user {user_id}: {e}")
        
        # Return default settings if no saved settings found
        self.user_settings[user_id] = self.DEFAULT_SETTINGS.copy()
        return self.user_settings[user_id]
    
    def update_user_setting(self, user_id: int, key: str, value: Any) -> Dict[str, Any]:
        """Update a specific setting for a user."""
        settings = self.get_user_settings(user_id)
        settings[key] = value
        self.save_user_settings(user_id)
        return settings
    
    def save_user_settings(self, user_id: int) -> None:
        """Save user settings to file."""
        if user_id not in self.user_settings:
            return
        
        settings_file = self.settings_dir / f"{user_id}.json"
        with open(settings_file, "w") as f:
            json.dump(self.user_settings[user_id], f, indent=2)
    
    def reset_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Reset user settings to default."""
        self.user_settings[user_id] = self.DEFAULT_SETTINGS.copy()
        self.save_user_settings(user_id)
        return self.user_settings[user_id]


# Create an instance of UserSettings for global use
user_settings_manager = UserSettings()


def get_available_documents() -> List[Dict[str, str]]:
    """Get list of available Memvid documents in the output directory."""
    import logging
    logger = logging.getLogger(__name__)
    
    output_dir = Path(MEMVID_OUTPUT_DIR)
    logger.info(f"Looking for Memvid documents in: {output_dir}")
    
    # Check if directory exists
    if not output_dir.exists():
        logger.warning(f"Output directory does not exist: {output_dir}")
        return []
    
    # Ensure directory is accessible
    try:
        # Try to list directory contents
        files = list(output_dir.iterdir())
        logger.info(f"Found {len(files)} files in output directory")
    except PermissionError:
        logger.error(f"Permission error when accessing output directory: {output_dir}")
        return []
    except Exception as e:
        logger.error(f"Error accessing output directory: {e}")
        return []
    
    # Look for MP4 files
    mp4_files = list(output_dir.glob("*.mp4"))
    logger.info(f"Found {len(mp4_files)} MP4 files")
    
    documents = []
    for file in mp4_files:
        try:
            base_name = file.stem
            index_file = output_dir / f"{base_name}_index.json"
            faiss_file = output_dir / f"{base_name}.faiss"
            
            # Log what we're checking
            logger.debug(f"Checking files for {base_name}:")
            logger.debug(f"  - MP4: {file} (exists: {file.exists()})")
            logger.debug(f"  - Index: {index_file} (exists: {index_file.exists()})")
            logger.debug(f"  - FAISS: {faiss_file} (exists: {faiss_file.exists()})")
            
            # Only add if index file exists
            if index_file.exists():
                # Get file size
                try:
                    file_size = file.stat().st_size
                    size_mb = round(file_size / (1024 * 1024), 2)
                except Exception as e:
                    logger.warning(f"Error getting file size for {file}: {e}")
                    size_mb = 0
                
                # Get modification time
                try:
                    last_modified = file.stat().st_mtime
                except Exception as e:
                    logger.warning(f"Error getting modification time for {file}: {e}")
                    last_modified = 0
                
                # Add document info
                document_info = {
                    "id": base_name,
                    "name": base_name,
                    "video_path": str(file),
                    "index_path": str(index_file),
                    "faiss_path": str(faiss_file) if faiss_file.exists() else None,
                    "size_mb": size_mb,
                    "last_modified": last_modified
                }
                
                documents.append(document_info)
                logger.info(f"Added document: {base_name} ({size_mb:.2f} MB)")
            else:
                logger.warning(f"Skipping {base_name}: index file not found")
        
        except Exception as e:
            logger.error(f"Error processing file {file}: {e}")
    
    # Sort by last modified (newest first)
    documents.sort(key=lambda x: x["last_modified"], reverse=True)
    
    logger.info(f"Returning {len(documents)} valid documents")
    return documents


def validate_env_vars() -> List[str]:
    """Validate that all required environment variables are set."""
    missing_vars = []
    
    if not TELEGRAM_BOT_TOKEN:
        missing_vars.append("TELEGRAM_BOT_TOKEN")
    
    if not OPENROUTER_API_KEY:
        missing_vars.append("OPENROUTER_API_KEY")
    
    return missing_vars
