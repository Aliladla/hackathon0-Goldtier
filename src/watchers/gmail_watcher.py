"""
Gmail watcher for Personal AI Employee (Silver Tier).

Monitors Gmail inbox for important messages using Gmail API.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from typing import List, Dict, Any
from googleapiclient.errors import HttpError

from watchers.base_watcher import BaseWatcher
from utils.logger import VaultLogger
from utils.vault_manager import VaultManager
from utils.gmail_auth import GmailAuthManager
from utils.retry_handler import with_retry


class GmailWatcher(BaseWatcher):
    """Watches Gmail inbox for important messages."""

    def __init__(self, vault_path: str, logger: VaultLogger, vault_manager: VaultManager,
                 credentials_path: str, token_path: str, check_interval: int = 120):
        """
        Initialize Gmail watcher.

        Args:
            vault_path: Path to Obsidian vault
            logger: Logger instance
            vault_manager: Vault manager instance
            credentials_path: Path to Gmail OAuth2 credentials
            token_path: Path to Gmail OAuth2 token
            check_interval: Check interval in seconds (default 120 = 2 minutes)
        """
        super().__init__(vault_path, check_interval)
        self.logger = logger
        self.vault_manager = vault_manager
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.processed_message_ids = set()

        # Initialize Gmail auth
        self.auth_manager = GmailAuthManager(credentials_path, token_path)
        self.gmail_service = None

    def _initialize_service(self):
        """Initialize Gmail API service."""
        if not self.gmail_service:
            try:
                self.gmail_service = self.auth_manager.get_gmail_service()
                self.logger.info("Gmail API service initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gmail service: {e}", exc_info=True)
                raise

    @with_retry(max_retries=3, base_delay=2.0)
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Gmail inbox for new important messages.

        Returns:
            List of message info dictionaries
        """
        if not self.gmail_service:
            self._initialize_service()

        new_messages = []

        try:
            # Query for important or starred messages
            query = 'is:unread (is:important OR is:starred)'

            results = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10
            ).execute()

            messages = results.get('messages', [])

            for message in messages:
                message_id = message['id']

                # Skip if already processed
                if message_id in self.processed_message_ids:
                    continue

                # Get full message details
                msg = self.gmail_service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()

                # Extract message info
                message_info = self._extract_message_info(msg)
                new_messages.append(message_info)
                self.processed_message_ids.add(message_id)

                self.logger.info(f"Gmail message detected: {message_info['subject']} from {message_info['from']}")

        except HttpError as e:
            if e.resp.status == 429:
                self.logger.warning("Gmail API rate limit hit")
                raise  # Will be retried by @with_retry
            else:
                self.logger.error(f"Gmail API error: {e}", exc_info=True)
                raise
        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}", exc_info=True)
            raise

        return new_messages

    def _extract_message_info(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant information from Gmail message.

        Args:
            msg: Gmail API message object

        Returns:
            Dictionary with message info
        """
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}

        # Get message snippet
        snippet = msg.get('snippet', '')

        # Get labels
        labels = msg.get('labelIds', [])

        # Determine importance
        importance = 'high' if 'IMPORTANT' in labels or 'STARRED' in labels else 'normal'

        return {
            'message_id': msg['id'],
            'thread_id': msg['threadId'],
            'from': headers.get('From', 'Unknown'),
            'to': headers.get('To', ''),
            'subject': headers.get('Subject', 'No Subject'),
            'date': headers.get('Date', ''),
            'snippet': snippet,
            'labels': labels,
            'importance': importance,
            'timestamp': datetime.now()
        }

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create action file for Gmail message.

        Args:
            item: Message info dictionary

        Returns:
            Path to created action file
        """
        try:
            message_id = item['message_id']
            timestamp = item['timestamp']

            # Generate unique action file name
            timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
            action_filename = f"EMAIL_{message_id[:8]}_{timestamp_str}.md"
            action_filepath = self.needs_action / action_filename

            # Create action file content
            content = self._create_action_content(item)

            # Write action file
            action_filepath.write_text(content, encoding='utf-8')

            self.logger.info(f"Created email action item: {action_filename}")

            # Update dashboard
            self.vault_manager.update_dashboard(
                "email_detected",
                {"subject": item['subject'], "from": item['from']}
            )

            return action_filepath

        except Exception as e:
            self.logger.error(f"Error creating email action file: {e}", exc_info=True)
            raise

    def _create_action_content(self, item: Dict[str, Any]) -> str:
        """
        Create action file content for email.

        Args:
            item: Message info dictionary

        Returns:
            Markdown content with frontmatter
        """
        timestamp_readable = item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

        content = f"""---
type: email
message_id: {item['message_id']}
thread_id: {item['thread_id']}
from: {item['from']}
to: {item['to']}
subject: {item['subject']}
received: {item['timestamp'].isoformat()}
importance: {item['importance']}
labels: {item['labels']}
status: pending
---

## Email Details

- **From**: {item['from']}
- **Subject**: {item['subject']}
- **Received**: {timestamp_readable}
- **Importance**: {item['importance'].capitalize()}

## Email Snippet

{item['snippet']}

## Suggested Actions

- [ ] Read full email in Gmail
- [ ] Draft reply based on Company Handbook rules
- [ ] Use /process_email skill to generate draft
- [ ] Respond within 24 hours (client communication rule)

## Notes

Add any processing notes here.
"""
        return content

    def run(self):
        """Main watcher loop with enhanced error handling."""
        self.logger.info(f"Starting GmailWatcher (check interval: {self.check_interval}s)")

        # Initialize service
        try:
            self._initialize_service()
        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail service: {e}")
            self.logger.error("Gmail watcher cannot start. Please run: python src/utils/gmail_auth.py")
            return

        while self.running:
            try:
                items = self.check_for_updates()
                for item in items:
                    try:
                        self.create_action_file(item)
                    except Exception as e:
                        self.logger.error(f"Error processing email {item.get('subject', 'unknown')}: {e}")

            except Exception as e:
                self.logger.error(f"Error in Gmail watcher loop: {e}", exc_info=True)

            import time
            time.sleep(self.check_interval)

        self.logger.info("GmailWatcher stopped")
