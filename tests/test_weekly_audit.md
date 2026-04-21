# Weekly Audit Integration Tests

**Test Suite**: Weekly business and accounting audit generation

**Purpose**: Validate that the audit orchestrator correctly aggregates data from multiple sources, detects bottlenecks, identifies cost optimization opportunities, and generates comprehensive CEO briefings.

---

## Test Environment Setup

### Prerequisites

1. **Vault Structure**:
   ```
   AI_Employee_Vault/
   ├── Done/                    # Completed tasks
   ├── Social_Media/
   │   └── Analytics/           # Social media metrics
   ├── Briefings/               # Generated briefings
   └── Dashboard.md             # Main dashboard
   ```

2. **Sample Data**:
   - Completed tasks in Done/ folder (last 7 days)
   - Social media analytics files
   - Odoo connection (optional for full test)

3. **Configuration**:
   ```bash
   ENABLE_WEEKLY_AUDIT=true
   ENABLE_ODOO=true  # Optional
   ENABLE_SOCIAL_MEDIA=true  # Optional
   ```

---

## Test Case 1: Full Data Availability

**Objective**: Test weekly audit with all data sources available

**Setup**:
1. Ensure Odoo client is connected
2. Create sample completed tasks in Done/
3. Create sample analytics files in Social_Media/Analytics/
4. Ensure Dashboard.md exists

**Test Steps**:

```python
from orchestrators.audit_orchestrator import create_audit_orchestrator
from integrations.odoo_client import create_odoo_client
from integrations.facebook_client import create_facebook_client
from integrations.instagram_client import create_instagram_client
from integrations.twitter_client import create_twitter_client
import logging

# Initialize logger
logger = logging.getLogger("TestAudit")

# Initialize clients
odoo_client = create_odoo_client(vault_path="AI_Employee_Vault")
facebook_client = create_facebook_client(vault_path="AI_Employee_Vault")
instagram_client = create_instagram_client(vault_path="AI_Employee_Vault")
twitter_client = create_twitter_client(vault_path="AI_Employee_Vault")

# Create audit orchestrator
audit_orch = create_audit_orchestrator(
    vault_path="AI_Employee_Vault",
    logger=logger,
    vault_manager=vault_manager,
    odoo_client=odoo_client,
    facebook_client=facebook_client,
    instagram_client=instagram_client,
    twitter_client=twitter_client
)

# Generate weekly audit
briefing_path = audit_orch.generate_weekly_audit()

print(f"Briefing generated: {briefing_path}")
```

**Expected Results**:
- ✓ Briefing file created in Briefings/ folder
- ✓ Filename format: CEO_BRIEFING_YYYYMMDD.md
- ✓ Valid YAML frontmatter with week_start, week_end, generated
- ✓ Executive Summary section with key highlights
- ✓ Financial Performance section with Odoo data
- ✓ Operational Performance section with task data
- ✓ Marketing Performance section with social media data
- ✓ Bottlenecks section (if any detected)
- ✓ Cost Optimization section (if opportunities found)
- ✓ Recommendations section with actionable insights
- ✓ Next Week Focus section
- ✓ Dashboard.md updated with briefing link

**Validation**:
```python
import yaml
from pathlib import Path

# Read briefing file
briefing_content = briefing_path.read_text(encoding='utf-8')

# Validate frontmatter
assert briefing_content.startswith('---')
frontmatter_end = briefing_content.find('---', 3)
frontmatter = yaml.safe_load(briefing_content[3:frontmatter_end])

assert frontmatter['type'] == 'ceo_briefing'
assert 'week_start' in frontmatter
assert 'week_end' in frontmatter
assert 'generated' in frontmatter

# Validate sections
assert '# CEO Weekly Briefing' in briefing_content
assert '## Executive Summary' in briefing_content
assert '## Financial Performance' in briefing_content
assert '## Operational Performance' in briefing_content
assert '## Marketing Performance' in briefing_content
assert '## Recommendations' in briefing_content

# Validate Dashboard.md update
dashboard_path = Path("AI_Employee_Vault/Dashboard.md")
dashboard_content = dashboard_path.read_text(encoding='utf-8')
assert briefing_path.name in dashboard_content

print("✓ Test Case 1 PASSED: Full data availability")
```

