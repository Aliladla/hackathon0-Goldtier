"""
Approval orchestrator for Personal AI Employee (Silver Tier).

Watches approval folders and executes approved actions.
"""

import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import yaml


class ApprovalOrchestrator:
    """Orchestrates approval workflow for sensitive actions."""

    def __init__(self, vault_path: str, logger, vault_manager, dry_run: bool = True):
        """
        Initialize approval orchestrator.

        Args:
            vault_path: Path to Obsidian vault
            logger: Logger instance
            vault_manager: Vault manager instance
            dry_run: If True, log actions without executing
        """
        self.vault_path = Path(vault_path)
        self.logger = logger
        self.vault_manager = vault_manager
        self.dry_run = dry_run

        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.done = self.vault_path / 'Done'

        self.running = False
        self.processed_files = set()

        # Ensure folders exist
        for folder in [self.pending_approval, self.approved, self.rejected]:
            folder.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start the approval orchestrator."""
        self.running = True
        self.logger.info("Starting Approval Orchestrator")
        self.run()

    def stop(self):
        """Stop the approval orchestrator."""
        self.running = False
        self.logger.info("Stopping Approval Orchestrator")

    def run(self):
        """Main orchestrator loop."""
        while self.running:
            try:
                # Check for expired approvals
                self.check_expired_approvals()

                # Process approved actions
                self.process_approved_actions()

                # Process rejected actions
                self.process_rejected_actions()

            except Exception as e:
                self.logger.error(f"Error in approval orchestrator loop: {e}", exc_info=True)

            time.sleep(5)  # Check every 5 seconds

    def check_expired_approvals(self):
        """Check for and reject expired approval requests."""
        if not self.pending_approval.exists():
            return

        for approval_file in self.pending_approval.glob("APPROVAL_*.md"):
            try:
                # Read frontmatter
                content = approval_file.read_text(encoding='utf-8')
                frontmatter = self._parse_frontmatter(content)

                if not frontmatter:
                    continue

                # Check expiration
                created_at = frontmatter.get('created_at')
                expires_at = frontmatter.get('expires_at')

                if expires_at:
                    expires_dt = datetime.fromisoformat(expires_at)
                    if datetime.now() > expires_dt:
                        self.logger.warning(f"Approval request expired: {approval_file.name}")
                        self._reject_approval(approval_file, "Expired (>24 hours)")

            except Exception as e:
                self.logger.error(f"Error checking expiration for {approval_file.name}: {e}")

    def process_approved_actions(self):
        """Process actions that have been approved."""
        if not self.approved.exists():
            return

        for approval_file in self.approved.glob("APPROVAL_*.md"):
            file_key = str(approval_file.absolute())

            # Skip if already processed
            if file_key in self.processed_files:
                continue

            try:
                self.logger.info(f"Processing approved action: {approval_file.name}")

                # Read approval file
                content = approval_file.read_text(encoding='utf-8')
                frontmatter = self._parse_frontmatter(content)

                if not frontmatter:
                    self.logger.error(f"No frontmatter in {approval_file.name}")
                    continue

                # Check if this is a Ralph Wiggum approval request (Gold tier)
                # Ralph Wiggum handles its own approvals, so skip them here
                file_type = frontmatter.get('type')
                if file_type == 'approval_request':
                    self.logger.debug(f"Skipping Ralph Wiggum approval: {approval_file.name}")
                    self.processed_files.add(file_key)
                    continue

                action_type = frontmatter.get('action')

                # Route to appropriate handler
                if action_type == 'send_email':
                    self._execute_email_action(approval_file, frontmatter, content)
                elif action_type == 'post_linkedin':
                    self._execute_linkedin_action(approval_file, frontmatter, content)
                elif action_type == 'send_whatsapp':
                    self._execute_whatsapp_action(approval_file, frontmatter, content)
                else:
                    self.logger.warning(f"Unknown action type: {action_type}")

                # Mark as processed
                self.processed_files.add(file_key)

                # Move to Done
                done_path = self.done / approval_file.name
                approval_file.rename(done_path)
                self.logger.info(f"Moved approved action to Done: {approval_file.name}")

            except Exception as e:
                self.logger.error(f"Error processing approved action {approval_file.name}: {e}", exc_info=True)

    def process_rejected_actions(self):
        """Process actions that have been rejected."""
        if not self.rejected.exists():
            return

        for approval_file in self.rejected.glob("APPROVAL_*.md"):
            file_key = str(approval_file.absolute())

            # Skip if already processed
            if file_key in self.processed_files:
                continue

            try:
                self.logger.info(f"Processing rejected action: {approval_file.name}")

                # Log rejection
                content = approval_file.read_text(encoding='utf-8')
                frontmatter = self._parse_frontmatter(content)

                action_type = frontmatter.get('action', 'unknown')
                self.logger.info(f"Action rejected: {action_type}")

                # Update vault manager
                self.vault_manager.update_dashboard(
                    "action_rejected",
                    {"action": action_type, "filename": approval_file.name}
                )

                # Mark as processed
                self.processed_files.add(file_key)

                # Move to Done
                done_path = self.done / approval_file.name
                approval_file.rename(done_path)

            except Exception as e:
                self.logger.error(f"Error processing rejected action {approval_file.name}: {e}", exc_info=True)

    def _execute_email_action(self, approval_file: Path, frontmatter: Dict[str, Any], content: str):
        """Execute email send action."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would send email: {frontmatter.get('to')}")
            return

        # Extract email parameters from frontmatter and content
        to = frontmatter.get('to')
        subject = frontmatter.get('subject')
        reply_to_message_id = frontmatter.get('reply_to_message_id')

        # Extract email body from content (after frontmatter)
        body = self._extract_email_body(content)

        self.logger.info(f"Sending email to {to}: {subject}")

        try:
            # Call MCP server to send email
            # For Silver tier, we'll use a simple approach:
            # 1. Check if MCP server is available
            # 2. If not, log and create manual instruction
            # 3. If yes, call via subprocess (future implementation)

            # For now, create a manual instruction file
            self._create_manual_email_instruction(to, subject, body, reply_to_message_id)

            self.logger.info("Email send action prepared (manual send required)")

            # Update dashboard
            self.vault_manager.update_dashboard(
                "email_prepared",
                {"to": to, "subject": subject}
            )

        except Exception as e:
            self.logger.error(f"Error executing email action: {e}", exc_info=True)
            raise

    def _extract_email_body(self, content: str) -> str:
        """Extract email body from approval file content."""
        # Find the email body section
        lines = content.split('\n')
        body_lines = []
        in_body = False

        for line in lines:
            if '## Draft Email Body' in line or '## Email Body' in line:
                in_body = True
                continue
            elif in_body and line.startswith('##'):
                break
            elif in_body:
                body_lines.append(line)

        return '\n'.join(body_lines).strip()

    def _create_manual_email_instruction(self, to: str, subject: str, body: str, reply_to: str = None):
        """Create manual email instruction file."""
        instruction_path = self.vault_path / 'Needs_Action' / f'MANUAL_EMAIL_{datetime.now().strftime("%Y%m%d%H%M%S")}.md'

        content = f"""---
type: manual_instruction
action: send_email
to: {to}
subject: {subject}
created: {datetime.now().isoformat()}
---

## Manual Email Send Required

The approval orchestrator has prepared this email for sending. Since the MCP server is not fully integrated in Silver tier, please send this email manually.

### Email Details

**To**: {to}
**Subject**: {subject}
{f'**Reply To Message ID**: {reply_to}' if reply_to else ''}

### Email Body

{body}

### Instructions

1. Copy the email body above
2. Open your email client (Gmail, Outlook, etc.)
3. Compose new email with the details above
4. Send the email
5. Mark this task as complete by moving to Done/

### Note

Gold tier will include full MCP server integration for automated email sending.
"""

        instruction_path.write_text(content, encoding='utf-8')
        self.logger.info(f"Created manual email instruction: {instruction_path.name}")

    def _execute_linkedin_action(self, approval_file: Path, frontmatter: Dict[str, Any], content: str):
        """Execute LinkedIn post action."""
        if self.dry_run:
            self.logger.info("[DRY RUN] Would post to LinkedIn")
            return

        self.logger.info("LinkedIn post action executed (implementation pending)")

        # Update dashboard
        self.vault_manager.update_dashboard(
            "linkedin_posted",
            {"filename": approval_file.name}
        )

    def _execute_whatsapp_action(self, approval_file: Path, frontmatter: Dict[str, Any], content: str):
        """Execute WhatsApp send action."""
        if self.dry_run:
            self.logger.info("[DRY RUN] Would send WhatsApp message")
            return

        self.logger.info("WhatsApp send action executed (implementation pending)")

        # Update dashboard
        self.vault_manager.update_dashboard(
            "whatsapp_sent",
            {"filename": approval_file.name}
        )

    def _reject_approval(self, approval_file: Path, reason: str):
        """Reject an approval request."""
        try:
            # Add rejection reason to file
            content = approval_file.read_text(encoding='utf-8')
            content += f"\n\n## Rejection\n\n**Reason**: {reason}\n**Rejected at**: {datetime.now().isoformat()}\n"

            # Move to Rejected
            rejected_path = self.rejected / approval_file.name
            rejected_path.write_text(content, encoding='utf-8')
            approval_file.unlink()

            self.logger.info(f"Rejected approval: {approval_file.name} - {reason}")

        except Exception as e:
            self.logger.error(f"Error rejecting approval {approval_file.name}: {e}")

    def _parse_frontmatter(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse YAML frontmatter from markdown content.

        Args:
            content: Markdown content with frontmatter

        Returns:
            Dictionary of frontmatter fields, or None if parsing fails
        """
        try:
            if not content.startswith('---'):
                return None

            # Find end of frontmatter
            end_index = content.find('---', 3)
            if end_index == -1:
                return None

            # Extract and parse YAML
            yaml_content = content[3:end_index].strip()
            return yaml.safe_load(yaml_content)

        except Exception as e:
            self.logger.error(f"Error parsing frontmatter: {e}")
            return None
