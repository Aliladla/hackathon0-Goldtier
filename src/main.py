"""
Main orchestrator for Personal AI Employee (Bronze + Silver + Gold Tier).

Entry point that initializes the vault, starts all watchers and orchestrators,
and handles graceful shutdown.
"""

import os
import sys
import signal
import threading
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from utils.logger import create_logger
from utils.vault_manager import create_vault_manager
from watchers.file_watcher import FileWatcher

# Silver tier imports (optional - only if enabled)
try:
    from watchers.gmail_watcher import GmailWatcher
    from watchers.whatsapp_watcher import WhatsAppWatcher
    from watchers.linkedin_watcher import LinkedInWatcher
    from orchestrators.approval_orchestrator import ApprovalOrchestrator
    from orchestrators.scheduler import create_scheduler
    SILVER_TIER_AVAILABLE = True
except ImportError as e:
    SILVER_TIER_AVAILABLE = False
    print(f"Silver tier components not available: {e}")

# Gold tier imports (optional - only if enabled)
try:
    from utils.error_recovery import initialize_error_recovery
    from utils.watchdog import initialize_watchdog
    from orchestrators.ralph_wiggum import RalphWiggumLoop
    GOLD_TIER_AVAILABLE = True
except ImportError as e:
    GOLD_TIER_AVAILABLE = False
    print(f"Gold tier components not available: {e}")


