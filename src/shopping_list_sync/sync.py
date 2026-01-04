"""Todoist synchronization module for Shopping List Sync."""

import os
import signal
import sys
import threading
import time
from typing import Dict, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from todoist_api_python.api import TodoistAPI
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from shopping_list_sync.config import settings
from shopping_list_sync.organizer import organize_shopping_list
from shopping_list_sync.state import SyncState


def create_todoist_retry_decorator():
    """Create a retry decorator for Todoist API calls."""
    return retry(
        retry=retry_if_exception_type((
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError
        )),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, log_level="WARNING"),
        reraise=True
    )


class ShoppingListSync:
    """Shopping list synchronization manager."""

    def __init__(self, sync_interval: int = None):
        """Initialize the sync manager.

        Args:
            sync_interval: Sync interval in seconds (default from settings)
        """
        self.sync_interval = sync_interval or settings.SYNC_INTERVAL_SECONDS
        self.state = SyncState(str(settings.STATE_FILE))
        self.todoist_client = TodoistAPI(settings.TODOIST_API_KEY)
        self._lock = threading.Lock()
        self._scheduler: Optional[BackgroundScheduler] = None

        # Load existing state
        self.state.load()

    @create_todoist_retry_decorator()
    def _get_shopping_project_id(self) -> Optional[str]:
        """Get the shopping list project ID."""
        try:
            # Try ID first if configured
            if settings.TODOIST_SHOPPING_PROJECT_ID:
                try:
                    project = self.todoist_client.get_project(
                        project_id=settings.TODOIST_SHOPPING_PROJECT_ID
                    )
                    return project.id
                except Exception:
                    logger.warning(
                        f"Project ID {settings.TODOIST_SHOPPING_PROJECT_ID} not found, "
                        f"falling back to name search"
                    )

            # Fall back to name search
            projects = self.todoist_client.get_projects()
            shopping_project = next(
                (p for p in projects if p.name == settings.TODOIST_SHOPPING_PROJECT_NAME),
                None
            )
            return shopping_project.id if shopping_project else None
        except Exception as e:
            logger.error(f"Failed to get shopping project: {e}")
            raise

    @create_todoist_retry_decorator()
    def _get_current_tasks_state(self, project_id: str) -> Dict:
        """Get current state of all tasks in the shopping list."""
        try:
            tasks = self.todoist_client.get_tasks(project_id=project_id)
            return {
                task.id: {
                    'content': task.content,
                    'section_id': task.section_id,
                    'is_completed': task.is_completed
                }
                for task in tasks
            }
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            raise

    def check_and_sync(self) -> None:
        """Check for changes in Todoist and sync them."""
        with self._lock:
            try:
                logger.info("Starting Todoist sync check...")

                # Get the shopping list project
                project_id = self._get_shopping_project_id()
                if not project_id:
                    logger.warning(
                        f"Shopping list project '{settings.TODOIST_SHOPPING_PROJECT_NAME}' not found"
                    )
                    return

                # Get current and previous states
                current_state = self._get_current_tasks_state(project_id)

                # Check for changes
                if self.state.has_changed(current_state):
                    logger.info("Changes detected in shopping list, organizing items...")
                    try:
                        organize_shopping_list()
                        # Only update state if organization was successful
                        self.state.update(current_state)
                        self.state.save()
                        logger.info("Shopping list organization completed successfully")
                    except Exception as e:
                        logger.error(f"Failed to organize shopping list: {e}")
                        logger.exception(e)
                        # Don't save state so we can retry next time
                        raise
                else:
                    logger.info("No changes detected in shopping list")

                logger.info("Todoist sync check completed")
            except Exception as e:
                logger.error(f"Todoist sync check failed: {e}")
                logger.exception(e)
                raise

    def health_check(self) -> bool:
        """Verify Todoist API connectivity and project access.

        Returns:
            True if health check passed, False otherwise
        """
        try:
            logger.info("Running health check...")

            # Check Todoist API connectivity
            project_id = self._get_shopping_project_id()
            if not project_id:
                logger.error(
                    f"Health check failed: Shopping list project "
                    f"'{settings.TODOIST_SHOPPING_PROJECT_NAME}' not found"
                )
                return False

            project = self.todoist_client.get_project(project_id=project_id)
            logger.info(f"✓ Connected to Todoist project: {project.name} (ID: {project.id})")

            # Check if we have sections
            sections = self.todoist_client.get_sections(project_id=project_id)
            logger.info(f"✓ Found {len(sections)} sections in project")

            logger.info("Health check passed!")
            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            logger.exception(e)
            return False

    def start(self) -> None:
        """Start the sync scheduler in daemon mode."""
        logger.info(f"Starting Shopping List Sync daemon (interval: {self.sync_interval}s)...")

        # Create scheduler
        self._scheduler = BackgroundScheduler(timezone=settings.SCHEDULER_TIMEZONE)
        self._scheduler.add_job(
            self.check_and_sync,
            'interval',
            seconds=self.sync_interval,
            id='shopping_sync',
            max_instances=1  # Prevent overlapping runs
        )

        # Set up signal handlers for graceful shutdown
        def shutdown_handler(signum, frame):
            logger.info("Received shutdown signal, stopping scheduler...")
            if self._scheduler:
                self._scheduler.shutdown()
            logger.info("Scheduler stopped. Exiting.")
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        # Start scheduler
        self._scheduler.start()
        logger.info("Scheduler started. Press Ctrl+C to stop.")

        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down...")
            if self._scheduler:
                self._scheduler.shutdown()

    def stop(self) -> None:
        """Stop the sync scheduler."""
        if self._scheduler:
            logger.info("Stopping scheduler...")
            self._scheduler.shutdown()
            self._scheduler = None