---

## Test Case 2: Partial Data Availability (No Odoo)

**Objective**: Test weekly audit when Odoo is unavailable

**Setup**:
1. Set odoo_client=None
2. Create sample completed tasks in Done/
3. Create sample analytics files in Social_Media/Analytics/

**Test Steps**:

```python
# Create audit orchestrator without Odoo
audit_orch = create_audit_orchestrator(
    vault_path="AI_Employee_Vault",
    logger=logger,
    vault_manager=vault_manager,
    odoo_client=None,  # Odoo unavailable
    facebook_client=facebook_client,
    instagram_client=instagram_client,
    twitter_client=twitter_client
)

# Generate weekly audit
briefing_path = audit_orch.generate_weekly_audit()
```

**Expected Results**:
- ✓ Briefing generated successfully
- ✓ Financial Performance section shows zero values
- ✓ Operational Performance section populated
- ✓ Marketing Performance section populated
- ✓ Warning logged: "Odoo client not available, skipping financial data"
- ✓ Recommendations exclude financial recommendations

**Validation**:
```python
briefing_content = briefing_path.read_text(encoding='utf-8')

# Financial section should show zeros
assert '**Total Revenue**: $0.00' in briefing_content
assert '**Invoices Issued**: 0' in briefing_content

# Other sections should be populated
assert '**Tasks Completed**:' in briefing_content
assert '**Total Posts**:' in briefing_content

print("✓ Test Case 2 PASSED: Partial data availability")
```

---

## Test Case 3: Bottleneck Detection

**Objective**: Test bottleneck detection for tasks exceeding 2x expected time

**Setup**:
1. Create sample tasks with completion_time > 2x expected_time
2. Place in Done/ folder with modification time in last 7 days

**Sample Task File** (Done/TASK_DATABASE_MIGRATION.md):
```markdown
---
type: task
title: Database Migration
task_type: development
priority: high
expected_time: 3.0
completion_time: 8.0
completed_at: 2026-04-15T14:30:00
---

# Database Migration Task

Migrated database schema from v1 to v2.

## Challenges
- Unexpected data inconsistencies
- Required additional validation steps
- Performance optimization needed

## Resolution
- Fixed data inconsistencies
- Added validation layer
- Optimized queries
```

**Test Steps**:

```python
# Generate weekly audit
briefing_path = audit_orch.generate_weekly_audit()

# Read briefing
briefing_content = briefing_path.read_text(encoding='utf-8')
```

**Expected Results**:
- ✓ Bottleneck detected for Database Migration task
- ✓ Delay factor calculated: 8.0 / 3.0 = 2.67x
- ✓ Bottleneck listed in Bottlenecks & Issues section
- ✓ Recommendation generated: "Review bottlenecks and optimize workflows"

**Validation**:
```python
# Check bottleneck section
assert '## Bottlenecks & Issues' in briefing_content
assert 'Database Migration' in briefing_content
assert 'Delay Factor: 2.7x' in briefing_content

# Check recommendation
assert 'exceeded expected completion time' in briefing_content
assert 'Review bottlenecks and optimize workflows' in briefing_content

print("✓ Test Case 3 PASSED: Bottleneck detection")
```

---

## Test Case 4: Cost Optimization Analysis

**Objective**: Test cost optimization recommendations

**Setup**:
1. Configure Odoo with outstanding invoices > 30% of revenue
2. Generate weekly audit

**Sample Financial Data**:
```python
financial_data = {
    'revenue': 50000.00,
    'invoices': {'count': 10, 'total': 50000.00, 'paid': 7, 'unpaid': 3},
    'payments': {'count': 7, 'total': 35000.00},
    'outstanding': 15000.00,  # 30% of revenue
}
```

**Test Steps**:

