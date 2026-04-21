"""
Social media orchestrator for Gold tier autonomous AI employee.

Monitors business updates, adapts content for each platform, handles approval workflow,
publishes posts, and collects engagement metrics.
"""

import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import yaml


class SocialMediaOrchestrator:
    """Orchestrates social media posting and engagement tracking."""

    def __init__(
        self,
        vault_path: str,
        logger: logging.Logger,
        vault_manager,
        facebook_client=None,
        instagram_client=None,
        twitter_client=None,
        check_interval: int = 60
    ):
        """
        Initialize social media orchestrator.

        Args:
            vault_path: Path to Obsidian vault
            logger: Logger instance
            vault_manager: VaultManager instance
            facebook_client: FacebookClient instance
            instagram_client: InstagramClient instance
            twitter_client: TwitterClient instance
            check_interval: Check interval in seconds
        """
        self.vault_path = Path(vault_path)
        self.logger = logger
        self.vault_manager = vault_manager
        self.facebook_client = facebook_client
        self.instagram_client = instagram_client
        self.twitter_client = twitter_client
        self.check_interval = check_interval

        # Folder paths
        self.drafts_path = self.vault_path / "Social_Media" / "Drafts"
        self.published_path = self.vault_path / "Social_Media" / "Published"
        self.analytics_path = self.vault_path / "Social_Media" / "Analytics"
        self.pending_approval_path = self.vault_path / "Pending_Approval"
        self.approved_path = self.vault_path / "Approved"

        # Ensure directories exist
        for path in [self.drafts_path, self.published_path, self.analytics_path]:
            path.mkdir(parents=True, exist_ok=True)

        # Tracking
        self.processed_files: Set[str] = set()
        self.scheduled_metrics: Dict[str, datetime] = {}
        self.running = False

        # Content adapter
        from utils.content_adapter import create_content_adapter
        self.content_adapter = create_content_adapter()

        self.logger.info(
            f"SocialMediaOrchestrator initialized: check_interval={check_interval}s"
        )

    def start(self):
        """Start the social media orchestrator."""
        self.running = True
        self.logger.info("Starting Social Media Orchestrator")
        self.run()

    def stop(self):
        """Stop the social media orchestrator."""
        self.running = False
        self.logger.info("Stopping Social Media Orchestrator")

    def run(self):
        """Main orchestrator loop."""
        while self.running:
            try:
                # Check for new business updates
                self.process_business_updates()

                # Check for approved posts
                self.process_approved_posts()

                # Collect scheduled metrics
                self.collect_scheduled_metrics()

            except Exception as e:
                self.logger.error(f"Error in social media orchestrator loop: {e}", exc_info=True)

            time.sleep(self.check_interval)

    def process_business_updates(self):
        """Process new business update files in Drafts/."""
        if not self.drafts_path.exists():
            return

        for update_file in self.drafts_path.glob("*.md"):
            file_key = str(update_file.absolute())

            # Skip if already processed
            if file_key in self.processed_files:
                continue

            try:
                self.logger.info(f"Processing business update: {update_file.name}")

                # Read update file
                content = update_file.read_text(encoding='utf-8')
                frontmatter = self._parse_frontmatter(content)

                if not frontmatter:
                    self.logger.error(f"No frontmatter in {update_file.name}")
                    continue

                # Extract details
                title = frontmatter.get('title', '')
                platforms = frontmatter.get('platforms', ['facebook', 'instagram', 'twitter'])
                approval_required = frontmatter.get('approval_required', True)
                hashtags = frontmatter.get('hashtags', [])
                link = frontmatter.get('link')

                # Extract content (after frontmatter)
                update_content = self._extract_content(content)

                # Adapt content for all platforms
                adapted = self.content_adapter.adapt_business_update(
                    content=update_content,
                    title=title,
                    link=link,
                    hashtags=hashtags
                )

                if approval_required:
                    # Create approval request
                    self._create_approval_request(
                        update_file,
                        title,
                        platforms,
                        adapted
                    )
                else:
                    # Publish immediately
                    self._publish_to_platforms(
                        update_file,
                        title,
                        platforms,
                        adapted
                    )

                # Mark as processed
                self.processed_files.add(file_key)

            except Exception as e:
                self.logger.error(f"Error processing business update {update_file.name}: {e}", exc_info=True)

    def process_approved_posts(self):
        """Process approved social media posts."""
        if not self.approved_path.exists():
            return

        for approval_file in self.approved_path.glob("SOCIAL_MEDIA_APPROVAL_*.md"):
            file_key = str(approval_file.absolute())

            # Skip if already processed
            if file_key in self.processed_files:
                continue

            try:
                self.logger.info(f"Processing approved post: {approval_file.name}")

                # Read approval file
                content = approval_file.read_text(encoding='utf-8')
                frontmatter = self._parse_frontmatter(content)

                if not frontmatter:
                    self.logger.error(f"No frontmatter in {approval_file.name}")
                    continue

                # Extract original file and platforms
                original_file = frontmatter.get('original_file')
                platforms = frontmatter.get('platforms', ['facebook', 'instagram', 'twitter'])
                adapted_content = frontmatter.get('adapted_content', {})

                # Publish to platforms
                if original_file:
                    original_path = self.drafts_path / original_file
                    if original_path.exists():
                        self._publish_to_platforms(
                            original_path,
                            frontmatter.get('title', ''),
                            platforms,
                            adapted_content
                        )

                # Mark as processed
                self.processed_files.add(file_key)

                # Move approval file to Done
                done_path = self.vault_path / "Done" / approval_file.name
                approval_file.rename(done_path)

            except Exception as e:
                self.logger.error(f"Error processing approved post {approval_file.name}: {e}", exc_info=True)

    def _create_approval_request(
        self,
        update_file: Path,
        title: str,
        platforms: List[str],
        adapted: Dict[str, Dict]
    ):
        """Create approval request for social media post."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            approval_file = self.pending_approval_path / f"SOCIAL_MEDIA_APPROVAL_{timestamp}.md"

            # Build approval content
            approval_content = f"""---