class AIEmployeeOrchestrator:
    """Main orchestrator for AI Employee system."""

    def __init__(self):
        """Initialize orchestrator."""
        # Load environment variables
        load_dotenv()

        # Get configuration
        self.vault_path = os.getenv('VAULT_PATH')
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '30'))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'

        # Silver tier configuration
        self.enable_gmail = os.getenv('ENABLE_GMAIL', 'false').lower() == 'true'
        self.enable_whatsapp = os.getenv('ENABLE_WHATSAPP', 'false').lower() == 'true'
        self.enable_linkedin = os.getenv('ENABLE_LINKEDIN', 'false').lower() == 'true'
        self.enable_scheduler = os.getenv('ENABLE_SCHEDULER', 'false').lower() == 'true'

        # Gold tier configuration
        self.enable_ralph_wiggum = os.getenv('ENABLE_RALPH_WIGGUM', 'false').lower() == 'true'
        self.enable_odoo = os.getenv('ENABLE_ODOO', 'false').lower() == 'true'
        self.enable_social_media = os.getenv('ENABLE_SOCIAL_MEDIA', 'false').lower() == 'true'
        self.enable_weekly_audit = os.getenv('ENABLE_WEEKLY_AUDIT', 'false').lower() == 'true'
        self.max_retry_attempts = int(os.getenv('MAX_RETRY_ATTEMPTS', '5'))
        self.retry_base_delay = int(os.getenv('RETRY_BASE_DELAY', '1'))

        # Validate configuration
        if not self.vault_path:
            print("ERROR: VAULT_PATH not set in .env file")
            print("Please copy .env.example to .env and configure VAULT_PATH")
            sys.exit(1)

        # Initialize components
        self.logger = create_logger(self.vault_path, "Orchestrator", self.log_level)
        self.vault_manager = create_vault_manager(self.vault_path)

        # Bronze tier
        self.file_watcher = None

        # Silver tier
        self.gmail_watcher = None
        self.whatsapp_watcher = None
        self.linkedin_watcher = None
        self.approval_orchestrator = None
        self.scheduler = None

        # Gold tier
        self.error_recovery = None
        self.watchdog = None
        self.ralph_wiggum = None
        self.odoo_client = None
        self.facebook_client = None
        self.instagram_client = None
        self.twitter_client = None

        # Threads for concurrent watchers
        self.threads = []

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info("Shutdown signal received")
        self.shutdown()
        sys.exit(0)

    def initialize_vault(self):
        """Initialize vault structure and templates."""
        self.logger.info(f"Initializing vault at: {self.vault_path}")

        # Validate vault path
        if not self.vault_manager.validate_vault():
            self.logger.info("Creating vault directory structure")
            self.vault_manager.create_vault_structure()
        else:
            self.logger.info("Vault directory exists, ensuring folder structure")
            self.vault_manager.create_vault_structure()

        # Create templates if they don't exist
        self._create_dashboard_template()
        self._create_handbook_template()

        self.logger.info("Vault initialization complete")

    def _create_dashboard_template(self):
        """Create Dashboard.md if it doesn't exist."""
        dashboard_path = Path(self.vault_path) / "Dashboard.md"

        if dashboard_path.exists():
            self.logger.debug("Dashboard.md already exists")
            return

        content = """# Dashboard

**Last Updated**: Not yet updated
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

## System Information

- **Vault Path**: {vault_path}
- **Check Interval**: {check_interval} seconds
- **Dry Run Mode**: {dry_run}

---
*Generated by Personal AI Employee (Bronze Tier)*
""".format(
            vault_path=self.vault_path,
            check_interval=self.check_interval,
            dry_run="Enabled" if self.dry_run else "Disabled"
        )

        dashboard_path.write_text(content, encoding='utf-8')
        self.logger.info("Created Dashboard.md template")

    def _create_handbook_template(self):
        """Create Company_Handbook.md if it doesn't exist."""
        handbook_path = Path(self.vault_path) / "Company_Handbook.md"

        if handbook_path.exists():
            self.logger.debug("Company_Handbook.md already exists")
            return

        content = """# Company Handbook

This handbook defines the rules and behaviors for your Personal AI Employee.

## Purpose

The AI Employee reads this handbook to understand how to process files, prioritize tasks, and make decisions on your behalf. Update these rules to customize the AI's behavior.

## General Rules

### File Processing
- Review all files within 24 hours of detection
- Flag any files over 10 MB for manual review
- Categorize files by type (invoice, contract, report, etc.)

### Prioritization
- Client communications are highest priority
- Financial documents require careful review
- Administrative tasks can be processed in batch

### Decision Making
- When in doubt, ask for human approval
- Never make financial commitments without approval
- Always log reasoning for decisions

## Specific Rules

### Invoices
- Flag all invoices over $500 for review
- Check for duplicate invoice numbers
- Verify payment terms and due dates
- Log to accounting folder

### Contracts
- All contracts require human review before signing
- Check for expiration dates and renewal terms
- Flag any unusual clauses or terms

### Client Communications
- Respond to client emails within 24 hours
- Maintain professional and friendly tone
- Escalate urgent requests immediately

### Reports
- Summarize key findings and recommendations
- Highlight any anomalies or concerns
- Archive completed reports to Done folder

## Custom Rules

Add your own rules here:

- [Your custom rule 1]
- [Your custom rule 2]
- [Your custom rule 3]

## Notes

- Rules are applied in order from top to bottom
- More specific rules override general rules
- Update this handbook as your needs evolve

---
*Last Updated*: {date}
""".format(date="2026-04-16")

        handbook_path.write_text(content, encoding='utf-8')
        self.logger.info("Created Company_Handbook.md template")

    def start(self):
        """Start the AI Employee system."""
        # Determine active tier
        gold_active = GOLD_TIER_AVAILABLE and any([
            self.enable_ralph_wiggum, self.enable_odoo,
            self.enable_social_media, self.enable_weekly_audit
        ])
        silver_active = SILVER_TIER_AVAILABLE and any([
            self.enable_gmail, self.enable_whatsapp,
            self.enable_linkedin, self.enable_scheduler
        ])

        if gold_active:
            tier = "Bronze + Silver + Gold"
        elif silver_active:
            tier = "Bronze + Silver"
        else:
            tier = "Bronze"

        self.logger.info("=" * 60)
        self.logger.info(f"Personal AI Employee ({tier} Tier) Starting")
        self.logger.info("=" * 60)

        # Initialize vault
        self.initialize_vault()

        # Initialize Gold tier infrastructure (if available)
        if GOLD_TIER_AVAILABLE:
            self._initialize_gold_tier()

        # Update dashboard with startup event
        self.vault_manager.update_dashboard("system_startup", {})

        # Start Bronze tier components
        self._start_bronze_tier()

        # Start Silver tier components (if enabled)
        if SILVER_TIER_AVAILABLE:
            self._start_silver_tier()

        # Start Gold tier components (if enabled)
        if GOLD_TIER_AVAILABLE:
            self._start_gold_tier()

        self.logger.info("=" * 60)
        self.logger.info("System is now running. Press Ctrl+C to stop.")
        self.logger.info("=" * 60)
        self.logger.info(f"Dry run mode: {'Enabled' if self.dry_run else 'Disabled'}")
        self.logger.info("=" * 60)

        # Keep main thread alive
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    def _initialize_gold_tier(self):
        """Initialize Gold tier infrastructure."""
        self.logger.info("Initializing Gold Tier Infrastructure")

        # Initialize error recovery
        self.error_recovery = initialize_error_recovery(
            self.vault_path,
            max_retries=self.max_retry_attempts,
            base_delay=self.retry_base_delay
        )
        self.logger.info("✓ Error recovery initialized")

        # Initialize watchdog
        self.watchdog = initialize_watchdog(
            self.vault_path,
            check_interval=60
        )
        self.logger.info("✓ Watchdog initialized")

    def _start_bronze_tier(self):
        """Start Bronze tier components."""
        self.logger.info("Starting Bronze Tier Components")

        # File watcher
        self.file_watcher = FileWatcher(
            vault_path=self.vault_path,
            logger=create_logger(self.vault_path, "FileWatcher", self.log_level),
            vault_manager=self.vault_manager,
            check_interval=self.check_interval
        )

        thread = threading.Thread(target=self.file_watcher.start, daemon=True)
        thread.start()
        self.threads.append(thread)

        self.logger.info(f"✓ File Watcher started (monitoring: {Path(self.vault_path) / 'Inbox'})")

    def _start_silver_tier(self):
        """Start Silver tier components."""
        self.logger.info("Starting Silver Tier Components")

        # Approval orchestrator (always start if Silver tier available)
        self.approval_orchestrator = ApprovalOrchestrator(
            vault_path=self.vault_path,
            logger=create_logger(self.vault_path, "ApprovalOrchestrator", self.log_level),
            vault_manager=self.vault_manager,
            dry_run=self.dry_run
        )
        thread = threading.Thread(target=self.approval_orchestrator.start, daemon=True)
        thread.start()
        self.threads.append(thread)
        self.logger.info("✓ Approval Orchestrator started")

        # Gmail watcher
        if self.enable_gmail:
            try:
                credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'config/gmail_credentials.json')
                token_path = os.getenv('GMAIL_TOKEN_PATH', 'config/gmail_token.json')
                gmail_interval = int(os.getenv('GMAIL_CHECK_INTERVAL', '120'))

                self.gmail_watcher = GmailWatcher(
                    vault_path=self.vault_path,
                    logger=create_logger(self.vault_path, "GmailWatcher", self.log_level),
                    vault_manager=self.vault_manager,
                    credentials_path=credentials_path,
                    token_path=token_path,
                    check_interval=gmail_interval
                )

                thread = threading.Thread(target=self.gmail_watcher.start, daemon=True)
                thread.start()
                self.threads.append(thread)
                self.logger.info(f"✓ Gmail Watcher started (check interval: {gmail_interval}s)")
            except Exception as e:
                self.logger.error(f"Failed to start Gmail watcher: {e}")

        # WhatsApp watcher
        if self.enable_whatsapp:
            try:
                session_path = os.getenv('WHATSAPP_SESSION_PATH', 'config/whatsapp_session')
                keywords = os.getenv('WHATSAPP_KEYWORDS', 'urgent,asap,invoice,payment,help').split(',')
                whatsapp_interval = int(os.getenv('WHATSAPP_CHECK_INTERVAL', '30'))

                self.whatsapp_watcher = WhatsAppWatcher(
                    vault_path=self.vault_path,
                    logger=create_logger(self.vault_path, "WhatsAppWatcher", self.log_level),
                    vault_manager=self.vault_manager,
                    session_path=session_path,
                    keywords=keywords,
                    check_interval=whatsapp_interval
                )

                thread = threading.Thread(target=self.whatsapp_watcher.start, daemon=True)
                thread.start()
                self.threads.append(thread)
                self.logger.info(f"✓ WhatsApp Watcher started (check interval: {whatsapp_interval}s)")
            except Exception as e:
                self.logger.error(f"Failed to start WhatsApp watcher: {e}")

        # LinkedIn watcher
        if self.enable_linkedin:
            try:
                linkedin_interval = int(os.getenv('LINKEDIN_CHECK_INTERVAL', '60'))

                self.linkedin_watcher = LinkedInWatcher(
                    vault_path=self.vault_path,
                    logger=create_logger(self.vault_path, "LinkedInWatcher", self.log_level),
                    vault_manager=self.vault_manager,
                    check_interval=linkedin_interval
                )

                thread = threading.Thread(target=self.linkedin_watcher.start, daemon=True)
                thread.start()
                self.threads.append(thread)
                self.logger.info(f"✓ LinkedIn Watcher started (check interval: {linkedin_interval}s)")
            except Exception as e:
                self.logger.error(f"Failed to start LinkedIn watcher: {e}")

        # Scheduler
        if self.enable_scheduler:
            try:
                from utils.briefing_generator import generate_daily_briefing

                self.scheduler = create_scheduler(
                    create_logger(self.vault_path, "Scheduler", self.log_level)
                )

                # Register daily briefing task
                briefing_time = os.getenv('DAILY_BRIEFING_TIME', '08:00')

                def briefing_task():
                    """Generate daily briefing."""
                    try:
                        briefing_path = generate_daily_briefing(
                            self.vault_path,
                            create_logger(self.vault_path, "BriefingGenerator", self.log_level)
                        )
                        # Update dashboard with briefing link
                        self.vault_manager.update_dashboard(
                            "briefing_generated",
                            {"filename": briefing_path.name}
                        )
                    except Exception as e:
                        self.logger.error(f"Error generating briefing: {e}", exc_info=True)

                self.scheduler.register_daily_task('daily_briefing', briefing_time, briefing_task)

                thread = threading.Thread(target=self.scheduler.start, daemon=True)
                thread.start()
                self.threads.append(thread)
                self.logger.info(f"✓ Scheduler started (daily briefing at {briefing_time})")
            except Exception as e:
                self.logger.error(f"Failed to start scheduler: {e}")

    def _start_gold_tier(self):
        """Start Gold tier components."""
        self.logger.info("Starting Gold Tier Components")

        # Start watchdog monitoring in background thread
        if self.watchdog:
            thread = threading.Thread(target=self.watchdog.run, daemon=True)
            thread.start()
            self.threads.append(thread)
            self.logger.info("✓ Watchdog monitoring started")

        # Odoo client initialization
        if self.enable_odoo:
            try:
                from integrations.odoo_client import create_odoo_client

                self.odoo_client = create_odoo_client(vault_path=self.vault_path)
                if self.odoo_client:
                    self.odoo_client.connect()
                    self.logger.info("✓ Odoo client initialized and connected")
                else:
                    self.logger.warning("Odoo client not initialized (missing configuration)")
            except Exception as e:
                self.logger.error(f"Failed to initialize Odoo client: {e}")

        # Social media clients initialization
        if self.enable_social_media:
            try:
                from integrations.facebook_client import create_facebook_client
                from integrations.instagram_client import create_instagram_client
                from integrations.twitter_client import create_twitter_client

                # Facebook
                self.facebook_client = create_facebook_client(vault_path=self.vault_path)
                if self.facebook_client:
                    self.logger.info("✓ Facebook client initialized")
                else:
                    self.logger.warning("Facebook client not initialized (missing configuration)")

                # Instagram
                self.instagram_client = create_instagram_client(vault_path=self.vault_path)
                if self.instagram_client:
                    self.logger.info("✓ Instagram client initialized")
                else:
                    self.logger.warning("Instagram client not initialized (missing configuration)")

                # Twitter
                self.twitter_client = create_twitter_client(vault_path=self.vault_path)
                if self.twitter_client:
                    self.logger.info("✓ Twitter client initialized")
                else:
                    self.logger.warning("Twitter client not initialized (missing configuration)")

            except Exception as e:
                self.logger.error(f"Failed to initialize social media clients: {e}")

        # Weekly audit orchestrator
        if self.enable_weekly_audit:
            try:
                from orchestrators.audit_orchestrator import create_audit_orchestrator

                self.audit_orchestrator = create_audit_orchestrator(
                    vault_path=self.vault_path,
                    logger=create_logger(self.vault_path, "AuditOrchestrator", self.log_level),
                    vault_manager=self.vault_manager,
                    odoo_client=self.odoo_client if self.enable_odoo else None,
                    facebook_client=self.facebook_client if self.enable_social_media else None,
                    instagram_client=self.instagram_client if self.enable_social_media else None,
                    twitter_client=self.twitter_client if self.enable_social_media else None
                )

                # Schedule weekly audit (Sunday 11:00 PM)
                def weekly_audit_task():
                    try:
                        self.logger.info("Running scheduled weekly audit")
                        briefing_path = self.audit_orchestrator.generate_weekly_audit()
                        self.logger.info(f"Weekly audit complete: {briefing_path}")
                    except Exception as e:
                        self.logger.error(f"Error generating weekly audit: {e}", exc_info=True)

                # Register with scheduler if available
                if self.scheduler:
                    self.scheduler.register_weekly_task('weekly_audit', 'Sunday', '23:00', weekly_audit_task)
                    self.logger.info("✓ Weekly audit scheduled (Sunday 11:00 PM)")
                else:
                    self.logger.info("✓ Audit orchestrator initialized (scheduler not available)")

            except Exception as e:
                self.logger.error(f"Failed to initialize audit orchestrator: {e}")

        # Ralph Wiggum autonomous loop
        if self.enable_ralph_wiggum:
            try:
                ralph_max_iterations = int(os.getenv('RALPH_MAX_ITERATIONS', '10'))
                ralph_check_interval = int(os.getenv('RALPH_CHECK_INTERVAL', '60'))

                self.ralph_wiggum = RalphWiggumLoop(
                    vault_path=self.vault_path,
                    logger=create_logger(self.vault_path, "RalphWiggum", self.log_level),
                    vault_manager=self.vault_manager,
                    max_iterations=ralph_max_iterations,
                    check_interval=ralph_check_interval
                )

                thread = threading.Thread(target=self.ralph_wiggum.start, daemon=True)
                thread.start()
                self.threads.append(thread)
                self.logger.info(f"✓ Ralph Wiggum Loop started (max iterations: {ralph_max_iterations})")
            except Exception as e:
                self.logger.error(f"Failed to start Ralph Wiggum loop: {e}")

    def shutdown(self):
        """Shutdown the AI Employee system."""
        self.logger.info("Shutting down AI Employee system")

        # Stop all watchers and orchestrators
        if self.file_watcher:
            self.file_watcher.stop()
        if self.gmail_watcher:
            self.gmail_watcher.stop()
        if self.whatsapp_watcher:
            self.whatsapp_watcher.stop()
        if self.linkedin_watcher:
            self.linkedin_watcher.stop()
        if self.approval_orchestrator:
            self.approval_orchestrator.stop()
        if self.scheduler:
            self.scheduler.stop()
        if self.ralph_wiggum:
            self.ralph_wiggum.stop()

        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)

        # Update dashboard with shutdown event
        try:
            dashboard_path = Path(self.vault_path) / "Dashboard.md"
            if dashboard_path.exists():
                content = dashboard_path.read_text(encoding='utf-8')
                content = content.replace("**System Status**: Active", "**System Status**: Inactive")
                dashboard_path.write_text(content, encoding='utf-8')
        except Exception as e:
            self.logger.error(f"Error updating dashboard on shutdown: {e}")

        self.logger.info("Shutdown complete")


def main():
    """Main entry point."""
    try:
        orchestrator = AIEmployeeOrchestrator()
        orchestrator.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
