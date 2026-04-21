"""
LinkedIn watcher for Personal AI Employee (Silver Tier).

Monitors Business_Updates folder for new content to post on LinkedIn.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from typing import List, Dict, Any
import time

from watchers.base_watcher import BaseWatcher
from utils.logger import VaultLogger
from utils.vault_manager import VaultManager


class LinkedInWatcher(BaseWatcher):
    """Watches Business_Updates folder for LinkedIn post content."""

    def __init__(self, vault_path: str, logger: VaultLogger, vault_manager: VaultManager,
                 check_interval: int = 60):
        """
        Initialize LinkedIn watcher.

        Args:
            vault_path: Path to Obsidian vault
            logger: Logger instance
            vault_manager: Vault manager instance
            check_interval: Check interval in seconds (default 60)
        """
        super().__init__(vault_path, check_interval)
        self.logger = logger
        self.vault_manager = vault_manager
        self.business_updates = self.vault_path / 'Business_Updates'
        self.processed_files = set()

        # Ensure folder exists
        self.business_updates.mkdir(parents=True, exist_ok=True)

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Business_Updates folder for new files.

        Returns:
            List of file info dictionaries
        """
        if not self.business_updates.exists():
            self.logger.warning(f"Business_Updates folder does not exist: {self.business_updates}")
            return []

        new_files = []

        try:
            for file_path in self.business_updates.iterdir():
                # Skip directories and hidden files
                if file_path.is_dir() or file_path.name.startswith('.'):
                    continue

                # Only process markdown and text files
                if file_path.suffix not in ['.md', '.txt']:
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

                self.logger.info(f"Business update detected: {file_info['name']}")

        except Exception as e:
            self.logger.error(f"Error checking Business_Updates: {e}", exc_info=True)

        return new_files

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create action file for LinkedIn post draft.

        Note: This creates a marker file. The actual LinkedIn post draft
        is created by the /draft_linkedin_post Claude skill.

        Args:
            item: File info dictionary

        Returns:
            Path to created action file
        """
        try:
            file_path = item['path']
            filename = item['name']
            timestamp = item['timestamp']

            # Generate unique action file name
            timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
            action_filename = f"LINKEDIN_draft_{filename.replace('.', '_')}_{timestamp_str}.md"
            action_filepath = self.needs_action / action_filename

            # Create action file content
            content = self._create_action_content(item)

            # Write action file
            action_filepath.write_text(content, encoding='utf-8')

            self.logger.info(f"Created LinkedIn action item: {action_filename}")

            # Update dashboard
            self.vault_manager.update_dashboard(
                "linkedin_update_detected",
                {"filename": filename}
            )

            return action_filepath

        except Exception as e:
            self.logger.error(f"Error creating LinkedIn action file: {e}", exc_info=True)
            raise

    def _create_action_content(self, item: Dict[str, Any]) -> str:
        """
        Create action file content for LinkedIn post.

        Args:
            item: File info dictionary

        Returns:
            Markdown content with frontmatter
        """
        file_path = item['path']
        filename = item['name']
        timestamp_readable = item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

        # Read business update content
        try:
            update_content = file_path.read_text(encoding='utf-8')
            # Limit preview to first 500 characters
            preview = update_content[:500] + ('...' if len(update_content) > 500 else '')
        except Exception as e:
            self.logger.error(f"Error reading business update: {e}")
            preview = "[Error reading file content]"

        content = f"""---
type: linkedin_draft
source_file: {filename}
source_path: Business_Updates/{filename}
timestamp: {item['timestamp'].isoformat()}
status: pending
---

## LinkedIn Post Draft Needed

A new business update has been detected and needs to be drafted as a LinkedIn post.

- **Source File**: {filename}
- **Detected**: {timestamp_readable}

## Business Update Preview

{preview}

## Suggested Actions

- [ ] Use /draft_linkedin_post skill to generate LinkedIn post
- [ ] Review and edit the draft
- [ ] Approve the post for publishing
- [ ] Post manually to LinkedIn (Silver tier)

## Usage

```
/draft_linkedin_post Business_Updates/{filename}
```

This will:
1. Read the business update
2. Generate an engaging LinkedIn post with hashtags
3. Create an approval request in Pending_Approval/
4. Wait for your approval to publish

## Notes

⚠️ Silver tier uses manual LinkedIn posting. After approval, copy the post content and publish via LinkedIn website.

Add any processing notes here.
"""
        return content

    def run(self):
        """Main watcher loop with enhanced error handling."""
        self.logger.info(f"Starting LinkedInWatcher (check interval: {self.check_interval}s)")

        while self.running:
            try:
                items = self.check_for_updates()
                for item in items:
                    try:
                        self.create_action_file(item)
                    except Exception as e:
                        self.logger.error(f"Error processing business update {item.get('name', 'unknown')}: {e}")

            except Exception as e:
                self.logger.error(f"Error in LinkedIn watcher loop: {e}", exc_info=True)

            time.sleep(self.check_interval)

        self.logger.info("LinkedInWatcher stopped")