```python
# Generate weekly audit
briefing_path = audit_orch.generate_weekly_audit()

# Read briefing
briefing_content = briefing_path.read_text(encoding='utf-8')
```

**Expected Results**:
- ✓ Cost optimization opportunity detected
- ✓ Potential savings calculated: $15,000 * 0.1 = $1,500
- ✓ Recommendation: "Follow up on overdue invoices"
- ✓ High priority financial recommendation generated

**Validation**:
```python
# Check cost optimization section
assert '## Cost Optimization' in briefing_content
assert 'Total Potential Savings: $1,500.00' in briefing_content
assert 'outstanding invoices' in briefing_content.lower()

# Check financial recommendation
assert 'Outstanding invoices exceed 30% of revenue' in briefing_content
assert 'Prioritize collections' in briefing_content

print("✓ Test Case 4 PASSED: Cost optimization analysis")
```

---

## Test Case 5: Social Media Performance Analysis

**Objective**: Test social media metrics aggregation and engagement rate calculation

**Setup**:
1. Create sample analytics files for all platforms
2. Place in Social_Media/Analytics/ with modification time in last 7 days

**Sample Analytics File** (Social_Media/Analytics/ANALYTICS_20260415_product_launch.md):
```markdown
---
type: social_media_analytics
business_update: Product Launch Announcement
collected_at: 2026-04-15T12:00:00
---

## Social Media Analytics: Product Launch Announcement

**Metrics Collected**: 2026-04-15 at 12:00

### Facebook Performance

- **reach**: 10000
- **engagement**: 600

**Engagement**:
- Likes: 400
- Comments: 150
- Shares: 50

### Instagram Performance

- **reach**: 8000
- **engagement**: 640

**Engagement**:
- Likes: 500
- Comments: 140

### Twitter Performance

- **reach**: 7000
- **engagement**: 260

**Engagement**:
- Likes: 180
- Retweets: 60
- Replies: 20
```

**Test Steps**:

```python
# Generate weekly audit
briefing_path = audit_orch.generate_weekly_audit()

# Read briefing
briefing_content = briefing_path.read_text(encoding='utf-8')
```

**Expected Results**:
- ✓ Total posts counted: 1
- ✓ Total reach: 10,000 + 8,000 + 7,000 = 25,000
- ✓ Total engagement: 600 + 640 + 260 = 1,500
- ✓ Avg engagement rate: (1,500 / 25,000) * 100 = 6.00%
- ✓ Platform breakdown shows individual metrics
- ✓ Engagement rates calculated per platform

**Validation**:
```python
# Check social media section
assert '## Marketing Performance' in briefing_content
assert 'Total Posts: 1' in briefing_content
assert 'Total Reach: 25,000' in briefing_content
assert 'Total Engagement: 1,500' in briefing_content
assert 'Avg Engagement Rate: 6.00%' in briefing_content

# Check platform breakdown
assert '**Facebook**:' in briefing_content
assert 'Reach: 10,000' in briefing_content
assert '**Instagram**:' in briefing_content
assert 'Reach: 8,000' in briefing_content
assert '**Twitter**:' in briefing_content
assert 'Reach: 7,000' in briefing_content

print("✓ Test Case 5 PASSED: Social media performance analysis")
```

---

## Test Case 6: Dashboard Update

**Objective**: Test Dashboard.md update with briefing link

**Setup**:
1. Ensure Dashboard.md exists with standard structure
2. Generate weekly audit

**Sample Dashboard.md**:
```markdown
# Personal AI Employee Dashboard

**System Status**: Active
**Last Updated**: 2026-04-17 10:00

## Recent Activity

- Task processing active
- Email monitoring active
- Social media automation active
```

**Test Steps**:

```python
# Generate weekly audit
briefing_path = audit_orch.generate_weekly_audit()

# Read updated Dashboard.md
dashboard_path = Path("AI_Employee_Vault/Dashboard.md")
dashboard_content = dashboard_path.read_text(encoding='utf-8')
```