type: social_media_approval
original_file: {update_file.name}
title: {title}
platforms: {platforms}
created: {datetime.now().isoformat()}
status: pending
adapted_content: {json.dumps(adapted)}
---

## Social Media Approval Required

**Original Update**: {title}

"""

            # Add platform-specific previews
            if 'facebook' in platforms and 'facebook' in adapted:
                approval_content += f"""### Facebook Post

{adapted['facebook']['message']}

---

"""

            if 'instagram' in platforms and 'instagram' in adapted:
                approval_content += f"""### Instagram Post

{adapted['instagram']['caption']}

---

"""

            if 'twitter' in platforms and 'twitter' in adapted:
                approval_content += "### Twitter\n\n"
                if adapted['twitter'].get('is_thread'):
                    for i, tweet in enumerate(adapted['twitter']['tweets'], 1):
                        approval_content += f"{i}/ {tweet}\n\n"
                else:
                    approval_content += f"{adapted['twitter']['text']}\n\n"
                approval_content += "---\n\n"

            approval_content += """**Action Required**:
1. Review posts for all platforms
2. If approved, move this file to Approved/ folder
3. If rejected, move to Done/ with rejection reason

**Next Steps**:
- Approved: Posts will be published to all platforms
- Rejected: Draft will be archived
"""

            approval_file.write_text(approval_content, encoding='utf-8')
            self.logger.info(f"Created approval request: {approval_file.name}")

        except Exception as e:
            self.logger.error(f"Error creating approval request: {e}")

    def _publish_to_platforms(
        self,
        update_file: Path,
        title: str,
        platforms: List[str],
        adapted: Dict[str, Dict]
    ):
        """Publish content to social media platforms."""
        post_ids = {}

        try:
            # Publish to Facebook
            if 'facebook' in platforms and self.facebook_client and 'facebook' in adapted:
                try:
                    fb_post = self.facebook_client.create_post(
                        message=adapted['facebook']['message'],
                        link=adapted['facebook'].get('link')
                    )
                    post_ids['facebook'] = fb_post['post_id']
                    self.logger.info(f"Published to Facebook: {fb_post['post_id']}")
                except Exception as e:
                    self.logger.error(f"Failed to publish to Facebook: {e}")

            # Publish to Instagram
            if 'instagram' in platforms and self.instagram_client and 'instagram' in adapted:
                try:
                    # Instagram requires image - skip if not provided
                    self.logger.warning("Instagram post skipped (requires image)")
                except Exception as e:
                    self.logger.error(f"Failed to publish to Instagram: {e}")

            # Publish to Twitter
            if 'twitter' in platforms and self.twitter_client and 'twitter' in adapted:
                try:
                    if adapted['twitter'].get('is_thread'):
                        tw_thread = self.twitter_client.create_thread(
                            tweets=adapted['twitter']['tweets']
                        )
                        post_ids['twitter'] = tw_thread['thread_id']
                        self.logger.info(f"Published Twitter thread: {tw_thread['thread_id']}")
                    else:
                        tw_post = self.twitter_client.create_tweet(
                            text=adapted['twitter']['text']
                        )
                        post_ids['twitter'] = tw_post['tweet_id']
                        self.logger.info(f"Published tweet: {tw_post['tweet_id']}")
                except Exception as e:
                    self.logger.error(f"Failed to publish to Twitter: {e}")

            # Update business update file with post IDs
            self._update_business_update(update_file, post_ids)

            # Schedule metrics collection (24 hours)
            metrics_time = datetime.now() + timedelta(hours=24)
            self.scheduled_metrics[update_file.name] = {
                'time': metrics_time,
                'post_ids': post_ids,
                'title': title
            }

            # Move to Published folder
            published_file = self.published_path / update_file.name
            update_file.rename(published_file)
            self.logger.info(f"Moved to Published: {update_file.name}")

        except Exception as e:
            self.logger.error(f"Error publishing to platforms: {e}")

    def _update_business_update(self, update_file: Path, post_ids: Dict[str, str]):
        """Update business update file with post IDs."""
        try:
            content = update_file.read_text(encoding='utf-8')

            # Add post IDs to frontmatter
            lines = content.split('\n')
            frontmatter_end = -1
            for i, line in enumerate(lines):
                if i > 0 and line.strip() == '---':
                    frontmatter_end = i
                    break

            if frontmatter_end > 0:
                # Insert post IDs before closing ---
                lines.insert(frontmatter_end, f"published_at: {datetime.now().isoformat()}")
                lines.insert(frontmatter_end, "status: published")
                for platform, post_id in post_ids.items():
                    lines.insert(frontmatter_end, f"{platform}_post_id: {post_id}")

                update_file.write_text('\n'.join(lines), encoding='utf-8')

        except Exception as e:
            self.logger.error(f"Error updating business update: {e}")

    def collect_scheduled_metrics(self):
        """Collect engagement metrics for scheduled posts."""
        now = datetime.now()

        for file_name, schedule in list(self.scheduled_metrics.items()):
            if now >= schedule['time']:
                try:
                    self.logger.info(f"Collecting metrics for: {file_name}")
                    self._collect_and_report_metrics(
                        file_name,
                        schedule['post_ids'],
                        schedule['title']
                    )
                    # Remove from schedule
                    del self.scheduled_metrics[file_name]
                except Exception as e:
                    self.logger.error(f"Error collecting metrics for {file_name}: {e}")

    def _collect_and_report_metrics(
        self,
        file_name: str,
        post_ids: Dict[str, str],
        title: str
    ):
        """Collect metrics from all platforms and create analytics report."""
        metrics = {}

        # Collect Facebook metrics
        if 'facebook' in post_ids and self.facebook_client:
            try:
                fb_insights = self.facebook_client.get_post_insights(post_ids['facebook'])
                metrics['facebook'] = fb_insights
            except Exception as e:
                self.logger.error(f"Failed to collect Facebook metrics: {e}")

        # Collect Instagram metrics
        if 'instagram' in post_ids and self.instagram_client:
            try:
                ig_insights = self.instagram_client.get_media_insights(post_ids['instagram'])
                metrics['instagram'] = ig_insights
            except Exception as e:
                self.logger.error(f"Failed to collect Instagram metrics: {e}")

        # Collect Twitter metrics
        if 'twitter' in post_ids and self.twitter_client:
            try:
                tw_metrics = self.twitter_client.get_tweet_metrics(post_ids['twitter'])
                metrics['twitter'] = tw_metrics
            except Exception as e:
                self.logger.error(f"Failed to collect Twitter metrics: {e}")

        # Create analytics report
        self._create_analytics_report(file_name, title, metrics)

    def _create_analytics_report(
        self,
        file_name: str,
        title: str,
        metrics: Dict[str, Dict]
    ):
        """Create analytics report with engagement metrics."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.analytics_path / f"ANALYTICS_{timestamp}_{file_name}"

            report_content = f"""---
type: social_media_analytics
business_update: {title}
collected_at: {datetime.now().isoformat()}
---

## Social Media Analytics: {title}

**Metrics Collected**: {datetime.now().strftime("%Y-%m-%d at %H:%M")}

"""

            # Add platform-specific metrics
            for platform, data in metrics.items():
                report_content += f"### {platform.title()} Performance\n\n"

                if 'insights' in data:
                    for metric, value in data['insights'].items():
                        report_content += f"- **{metric}**: {value}\n"

                if 'engagement' in data:
                    report_content += "\n**Engagement**:\n"
                    for metric, value in data['engagement'].items():
                        report_content += f"- {metric.title()}: {value}\n"

                report_content += "\n"

            report_file.write_text(report_content, encoding='utf-8')
            self.logger.info(f"Created analytics report: {report_file.name}")

        except Exception as e:
            self.logger.error(f"Error creating analytics report: {e}")

    def _parse_frontmatter(self, content: str) -> Optional[Dict]:
        """Parse YAML frontmatter from markdown content."""
        try:
            if not content.startswith('---'):
                return None

            end_index = content.find('---', 3)
            if end_index == -1:
                return None

            yaml_content = content[3:end_index].strip()
            return yaml.safe_load(yaml_content)

        except Exception as e:
            self.logger.error(f"Error parsing frontmatter: {e}")
            return None

    def _extract_content(self, markdown: str) -> str:
        """Extract content after frontmatter."""
        try:
            if not markdown.startswith('---'):
                return markdown

            end_index = markdown.find('---', 3)
            if end_index == -1:
                return markdown

            return markdown[end_index + 3:].strip()

        except Exception as e:
            self.logger.error(f"Error extracting content: {e}")
            return markdown
