"""
Base watcher abstract class for Personal AI Employee.

Provides common interface for all watcher implementations
(file system, email, messaging, etc.).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Any
import time


class BaseWatcher(ABC):
    """Abstract base class for all watchers."""

    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize base watcher.

        Args:
            vault_path: Path to Obsidian vault
            check_interval: Check interval in seconds
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.running = False

    @abstractmethod
    def check_for_updates(self) -> List[Any]:
        """
        Check for new items to process.

        Returns:
            List of new items detected
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Any) -> Path:
        """
        Create action file in Needs_Action folder.

        Args:
            item: Item to create action file for

        Returns:
            Path to created action file
        """
        pass

    def start(self):
        """Start the watcher loop."""
        self.running = True
        self.run()

    def stop(self):
        """Stop the watcher loop."""
        self.running = False

    def run(self):
        """
        Main watcher loop.

        Continuously checks for updates and creates action files.
        """
        while self.running:
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
            except Exception as e:
                # Log error but continue running
                print(f"Error in watcher loop: {e}")

            time.sleep(self.check_interval)
