"""State management for tracking Todoist sync changes."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from loguru import logger


class SyncState:
    """Manages synchronization state for Todoist tasks."""

    def __init__(self, state_file: str = "data/sync_state.json"):
        """Initialize sync state manager.

        Args:
            state_file: Path to the JSON file for storing state
        """
        self.state_file = Path(state_file)
        self.tasks_state: Dict = {}  # task_id -> {content, section_id, is_completed}
        self.last_sync: Optional[datetime] = None

    def load(self) -> None:
        """Load state from JSON file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.tasks_state = data.get('tasks', {})
                    last_sync_str = data.get('last_sync')
                    if last_sync_str:
                        self.last_sync = datetime.fromisoformat(last_sync_str)
                logger.debug(f"Loaded state with {len(self.tasks_state)} tasks")
        except Exception as e:
            logger.error(f"Failed to load state from {self.state_file}: {e}")
            # Start with empty state if loading fails
            self.tasks_state = {}
            self.last_sync = None

    def save(self) -> None:
        """Save state to JSON file with atomic write."""
        try:
            # Ensure parent directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write: write to temp file, then rename
            temp_file = self.state_file.with_suffix('.tmp')
            state_dict = {
                'tasks': self.tasks_state,
                'last_sync': self.last_sync.isoformat() if self.last_sync else None
            }

            with open(temp_file, 'w') as f:
                json.dump(state_dict, f, indent=2)

            # Rename temp file to actual file (atomic operation)
            temp_file.replace(self.state_file)

            logger.debug(f"Saved state with {len(self.tasks_state)} tasks")
        except Exception as e:
            logger.error(f"Failed to save state to {self.state_file}: {e}")
            raise

    def has_changed(self, current_state: Dict) -> bool:
        """Check if the current state differs from stored state.

        Args:
            current_state: Dictionary of current task states

        Returns:
            True if state has changed, False otherwise
        """
        return current_state != self.tasks_state

    def update(self, new_state: Dict) -> None:
        """Update state with new task information.

        Args:
            new_state: Dictionary of new task states
        """
        self.tasks_state = new_state
        self.last_sync = datetime.utcnow()
