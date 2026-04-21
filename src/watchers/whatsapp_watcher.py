"""
WhatsApp watcher for Personal AI Employee (Silver Tier).

Monitors WhatsApp Web for urgent messages using Playwright.
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


class WhatsAppWatcher(BaseWatcher):
    """Watches WhatsApp Web for urgent messages."""

    def __init__(self, vault_path: str, logger: VaultLogger, vault_manager: VaultManager,
                 session_path: str, keywords: List[str], check_interval: int = 30):
        """
        Initialize WhatsApp watcher.

        Args:
            vault_path: Path to Obsidian vault
            logger: Logger instance
            vault_manager: Vault manager instance
            session_path: Path to store WhatsApp session
            keywords: List of urgent keywords to monitor
            check_interval: Check interval in seconds (default 30)
        """
        super().__init__(vault_path, check_interval)
        self.logger = logger
        self.vault_manager = vault_manager
        self.session_path = Path(session_path)
        self.keywords = [kw.lower() for kw in keywords]
        self.processed_messages = set()

        # Playwright will be initialized on first run
        self.browser = None
        self.context = None
        self.page = None

    def _initialize_browser(self):
        """Initialize Playwright browser with persistent session."""
        try:
            from playwright.sync_api import sync_playwright

            self.logger.info("Initializing WhatsApp Web browser...")

            # Create session directory
            self.session_path.mkdir(parents=True, exist_ok=True)

            # Launch persistent browser context
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,  # Must be False for QR code scan
                args=['--no-sandbox']
            )

            self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
            self.page.goto('https://web.whatsapp.com')

            self.logger.info("WhatsApp Web opened. Please scan QR code if needed.")
            self.logger.info("Waiting for WhatsApp to load...")

            # Wait for chat list to appear (indicates successful login)
            try:
                self.page.wait_for_selector('[data-testid="chat-list"]', timeout=60000)
                self.logger.info("WhatsApp Web loaded successfully")
            except Exception as e:
                self.logger.error(f"Failed to load WhatsApp Web: {e}")
                self.logger.error("Please ensure you've scanned the QR code")
                raise

        except ImportError:
            self.logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize WhatsApp browser: {e}", exc_info=True)
            raise

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check WhatsApp Web for new urgent messages.

        Returns:
            List of message info dictionaries
        """
        if not self.page:
            self._initialize_browser()

        new_messages = []

        try:
            # Find unread chats
            unread_chats = self.page.query_selector_all('[aria-label*="unread"]')

            for chat in unread_chats[:5]:  # Process max 5 at a time
                try:
                    # Get chat text
                    chat_text = chat.inner_text().lower()

                    # Check for urgent keywords
                    has_urgent_keyword = any(keyword in chat_text for keyword in self.keywords)

                    if has_urgent_keyword:
                        # Extract message details
                        message_info = self._extract_message_info(chat, chat_text)

                        # Skip if already processed
                        message_key = f"{message_info['sender']}_{message_info['timestamp']}"
                        if message_key in self.processed_messages:
                            continue

                        new_messages.append(message_info)
                        self.processed_messages.add(message_key)

                        self.logger.info(f"WhatsApp urgent message detected from: {message_info['sender']}")

                except Exception as e:
                    self.logger.error(f"Error processing WhatsApp chat: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error checking WhatsApp: {e}", exc_info=True)

        return new_messages

    def _extract_message_info(self, chat_element, chat_text: str) -> Dict[str, Any]:
        """
        Extract message information from chat element.

        Args:
            chat_element: Playwright element for chat
            chat_text: Text content of chat

        Returns:
            Dictionary with message info
        """
        # Extract sender name (first line usually)
        lines = chat_text.split('\n')
        sender = lines[0] if lines else 'Unknown'

        # Extract message text (skip sender and timestamp)
        message_text = '\n'.join(lines[1:]) if len(lines) > 1 else chat_text

        # Determine urgency based on keywords
        urgency = 'high'
        for keyword in self.keywords:
            if keyword in chat_text:
                urgency = 'high'
                break

        return {
            'sender': sender,
            'message': message_text,
            'urgency': urgency,
            'timestamp': datetime.now()
        }

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create action file for WhatsApp message.

        Args:
            item: Message info dictionary

        Returns:
            Path to created action file
        """
        try:
            sender = item['sender']
            timestamp = item['timestamp']

            # Generate unique action file name
            timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
            # Clean sender name for filename
            sender_clean = ''.join(c for c in sender if c.isalnum() or c in (' ', '_')).strip()
            sender_clean = sender_clean.replace(' ', '_')[:20]

            action_filename = f"WHATSAPP_{sender_clean}_{timestamp_str}.md"
            action_filepath = self.needs_action / action_filename

            # Create action file content
            content = self._create_action_content(item)

            # Write action file
            action_filepath.write_text(content, encoding='utf-8')

            self.logger.info(f"Created WhatsApp action item: {action_filename}")

            # Update dashboard
            self.vault_manager.update_dashboard(
                "whatsapp_detected",
                {"sender": sender, "urgency": item['urgency']}
            )

            return action_filepath

        except Exception as e:
            self.logger.error(f"Error creating WhatsApp action file: {e}", exc_info=True)
            raise

    def _create_action_content(self, item: Dict[str, Any]) -> str:
        """
        Create action file content for WhatsApp message.

        Args:
            item: Message info dictionary

        Returns:
            Markdown content with frontmatter
        """
        timestamp_readable = item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

        content = f"""---
type: whatsapp
sender: {item['sender']}
urgency: {item['urgency']}
timestamp: {item['timestamp'].isoformat()}
status: pending
---

## WhatsApp Message Details

- **From**: {item['sender']}
- **Urgency**: {item['urgency'].upper()}
- **Received**: {timestamp_readable}

## Message Content

{item['message']}

## Suggested Actions

- [ ] Read full conversation in WhatsApp Web
- [ ] Determine appropriate response based on Company Handbook rules
- [ ] Use /process_whatsapp skill to generate suggested response
- [ ] Respond manually via WhatsApp Web (Silver tier)

## Notes

⚠️ Silver tier requires manual WhatsApp responses. Copy suggested response and send via WhatsApp Web.

Add any processing notes here.
"""
        return content

    def run(self):
        """Main watcher loop with enhanced error handling."""
        self.logger.info(f"Starting WhatsAppWatcher (check interval: {self.check_interval}s)")

        # Initialize browser
        try:
            self._initialize_browser()
        except Exception as e:
            self.logger.error(f"Failed to initialize WhatsApp browser: {e}")
            self.logger.error("WhatsApp watcher cannot start. Please check Playwright installation.")
            return

        while self.running:
            try:
                items = self.check_for_updates()
                for item in items:
                    try:
                        self.create_action_file(item)
                    except Exception as e:
                        self.logger.error(f"Error processing WhatsApp message from {item.get('sender', 'unknown')}: {e}")

            except Exception as e:
                self.logger.error(f"Error in WhatsApp watcher loop: {e}", exc_info=True)

            time.sleep(self.check_interval)

        # Cleanup
        if self.browser:
            self.browser.close()

        self.logger.info("WhatsAppWatcher stopped")
