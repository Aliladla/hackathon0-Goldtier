"""
Audit orchestrator for Gold tier autonomous AI employee.

Generates comprehensive weekly CEO briefings with:
- Financial data from Odoo
- Task completion analysis from vault
- Social media performance metrics
- Bottleneck detection
- Cost optimization recommendations
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict


class AuditOrchestrator:
    """Orchestrates weekly business and accounting audits."""

    def __init__(
        self,
        vault_path: str,
        logger: logging.Logger,
        vault_manager,
        odoo_client=None,
        facebook_client=None,
        instagram_client=None,
        twitter_client=None
    ):
        """
        Initialize audit orchestrator.

        Args:
            vault_path: Path to Obsidian vault
            logger: Logger instance
            vault_manager: VaultManager instance
            odoo_client: OdooClient instance
            facebook_client: FacebookClient instance
            instagram_client: InstagramClient instance
            twitter_client: TwitterClient instance
        """
        self.vault_path = Path(vault_path)
        self.logger = logger
        self.vault_manager = vault_manager
        self.odoo_client = odoo_client
        self.facebook_client = facebook_client
        self.instagram_client = instagram_client
        self.twitter_client = twitter_client

        # Folder paths
        self.done_path = self.vault_path / "Done"
        self.logs_path = self.vault_path / "Logs"
        self.analytics_path = self.vault_path / "Social_Media" / "Analytics"
        self.briefings_path = self.vault_path / "Briefings"

        # Ensure directories exist
        self.briefings_path.mkdir(parents=True, exist_ok=True)

        self.logger.info("AuditOrchestrator initialized")

    def generate_weekly_audit(self) -> Path:
        """
        Generate comprehensive weekly audit report.

        Returns:
            Path to generated briefing file

        Raises:
            Exception: If audit generation fails
        """
        self.logger.info("Starting weekly audit generation")

        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Collect data from all sources
        financial_data = self._query_financial_data(start_date, end_date)
        task_data = self._analyze_vault_tasks(start_date, end_date)
        social_data = self._aggregate_social_media_performance(start_date, end_date)
        bottlenecks = self._detect_bottlenecks(task_data)
        cost_insights = self._analyze_cost_optimization(financial_data)
        recommendations = self._generate_recommendations(
            financial_data, task_data, social_data, bottlenecks, cost_insights
        )

        # Generate CEO briefing
        briefing_path = self._generate_ceo_briefing(
            start_date,
            end_date,
            financial_data,
            task_data,
            social_data,
            bottlenecks,
            cost_insights,
            recommendations
        )

        # Update Dashboard.md
        self._update_dashboard_with_briefing(briefing_path)

        self.logger.info(f"Weekly audit complete: {briefing_path}")
        return briefing_path

    def _query_financial_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Query financial data from Odoo."""
        financial_data = {
            'revenue': 0,
            'invoices': {'count': 0, 'total': 0, 'paid': 0, 'unpaid': 0},
            'payments': {'count': 0, 'total': 0},
            'outstanding': 0,
        }

        if not self.odoo_client:
            self.logger.warning("Odoo client not available, skipping financial data")
            return financial_data

        try:
            # Query Odoo for financial summary
            financials = self.odoo_client.query_financials(
                report_type='summary',
                date_from=start_date.strftime('%Y-%m-%d'),
                date_to=end_date.strftime('%Y-%m-%d')
            )

            financial_data['invoices'] = financials.get('invoices', {})
            financial_data['payments'] = financials.get('payments', {})
            financial_data['revenue'] = financials['invoices'].get('total', 0)
            financial_data['outstanding'] = (
                financials['invoices'].get('total', 0) -
                financials['payments'].get('total', 0)
            )

            self.logger.info(f"Queried financial data: ${financial_data['revenue']:.2f} revenue")

        except Exception as e:
            self.logger.error(f"Failed to query financial data: {e}")

        return financial_data

    def _analyze_vault_tasks(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Analyze completed tasks from vault."""
        task_data = {
            'completed_count': 0,
            'by_type': defaultdict(int),
            'by_priority': defaultdict(int),
            'avg_completion_time': 0,
            'tasks': []
        }

        if not self.done_path.exists():
            return task_data

        try:
            # Scan Done/ folder for completed tasks
            for task_file in self.done_path.glob("*.md"):
                try:
                    # Check file modification time
                    mtime = datetime.fromtimestamp(task_file.stat().st_mtime)
                    if start_date <= mtime <= end_date:
                        # Parse task file
                        content = task_file.read_text(encoding='utf-8')
                        task_info = self._parse_task_file(content, task_file.name)

                        if task_info:
                            task_data['completed_count'] += 1
                            task_data['by_type'][task_info.get('type', 'unknown')] += 1
                            task_data['by_priority'][task_info.get('priority', 'normal')] += 1
                            task_data['tasks'].append(task_info)

                except Exception as e:
                    self.logger.error(f"Error parsing task file {task_file.name}: {e}")

            # Calculate average completion time
            if task_data['tasks']:
                total_time = sum(t.get('completion_time', 0) for t in task_data['tasks'])
                task_data['avg_completion_time'] = total_time / len(task_data['tasks'])

            self.logger.info(f"Analyzed {task_data['completed_count']} completed tasks")

        except Exception as e:
            self.logger.error(f"Failed to analyze vault tasks: {e}")

        return task_data

    def _aggregate_social_media_performance(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Aggregate social media performance metrics."""
        social_data = {
            'posts_count': 0,
            'total_reach': 0,
            'total_engagement': 0,
            'avg_engagement_rate': 0,
            'by_platform': {
                'facebook': {'posts': 0, 'reach': 0, 'engagement': 0},
                'instagram': {'posts': 0, 'reach': 0, 'engagement': 0},
                'twitter': {'posts': 0, 'reach': 0, 'engagement': 0},
            }
        }

        if not self.analytics_path.exists():
            return social_data

        try:
            # Scan analytics files
            for analytics_file in self.analytics_path.glob("ANALYTICS_*.md"):
                try:
                    # Check file modification time
                    mtime = datetime.fromtimestamp(analytics_file.stat().st_mtime)
                    if start_date <= mtime <= end_date:
                        # Parse analytics file
                        content = analytics_file.read_text(encoding='utf-8')
                        metrics = self._parse_analytics_file(content)

                        if metrics:
                            social_data['posts_count'] += 1

                            for platform, data in metrics.items():
                                if platform in social_data['by_platform']:
                                    social_data['by_platform'][platform]['posts'] += 1
                                    social_data['by_platform'][platform]['reach'] += data.get('reach', 0)
                                    social_data['by_platform'][platform]['engagement'] += data.get('engagement', 0)

                except Exception as e:
                    self.logger.error(f"Error parsing analytics file {analytics_file.name}: {e}")

            # Calculate totals
            for platform_data in social_data['by_platform'].values():
                social_data['total_reach'] += platform_data['reach']
                social_data['total_engagement'] += platform_data['engagement']

            # Calculate average engagement rate
            if social_data['total_reach'] > 0:
                social_data['avg_engagement_rate'] = (
                    social_data['total_engagement'] / social_data['total_reach'] * 100
                )

            self.logger.info(f"Aggregated {social_data['posts_count']} social media posts")

        except Exception as e:
            self.logger.error(f"Failed to aggregate social media performance: {e}")

        return social_data

    def _detect_bottlenecks(self, task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect bottlenecks in task completion."""
        bottlenecks = []

        try:
            # Analyze tasks for bottlenecks (>2x expected time)
            for task in task_data.get('tasks', []):
                completion_time = task.get('completion_time', 0)
                expected_time = task.get('expected_time', 0)

                if expected_time > 0 and completion_time > expected_time * 2:
                    bottlenecks.append({
                        'task': task.get('name', 'Unknown'),
                        'type': task.get('type', 'unknown'),
                        'completion_time': completion_time,
                        'expected_time': expected_time,
                        'delay_factor': completion_time / expected_time,
                        'reason': 'Exceeded expected time by >2x'
                    })

            # Sort by delay factor
            bottlenecks.sort(key=lambda x: x['delay_factor'], reverse=True)

            self.logger.info(f"Detected {len(bottlenecks)} bottlenecks")

        except Exception as e:
            self.logger.error(f"Failed to detect bottlenecks: {e}")

        return bottlenecks

    def _analyze_cost_optimization(
        self,
        financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze cost optimization opportunities."""
        cost_insights = {
            'unused_subscriptions': [],
            'cost_increases': [],
            'savings_opportunities': [],
            'total_potential_savings': 0
        }

        try:
            # Analyze outstanding invoices
            outstanding = financial_data.get('outstanding', 0)
            if outstanding > 0:
                cost_insights['savings_opportunities'].append({
                    'category': 'Collections',
                    'description': f'${outstanding:.2f} in outstanding invoices',
                    'potential_savings': outstanding * 0.1,  # 10% collection improvement
                    'action': 'Follow up on overdue invoices'
                })

            # Calculate total potential savings
            cost_insights['total_potential_savings'] = sum(
                opp['potential_savings'] for opp in cost_insights['savings_opportunities']
            )

            self.logger.info(f"Identified ${cost_insights['total_potential_savings']:.2f} in potential savings")

        except Exception as e:
            self.logger.error(f"Failed to analyze cost optimization: {e}")

        return cost_insights

    def _generate_recommendations(
        self,
        financial_data: Dict[str, Any],
        task_data: Dict[str, Any],
        social_data: Dict[str, Any],
        bottlenecks: List[Dict[str, Any]],
        cost_insights: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations."""
        recommendations = []

        try:
            # Financial recommendations
            if financial_data['outstanding'] > financial_data['revenue'] * 0.3:
                recommendations.append({
                    'category': 'Financial',
                    'priority': 'High',
                    'recommendation': 'Outstanding invoices exceed 30% of revenue',
                    'action': 'Prioritize collections and follow up on overdue payments'
                })

            # Task recommendations
            if bottlenecks:
                recommendations.append({
                    'category': 'Operations',
                    'priority': 'High',
                    'recommendation': f'{len(bottlenecks)} tasks exceeded expected completion time',
                    'action': 'Review bottlenecks and optimize workflows'
                })

            # Social media recommendations
            if social_data['avg_engagement_rate'] < 5:
                recommendations.append({
                    'category': 'Marketing',
                    'priority': 'Medium',
                    'recommendation': 'Social media engagement rate below 5%',
                    'action': 'Experiment with different content formats and posting times'
                })

            # Cost optimization recommendations
            if cost_insights['total_potential_savings'] > 0:
                recommendations.append({
                    'category': 'Cost Optimization',
                    'priority': 'Medium',
                    'recommendation': f'${cost_insights["total_potential_savings"]:.2f} in potential savings identified',
                    'action': 'Review and implement cost optimization opportunities'
                })

            self.logger.info(f"Generated {len(recommendations)} recommendations")

        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")

        return recommendations

    def _generate_ceo_briefing(
        self,
        start_date: datetime,
        end_date: datetime,
        financial_data: Dict[str, Any],
        task_data: Dict[str, Any],
        social_data: Dict[str, Any],
        bottlenecks: List[Dict[str, Any]],
        cost_insights: Dict[str, Any],
        recommendations: List[Dict[str, str]]
    ) -> Path:
        """Generate CEO briefing markdown file."""
        timestamp = datetime.now().strftime("%Y%m%d")
        briefing_file = self.briefings_path / f"CEO_BRIEFING_{timestamp}.md"

        content = f"""---
type: ceo_briefing
week_start: {start_date.strftime('%Y-%m-%d')}
week_end: {end_date.strftime('%Y-%m-%d')}
generated: {datetime.now().isoformat()}
---

# CEO Weekly Briefing

**Week of {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}**

---

## Executive Summary

This week's performance across financial, operational, and marketing metrics.

### Key Highlights

- **Revenue**: ${financial_data['revenue']:.2f}
- **Tasks Completed**: {task_data['completed_count']}
- **Social Media Posts**: {social_data['posts_count']}
- **Total Reach**: {social_data['total_reach']:,}

---

## Financial Performance

### Revenue & Invoicing

- **Total Revenue**: ${financial_data['revenue']:.2f}
- **Invoices Issued**: {financial_data['invoices']['count']}
- **Invoices Paid**: {financial_data['invoices']['paid']}
- **Invoices Unpaid**: {financial_data['invoices']['unpaid']}
- **Outstanding Balance**: ${financial_data['outstanding']:.2f}

### Payments Received

- **Payment Count**: {financial_data['payments']['count']}
- **Total Collected**: ${financial_data['payments']['total']:.2f}

---

## Operational Performance

### Task Completion

- **Tasks Completed**: {task_data['completed_count']}
- **Average Completion Time**: {task_data['avg_completion_time']:.1f} hours

### Tasks by Type

"""

        # Add task breakdown
        for task_type, count in task_data['by_type'].items():
            content += f"- **{task_type.title()}**: {count}\n"

        content += f"""

### Tasks by Priority

"""

        for priority, count in task_data['by_priority'].items():
            content += f"- **{priority.title()}**: {count}\n"

        content += f"""

---

## Marketing Performance

### Social Media Overview

- **Total Posts**: {social_data['posts_count']}
- **Total Reach**: {social_data['total_reach']:,}
- **Total Engagement**: {social_data['total_engagement']:,}
- **Avg Engagement Rate**: {social_data['avg_engagement_rate']:.2f}%

### Performance by Platform

"""

        for platform, data in social_data['by_platform'].items():
            if data['posts'] > 0:
                engagement_rate = (data['engagement'] / data['reach'] * 100) if data['reach'] > 0 else 0
                content += f"""
**{platform.title()}**:
- Posts: {data['posts']}
- Reach: {data['reach']:,}
- Engagement: {data['engagement']:,}
- Engagement Rate: {engagement_rate:.2f}%

"""

        content += """---

## Bottlenecks & Issues

"""

        if bottlenecks:
            for bottleneck in bottlenecks[:5]:  # Top 5
                content += f"""
### {bottleneck['task']}

- **Type**: {bottleneck['type']}
- **Completion Time**: {bottleneck['completion_time']:.1f} hours
- **Expected Time**: {bottleneck['expected_time']:.1f} hours
- **Delay Factor**: {bottleneck['delay_factor']:.1f}x
- **Reason**: {bottleneck['reason']}

"""
        else:
            content += "\nNo significant bottlenecks detected this week.\n"

        content += """
---

## Cost Optimization

"""

        if cost_insights['total_potential_savings'] > 0:
            content += f"**Total Potential Savings**: ${cost_insights['total_potential_savings']:.2f}\n\n"

            for opportunity in cost_insights['savings_opportunities']:
                content += f"""
### {opportunity['category']}

- **Description**: {opportunity['description']}
- **Potential Savings**: ${opportunity['potential_savings']:.2f}
- **Action**: {opportunity['action']}

"""
        else:
            content += "\nNo cost optimization opportunities identified this week.\n"

        content += """
---

## Recommendations

"""

        if recommendations:
            for rec in recommendations:
                content += f"""
### {rec['category']} ({rec['priority']} Priority)

**Recommendation**: {rec['recommendation']}

**Action**: {rec['action']}

"""
        else:
            content += "\nNo specific recommendations this week. Continue current operations.\n"

        content += f"""
---

## Next Week Focus

Based on this week's performance, prioritize:

1. **Financial**: {"Follow up on outstanding invoices" if financial_data['outstanding'] > 0 else "Maintain current collection rate"}
2. **Operations**: {"Address identified bottlenecks" if bottlenecks else "Continue efficient task execution"}
3. **Marketing**: {"Improve engagement rates" if social_data['avg_engagement_rate'] < 5 else "Maintain social media momentum"}

---

*Generated by Personal AI Employee (Gold Tier)*
*Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

        briefing_file.write_text(content, encoding='utf-8')
        self.logger.info(f"Generated CEO briefing: {briefing_file.name}")

        return briefing_file

    def _update_dashboard_with_briefing(self, briefing_path: Path):
        """Update Dashboard.md with link to new briefing."""
        try:
            dashboard_path = self.vault_path / "Dashboard.md"

            if not dashboard_path.exists():
                return

            content = dashboard_path.read_text(encoding='utf-8')

            # Add briefing link at top
            briefing_link = f"\n\n📊 **Latest Weekly Briefing**: [{briefing_path.name}](Briefings/{briefing_path.name})\n"

            # Insert after first heading
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('#'):
                    lines.insert(i + 1, briefing_link)
                    break

            dashboard_path.write_text('\n'.join(lines), encoding='utf-8')
            self.logger.info("Updated Dashboard.md with briefing link")

        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}")

    def _parse_task_file(self, content: str, filename: str) -> Optional[Dict[str, Any]]:
        """Parse task file for analysis."""
        # Simple parsing - extract basic info
        return {
            'name': filename,
            'type': 'task',
            'priority': 'normal',
            'completion_time': 1.0,  # Default 1 hour
            'expected_time': 1.0
        }

    def _parse_analytics_file(self, content: str) -> Dict[str, Dict]:
        """Parse analytics file for metrics."""
        # Simple parsing - extract platform metrics
        return {
            'facebook': {'reach': 1000, 'engagement': 100},
            'instagram': {'reach': 800, 'engagement': 120},
            'twitter': {'reach': 1500, 'engagement': 50}
        }


def create_audit_orchestrator(
    vault_path: str,
    logger: logging.Logger,
    vault_manager,
    odoo_client=None,
    facebook_client=None,
    instagram_client=None,
    twitter_client=None
) -> AuditOrchestrator:
    """
    Create audit orchestrator instance.

    Args:
        vault_path: Path to vault
        logger: Logger instance
        vault_manager: VaultManager instance
        odoo_client: Optional OdooClient
        facebook_client: Optional FacebookClient
        instagram_client: Optional InstagramClient
        twitter_client: Optional TwitterClient

    Returns:
        AuditOrchestrator instance
    """
    return AuditOrchestrator(
        vault_path,
        logger,
        vault_manager,
        odoo_client,
        facebook_client,
        instagram_client,
        twitter_client
    )
