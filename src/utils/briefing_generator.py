"""
Briefing generation utilities for Personal AI Employee (Silver Tier).

Generates daily briefings with pending actions, priorities, and focus areas.
"""

from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import re


class BriefingGenerator:
    """Generates daily briefings for the AI Employee."""

    def __init__(self, vault_path: str, logger):
        """
        Initialize briefing generator.

        Args:
            vault_path: Path to Obsidian vault
            logger: Logger instance
        """
        self.vault_path = Path(vault_path)
        self.logger = logger

    def generate_briefing(self) -> Path:
        """
        Generate daily briefing.

        Returns:
            Path to generated briefing file
        """
        self.logger.info("Generating daily briefing...")

        # Collect data
        pending_actions = self._get_pending_actions()
        recent_activity = self._get_recent_activity()
        priorities = self._identify_priorities(pending_actions)
        system_health = self._check_system_health()

        # Generate briefing content
        briefing_content = self._create_briefing_content(
            pending_actions, recent_activity, priorities, system_health
        )

        # Save briefing
        briefing_path = self._save_briefing(briefing_content)

        self.logger.info(f"Briefing generated: {briefing_path.name}")

        return briefing_path

    def _get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get all pending action items."""
        needs_action = self.vault_path / 'Needs_Action'
        pending = []

        if not needs_action.exists():
            return pending

        for file_path in needs_action.glob('*.md'):
            try:
                content = file_path.read_text(encoding='utf-8')
                frontmatter = self._parse_frontmatter(content)

                if frontmatter:
                    pending.append({
                        'filename': file_path.name,
                        'type': frontmatter.get('type', 'unknown'),
                        'timestamp': frontmatter.get('timestamp') or frontmatter.get('received'),
                        'urgency': self._determine_urgency(frontmatter, content),
                        'summary': self._extract_summary(frontmatter, content)
                    })
            except Exception as e:
                self.logger.error(f"Error reading {file_path.name}: {e}")

        return sorted(pending, key=lambda x: x['urgency'], reverse=True)

    def _get_recent_activity(self) -> Dict[str, int]:
        """Get recent activity from logs."""
        logs_dir = self.vault_path / 'Logs'
        activity = {
            'files_processed': 0,
            'emails_detected': 0,
            'whatsapp_detected': 0,
            'linkedin_detected': 0,
            'approvals_processed': 0
        }

        if not logs_dir.exists():
            return activity

        # Read today's log
        today_log = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

        if today_log.exists():
            try:
                log_content = today_log.read_text(encoding='utf-8')

                activity['files_processed'] = log_content.count('File detected:')
                activity['emails_detected'] = log_content.count('Gmail message detected:')
                activity['whatsapp_detected'] = log_content.count('WhatsApp urgent message detected')
                activity['linkedin_detected'] = log_content.count('Business update detected:')
                activity['approvals_processed'] = log_content.count('Processing approved action:')

            except Exception as e:
                self.logger.error(f"Error reading log: {e}")

        return activity

    def _identify_priorities(self, pending_actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify high priority items."""
        priorities = []

        for action in pending_actions:
            if action['urgency'] == 'high':
                priorities.append(action)

        return priorities[:5]  # Top 5 priorities

    def _check_system_health(self) -> Dict[str, str]:
        """Check system health status."""
        # Simple health check based on recent log activity
        logs_dir = self.vault_path / 'Logs'
        today_log = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

        health = {
            'file_watcher': '❓ Unknown',
            'gmail_watcher': '❓ Unknown',
            'whatsapp_watcher': '❓ Unknown',
            'approval_orchestrator': '❓ Unknown'
        }

        if today_log.exists():
            try:
                log_content = today_log.read_text(encoding='utf-8')

                # Check for recent activity (last 5 minutes)
                if 'FileWatcher' in log_content:
                    health['file_watcher'] = '✅ Active'
                if 'GmailWatcher' in log_content:
                    health['gmail_watcher'] = '✅ Active'
                if 'WhatsAppWatcher' in log_content:
                    health['whatsapp_watcher'] = '✅ Active'
                if 'ApprovalOrchestrator' in log_content:
                    health['approval_orchestrator'] = '✅ Active'

            except Exception as e:
                self.logger.error(f"Error checking health: {e}")

        return health

    def _determine_urgency(self, frontmatter: Dict[str, Any], content: str) -> str:
        """Determine urgency level of action item."""
        # Check frontmatter urgency
        if frontmatter.get('urgency') == 'high':
            return 'high'
        if frontmatter.get('importance') == 'high':
            return 'high'

        # Check for urgent keywords in content
        urgent_keywords = ['urgent', 'asap', 'immediately', 'critical', 'overdue']
        content_lower = content.lower()

        if any(keyword in content_lower for keyword in urgent_keywords):
            return 'high'

        # Check age (overdue if > 24 hours)
        timestamp_str = frontmatter.get('timestamp') or frontmatter.get('received')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                age = datetime.now() - timestamp.replace(tzinfo=None)
                if age > timedelta(hours=24):
                    return 'high'
            except Exception:
                pass

        return 'medium'

    def _extract_summary(self, frontmatter: Dict[str, Any], content: str) -> str:
        """Extract summary from action item."""
        # Try to get subject or message
        if frontmatter.get('subject'):
            return frontmatter['subject']
        if frontmatter.get('original_name'):
            return f"File: {frontmatter['original_name']}"

        # Extract first line of content after frontmatter
        lines = content.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('#') and not line.startswith('-'):
                return line.strip()[:100]

        return "No summary available"

    def _create_briefing_content(self, pending_actions: List[Dict[str, Any]],
                                  recent_activity: Dict[str, int],
                                  priorities: List[Dict[str, Any]],
                                  system_health: Dict[str, str]) -> str:
        """Create briefing markdown content."""
        today = datetime.now().strftime('%Y-%m-%d')
        time = datetime.now().strftime('%H:%M:%S')

        # Count by urgency
        high_priority_count = len([a for a in pending_actions if a['urgency'] == 'high'])
        medium_priority_count = len([a for a in pending_actions if a['urgency'] == 'medium'])

        content = f"""# Daily Briefing - {today}

**Generated**: {today} {time}

## Executive Summary

Good morning! You have **{len(pending_actions)} pending actions** with **{high_priority_count} high priority** items.

"""

        # Pending Actions
        if pending_actions:
            content += f"""## Pending Actions ({len(pending_actions)})

### High Priority ({high_priority_count})

"""
            high_priority_items = [a for a in pending_actions if a['urgency'] == 'high']
            for i, action in enumerate(high_priority_items[:5], 1):
                content += f"""{i}. **{action['type'].upper()}**: {action['summary']}
   - File: {action['filename']}
   - Status: {action['urgency'].upper()} priority

"""

            if medium_priority_count > 0:
                content += f"""### Medium Priority ({medium_priority_count})

"""
                medium_priority_items = [a for a in pending_actions if a['urgency'] == 'medium']
                for i, action in enumerate(medium_priority_items[:3], 1):
                    content += f"""{i}. **{action['type'].upper()}**: {action['summary']}

"""

        # Recent Activity
        content += f"""## Recent Activity (Last 24 Hours)

"""
        if any(recent_activity.values()):
            if recent_activity['files_processed'] > 0:
                content += f"- ✅ Processed {recent_activity['files_processed']} files\n"
            if recent_activity['emails_detected'] > 0:
                content += f"- 📧 Detected {recent_activity['emails_detected']} emails\n"
            if recent_activity['whatsapp_detected'] > 0:
                content += f"- 💬 Detected {recent_activity['whatsapp_detected']} WhatsApp messages\n"
            if recent_activity['linkedin_detected'] > 0:
                content += f"- 📱 Detected {recent_activity['linkedin_detected']} LinkedIn updates\n"
            if recent_activity['approvals_processed'] > 0:
                content += f"- ✓ Processed {recent_activity['approvals_processed']} approvals\n"
        else:
            content += "- No recent activity\n"

        # Focus Areas
        content += f"""
## Focus Areas for Today

"""
        if priorities:
            for i, priority in enumerate(priorities[:3], 1):
                content += f"{i}. **{priority['summary']}** ({priority['type']})\n"
        else:
            content += "- No urgent items - good job staying on top of things!\n"

        # System Health
        content += f"""
## System Health

"""
        for component, status in system_health.items():
            component_name = component.replace('_', ' ').title()
            content += f"- {component_name}: {status}\n"

        # Footer
        content += f"""
---
*Generated by Personal AI Employee (Silver Tier)*
"""

        return content

    def _save_briefing(self, content: str) -> Path:
        """Save briefing to file."""
        briefings_dir = self.vault_path / 'Briefings'
        briefings_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{datetime.now().strftime('%Y-%m-%d')}_briefing.md"
        briefing_path = briefings_dir / filename

        briefing_path.write_text(content, encoding='utf-8')

        return briefing_path

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter from markdown content."""
        try:
            if not content.startswith('---'):
                return {}

            end_index = content.find('---', 3)
            if end_index == -1:
                return {}

            yaml_content = content[3:end_index].strip()

            # Simple YAML parsing (key: value)
            frontmatter = {}
            for line in yaml_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()

            return frontmatter

        except Exception as e:
            self.logger.error(f"Error parsing frontmatter: {e}")
            return {}


def generate_daily_briefing(vault_path: str, logger) -> Path:
    """
    Generate daily briefing (convenience function).

    Args:
        vault_path: Path to Obsidian vault
        logger: Logger instance

    Returns:
        Path to generated briefing file
    """
    generator = BriefingGenerator(vault_path, logger)
    return generator.generate_briefing()
