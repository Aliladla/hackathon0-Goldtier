"""
Vault management utilities for Personal AI Employee.

Provides functions for vault path validation, folder creation,
and dashboard updates.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class VaultManager:
    """Manages Obsidian vault operations."""

    REQUIRED_FOLDERS = [
        "Inbox",
        "Needs_Action",
        "Done",
        "Errors",
        "Logs",
        "Pending_Approval",  # Silver tier
        "Approved",          # Silver tier
        "Rejected",          # Silver tier
        "Briefings",         # Silver tier
        "Business_Updates"   # Silver tier
    ]

    def __init__(self, vault_path: str):
        """
        Initialize vault manager.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)

    def validate_vault(self) -> bool:
        """
        Validate that vault path exists and is accessible.

        Returns:
            True if valid, False otherwise
        """
        if not self.vault_path.exists():
            return False

        if not self.vault_path.is_dir():
            return False

        return True

    def create_vault_structure(self):
        """Create required vault folders if they don't exist."""
        self.vault_path.mkdir(parents=True, exist_ok=True)

        for folder in self.REQUIRED_FOLDERS:
            folder_path = self.vault_path / folder
            folder_path.mkdir(exist_ok=True)

    def get_folder_path(self, folder_name: str) -> Path:
        """
        Get path to a vault folder.

        Args:
            folder_name: Name of folder (e.g., "Inbox", "Needs_Action")

        Returns:
            Path to folder
        """
        return self.vault_path / folder_name

    def count_files_in_folder(self, folder_name: str) -> int:
        """
        Count markdown files in a folder.

        Args:
            folder_name: Name of folder

        Returns:
            Number of .md files
        """
        folder_path = self.get_folder_path(folder_name)
        if not folder_path.exists():
            return 0

        return len(list(folder_path.glob("*.md")))

    def update_dashboard(self, event_type: str, event_data: Dict[str, Any]):
        """
        Update Dashboard.md with new event.

        Args:
            event_type: Type of event (e.g., "file_detected", "system_startup")
            event_data: Event details
        """
        dashboard_path = self.vault_path / "Dashboard.md"

        # Read existing dashboard or create new
        if dashboard_path.exists():
            content = dashboard_path.read_text(encoding='utf-8')
        else:
            content = self._create_dashboard_template()

        # Update timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        content = self._update_timestamp(content, timestamp)

        # Update system status
        content = self._update_system_status(content, "Active")

        # Update pending count
        pending_count = self.count_files_in_folder("Needs_Action")
        content = self._update_pending_count(content, pending_count)

        # Add to recent activity
        activity_line = self._format_activity(event_type, event_data, timestamp)
        content = self._add_recent_activity(content, activity_line)

        # Write back
        dashboard_path.write_text(content, encoding='utf-8')

    def _create_dashboard_template(self) -> str:
        """Create initial dashboard template."""
        return """# Dashboard

**Last Updated**: {timestamp}
**System Status**: Inactive

## Pending Actions (0)

No pending actions.

## Recent Activity

No recent activity.

## Quick Links

- [Needs Action](Needs_Action/)
- [Done](Done/)
- [Logs](Logs/)
- [Company Handbook](Company_Handbook.md)
"""

    def _update_timestamp(self, content: str, timestamp: str) -> str:
        """Update last updated timestamp."""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('**Last Updated**:'):
                lines[i] = f'**Last Updated**: {timestamp}'
                break
        return '\n'.join(lines)

    def _update_system_status(self, content: str, status: str) -> str:
        """Update system status."""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('**System Status**:'):
                lines[i] = f'**System Status**: {status}'
                break
        return '\n'.join(lines)

    def _update_pending_count(self, content: str, count: int) -> str:
        """Update pending actions count."""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('## Pending Actions'):
                lines[i] = f'## Pending Actions ({count})'
                break
        return '\n'.join(lines)

    def _format_activity(self, event_type: str, event_data: Dict[str, Any], timestamp: str) -> str:
        """Format activity line."""
        time_only = timestamp.split(' ')[1]  # HH:MM:SS

        if event_type == "file_detected":
            filename = event_data.get('filename', 'unknown')
            return f"- [{time_only}] New file detected: {filename}"
        elif event_type == "system_startup":
            return f"- [{time_only}] System started"
        elif event_type == "file_processed":
            filename = event_data.get('filename', 'unknown')
            return f"- [{time_only}] File processed: {filename}"
        else:
            return f"- [{time_only}] {event_type}"

    def _add_recent_activity(self, content: str, activity_line: str, max_items: int = 10) -> str:
        """Add activity line to recent activity section."""
        lines = content.split('\n')

        # Find Recent Activity section
        activity_index = -1
        for i, line in enumerate(lines):
            if line.startswith('## Recent Activity'):
                activity_index = i
                break

        if activity_index == -1:
            return content

        # Find next section or end
        next_section_index = len(lines)
        for i in range(activity_index + 1, len(lines)):
            if lines[i].startswith('##'):
                next_section_index = i
                break

        # Extract existing activities
        existing_activities = []
        for i in range(activity_index + 1, next_section_index):
            line = lines[i].strip()
            if line.startswith('- ['):
                existing_activities.append(line)

        # Add new activity at the top
        new_activities = [activity_line] + existing_activities

        # Keep only last max_items
        new_activities = new_activities[:max_items]

        # Rebuild content
        new_lines = lines[:activity_index + 1]
        new_lines.append('')
        new_lines.extend(new_activities)
        new_lines.append('')
        new_lines.extend(lines[next_section_index:])

        return '\n'.join(new_lines)


def create_vault_manager(vault_path: str) -> VaultManager:
    """
    Factory function to create a VaultManager instance.

    Args:
        vault_path: Path to Obsidian vault

    Returns:
        VaultManager instance
    """
    return VaultManager(vault_path)
