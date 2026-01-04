"""Configuration management for Shopping List Sync."""

import os
from pathlib import Path
from typing import Dict, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # API Keys
    TODOIST_API_KEY: str = os.getenv('TODOIST_API_KEY', '')
    TODOIST_SHOPPING_PROJECT_NAME: str = os.getenv('TODOIST_SHOPPING_PROJECT_NAME', 'shopping')
    TODOIST_SHOPPING_PROJECT_ID: Optional[str] = os.getenv('TODOIST_SHOPPING_PROJECT_ID')
    TODOIST_SYSTEM_PROJECT_ID: Optional[str] = os.getenv('TODOIST_SYSTEM_PROJECT_ID')

    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    # Sync Configuration
    SYNC_INTERVAL_SECONDS: int = int(os.getenv('SYNC_INTERVAL_SECONDS', '60'))
    CATEGORIES_FILE: str = os.getenv('CATEGORIES_FILE', 'config/categories.yaml')

    # State Management
    STATE_FILE: Path = Path(os.getenv('STATE_FILE', 'data/sync_state.json'))

    # Scheduler
    SCHEDULER_TIMEZONE: str = os.getenv('SCHEDULER_TIMEZONE', 'UTC')

    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: Optional[Path] = Path(os.getenv('LOG_FILE')) if os.getenv('LOG_FILE') else None

    # Error Handling
    ERROR_HANDLING_MODE: str = os.getenv('ERROR_HANDLING_MODE', 'log')  # log, task, or both


settings = Settings()


def load_categories() -> Dict:
    """Load category mappings from YAML configuration file."""
    categories_path = Path(settings.CATEGORIES_FILE)

    if not categories_path.exists():
        raise FileNotFoundError(
            f"Categories file not found: {categories_path}. "
            f"Please ensure {settings.CATEGORIES_FILE} exists."
        )

    with open(categories_path, 'r') as f:
        config = yaml.safe_load(f)

    if 'categories' not in config:
        raise ValueError("Categories file must contain a 'categories' key")

    return config['categories']


def get_config_summary() -> str:
    """Get a summary of current configuration for logging."""
    return f"""Configuration:
  Todoist Project: {settings.TODOIST_SHOPPING_PROJECT_NAME} (ID: {settings.TODOIST_SHOPPING_PROJECT_ID or 'auto-detect'})
  OpenAI Model: {settings.OPENAI_MODEL}
  Sync Interval: {settings.SYNC_INTERVAL_SECONDS}s
  Categories File: {settings.CATEGORIES_FILE}
  Error Handling: {settings.ERROR_HANDLING_MODE}
  Log Level: {settings.LOG_LEVEL}
"""
