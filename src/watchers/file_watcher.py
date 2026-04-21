"""
File system watcher for Personal AI Employee.

Monitors Inbox folder for new files and creates action items
in Needs_Action folder.
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import os

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.base_watcher import BaseWatcher
from utils.logger import VaultLogger
from utils.vault_manager import VaultManager


class FileWatcher(BaseWatcher):
    """Watches file system for new files in Inbox folder."""

    def __init__(self, vault_path: str, logger: VaultLogger, vault_manager: VaultManager, check_interval: int = 30):
        """
        Initialize file watcher.

        Args:
            vault_path: Path to Obsidian vault
            logger: Logger instance
            vault_manager: Vault manager instance
            check_interval: Check interval in seconds
        """
        super().__init__(vault_path, check_interval)
        self.logger = logger
        self.vault_manager = vault_manager
        self.inbox = self.vault_path / 'Inbox'
        self.errors = self.vault_path / 'Errors'
        self.processed_files = set()

        # Ensure folders exist
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.errors.mkdir(parents=True, exist_ok=True)
        self.needs_action.mkdir(parents=True, exist_ok=True)

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Inbox folder for new files.

        Returns:
            List of file info dictionaries
        """
        if not self.inbox.exists():
            self.logger.warning(f"Inbox folder does not exist: {self.inbox}")
            return []

        new_files = []

        try:
            for file_path in self.inbox.iterdir():
                # Skip directories and hidden files
                if file_path.is_dir() or file_path.name.startswith('.'):
                    continue

                # Skip already processed files
                file_key = str(file_path.absolute())
                if file_key in self.processed_files:
                    continue

                # Get file info
                file_info = {
                    'path': file_path,
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'timestamp': datetime.now()
                }

                new_files.append(file_info)
                self.processed_files.add(file_key)

                self.logger.info(f"File detected: {file_info['name']} ({file_info['size']} bytes)")

        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}", exc_info=True)

        return new_files

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create action file in Needs_Action folder.

        Args:
            item: File info dictionary

        Returns:
            Path to created action file
        """
        try:
            file_path = item['path']
            filename = item['name']
            size = item['size']
            timestamp = item['timestamp']

            # Generate unique action file name
            timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
            action_filename = f"FILE_{filename}_{timestamp_str}.md"
            action_filepath = self.needs_action / action_filename

            # Check for collision (unlikely but possible)
            counter = 1
            while action_filepath.exists():
                action_filename = f"FILE_{filename}_{timestamp_str}_{counter}.md"
                action_filepath = self.needs_action / action_filename
                counter += 1

            # Create action file content
            content = self._create_action_content(filename, size, timestamp)

            # Write action file
            action_filepath.write_text(content, encoding='utf-8')

            self.logger.info(f"Created action item: {action_filename}")

            # Update dashboard
            self.vault_manager.update_dashboard(
                "file_detected",
                {"filename": filename}
            )

            return action_filepath

        except Exception as e:
            self.logger.error(f"Error creating action file: {e}", exc_info=True)
            self._move_to_errors(item['path'], str(e))
            raise

    def _create_action_content(self, filename: str, size: int, timestamp: datetime) -> str:
        """
        Create action file content with YAML frontmatter.

        Args:
            filename: Original filename
            size: File size in bytes
            timestamp: Detection timestamp

        Returns:
            Markdown content with frontmatter
        """
        size_kb = size / 1024
        timestamp_iso = timestamp.isoformat()
        timestamp_readable = timestamp.strftime('%Y-%m-%d %H:%M:%S')

        content = f"""---
type: file_drop
original_name: {filename}
size: {size}
timestamp: {timestamp_iso}
status: pending
---

## File Details

- **Name**: {filename}
- **Size**: {size_kb:.1f} KB
- **Detected**: {timestamp_readable}

## Suggested Actions

- [ ] Review file contents
- [ ] Determine next steps based on Company Handbook rules
- [ ] Move to Done when complete

## Notes

Add any processing notes here.
"""
        return content

    def _move_to_errors(self, file_path: Path, error_message: str):
        """
        Move problematic file to Errors folder.

        Args:
            file_path: Path to file
            error_message: Error description
        """
        try:
            if not file_path.exists():
                return

            error_filename = f"ERROR_{file_path.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            error_filepath = self.errors / error_filename

            # Create error report
            error_content = f"""Error processing file: {file_path.name}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Error: {error_message}

Original file location: {file_path}
"""
            error_filepath.write_text(error_content, encoding='utf-8')

            self.logger.warning(f"Moved problematic file info to Errors: {error_filename}")

        except Exception as e:
            self.logger.error(f"Error moving file to Errors: {e}", exc_info=True)

    def run(self):
        """
        Main watcher loop with enhanced error handling.

        Continuously checks for updates and creates action files.
        """
        self.logger.info(f"Starting FileWatcher (check interval: {self.check_interval}s)")

        while self.running:
            try:
                items = self.check_for_updates()
                for item in items:
                    try:
                        self.create_action_file(item)
                    except Exception as e:
                        self.logger.error(f"Error processing item {item.get('name', 'unknown')}: {e}")
                        # Continue with next item

            except Exception as e:
                self.logger.error(f"Error in watcher loop: {e}", exc_info=True)

            # Sleep for check interval
            import time
            time.sleep(self.check_interval)

        self.logger.info("FileWatcher stopped")