**Expected Results**:
- ✓ Briefing link added after first heading
- ✓ Link format: `📊 **Latest Weekly Briefing**: [CEO_BRIEFING_20260417.md](Briefings/CEO_BRIEFING_20260417.md)`
- ✓ Link is clickable in Obsidian
- ✓ Original dashboard content preserved

**Validation**:
```python
# Check briefing link
assert '📊 **Latest Weekly Briefing**:' in dashboard_content
assert f'[{briefing_path.name}]' in dashboard_content
assert f'(Briefings/{briefing_path.name})' in dashboard_content

# Check link position (after first heading)
lines = dashboard_content.split('\n')
heading_index = next(i for i, line in enumerate(lines) if line.startswith('#'))
link_index = next(i for i, line in enumerate(lines) if '📊 **Latest Weekly Briefing**:' in line)
assert link_index > heading_index

print("✓ Test Case 6 PASSED: Dashboard update")
```

---

## Test Case 7: Recommendation Generation

**Objective**: Test recommendation generation based on multiple data sources

**Setup**:
1. Configure data to trigger multiple recommendations:
   - Outstanding invoices > 30% revenue (Financial)
   - Tasks with bottlenecks (Operations)
   - Engagement rate < 5% (Marketing)
   - Cost savings opportunities (Cost Optimization)

**Test Steps**:

```python
# Generate weekly audit with configured data
briefing_path = audit_orch.generate_weekly_audit()

# Read briefing
briefing_content = briefing_path.read_text(encoding='utf-8')
```

**Expected Results**:
- ✓ Financial recommendation (High Priority)
- ✓ Operations recommendation (High Priority)
- ✓ Marketing recommendation (Medium Priority)
- ✓ Cost Optimization recommendation (Medium Priority)
- ✓ Each recommendation has category, priority, recommendation text, and action

**Validation**:
```python
# Check recommendations section
assert '## Recommendations' in briefing_content

# Financial recommendation
assert 'Financial (High Priority)' in briefing_content
assert 'Outstanding invoices exceed 30% of revenue' in briefing_content
assert 'Prioritize collections' in briefing_content

# Operations recommendation
assert 'Operations (High Priority)' in briefing_content
assert 'exceeded expected completion time' in briefing_content
assert 'Review bottlenecks' in briefing_content

# Marketing recommendation
assert 'Marketing (Medium Priority)' in briefing_content
assert 'engagement rate below 5%' in briefing_content
assert 'Experiment with different content formats' in briefing_content

# Cost optimization recommendation
assert 'Cost Optimization (Medium Priority)' in briefing_content
assert 'potential savings identified' in briefing_content
assert 'Review and implement cost optimization' in briefing_content

print("✓ Test Case 7 PASSED: Recommendation generation")
```

---

## Test Case 8: Scheduled Execution

**Objective**: Test weekly audit scheduled execution (Sunday 11:00 PM)

**Setup**:
1. Configure scheduler with weekly audit task
2. Mock time to Sunday 11:00 PM
3. Verify audit runs automatically

**Test Steps**:

```python
from unittest.mock import patch
from datetime import datetime

# Mock current time to Sunday 11:00 PM
with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2026, 4, 20, 23, 0, 0)  # Sunday
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
    
    # Trigger scheduler
    scheduler.check_and_run_tasks()
    
    # Wait for audit to complete
    import time
    time.sleep(5)
```

**Expected Results**:
- ✓ Audit triggered automatically at scheduled time
- ✓ Briefing generated without manual intervention
- ✓ Log entry: "Running scheduled weekly audit"
- ✓ Log entry: "Weekly audit complete: Briefings/CEO_BRIEFING_20260420.md"

**Validation**:
```python
# Check log file
log_path = Path("AI_Employee_Vault/Logs/AuditOrchestrator.log")
log_content = log_path.read_text(encoding='utf-8')

assert 'Running scheduled weekly audit' in log_content
assert 'Weekly audit complete' in log_content

# Check briefing exists
briefing_path = Path("AI_Employee_Vault/Briefings/CEO_BRIEFING_20260420.md")
assert briefing_path.exists()

print("✓ Test Case 8 PASSED: Scheduled execution")
```

---

## Test Case 9: Error Handling - Missing Data Sources

**Objective**: Test graceful handling when data sources are missing

**Setup**:
1. Remove Done/ folder
2. Remove Social_Media/Analytics/ folder
3. Set odoo_client=None

**Test Steps**:

```python
# Generate weekly audit with no data sources
briefing_path = audit_orch.generate_weekly_audit()

# Read briefing
briefing_content = briefing_path.read_text(encoding='utf-8')
```

**Expected Results**:
- ✓ Briefing generated successfully (no crash)
- ✓ All sections present with zero/empty values
- ✓ Warnings logged for missing data sources
- ✓ Recommendations section: "No specific recommendations this week"

**Validation**:
```python
# Check briefing has all sections
assert '## Financial Performance' in briefing_content
assert '## Operational Performance' in briefing_content
assert '## Marketing Performance' in briefing_content

# Check zero values
assert 'Total Revenue: $0.00' in briefing_content
assert 'Tasks Completed: 0' in briefing_content
assert 'Total Posts: 0' in briefing_content

# Check recommendations
assert 'No specific recommendations this week' in briefing_content

print("✓ Test Case 9 PASSED: Error handling - missing data sources")
```

---

## Test Case 10: Multiple Briefings

**Objective**: Test that multiple briefings can be generated without conflicts

**Setup**:
1. Generate first briefing
2. Wait 1 second
3. Generate second briefing

**Test Steps**:

```python
# Generate first briefing
briefing_path_1 = audit_orch.generate_weekly_audit()

# Wait
import time
time.sleep(1)

# Generate second briefing
briefing_path_2 = audit_orch.generate_weekly_audit()
```

**Expected Results**:
- ✓ Both briefings created successfully
- ✓ Different filenames (timestamp-based)
- ✓ Dashboard.md shows latest briefing link
- ✓ Both briefings accessible in Briefings/ folder

**Validation**:
```python
# Check both files exist
assert briefing_path_1.exists()
assert briefing_path_2.exists()

# Check different filenames
assert briefing_path_1.name != briefing_path_2.name

# Check Dashboard.md shows latest
dashboard_path = Path("AI_Employee_Vault/Dashboard.md")
dashboard_content = dashboard_path.read_text(encoding='utf-8')
assert briefing_path_2.name in dashboard_content

print("✓ Test Case 10 PASSED: Multiple briefings")
```

---

## Performance Tests

### Test Case 11: Large Dataset Performance

**Objective**: Test performance with large datasets

**Setup**:
- 100+ completed tasks in Done/
- 50+ analytics files
- Odoo with 100+ invoices

**Expected Results**:
- ✓ Audit completes in < 30 seconds
- ✓ Memory usage < 500MB
- ✓ No performance degradation

---

## Integration Tests

### Test Case 12: End-to-End Workflow

**Objective**: Test complete workflow from data collection to briefing

**Steps**:
1. Create Odoo invoices
2. Complete tasks and move to Done/
3. Publish social media posts
4. Collect engagement metrics
5. Trigger weekly audit
6. Verify briefing accuracy

**Expected Results**:
- ✓ All data sources integrated correctly
- ✓ Metrics calculated accurately
- ✓ Briefing reflects actual business activity

---

## Summary

**Total Test Cases**: 12
- **Unit Tests**: 7 (TC1-TC7)
- **Integration Tests**: 3 (TC8-TC10)
- **Performance Tests**: 1 (TC11)
- **End-to-End Tests**: 1 (TC12)

**Coverage**:
- ✓ Data collection from all sources
- ✓ Bottleneck detection
- ✓ Cost optimization analysis
- ✓ Recommendation generation
- ✓ Briefing generation
- ✓ Dashboard update
- ✓ Scheduled execution
- ✓ Error handling
- ✓ Performance validation

**Success Criteria**:
- All test cases pass
- No data loss or corruption
- Graceful error handling
- Performance within acceptable limits
- Accurate calculations and recommendations
