# Data Model: Gold Tier Autonomous AI Employee

**Feature**: 001-gold-tier  
**Date**: 2026-04-16  
**Purpose**: Define entities, relationships, and state transitions for Gold tier

## Core Entities

### 1. Task
**Purpose**: Represents work to be done by the AI employee

**Attributes**:
- `id`: Unique identifier (filename without extension)
- `type`: Task category (email, whatsapp, linkedin, invoice, payment, social_post, audit, general)
- `priority`: Urgency level (high, medium, low)
- `status`: Current state (pending, in_progress, awaiting_approval, approved, rejected, completed, failed)
- `created_date`: ISO 8601 timestamp
- `due_date`: ISO 8601 timestamp (optional)
- `assigned_to`: Component responsible (ralph_wiggum, approval_orchestrator, audit_orchestrator)
- `dependencies`: List of task IDs that must complete first
- `completion_promise`: Boolean indicating if task uses promise-based completion
- `iteration_count`: Number of Ralph Wiggum loop iterations (max 10)
- `error_count`: Number of failed attempts
- `last_error`: Most recent error message

**Relationships**:
- Has many: Approval Requests (0..*)
- Has many: Error Logs (0..*)
- Belongs to: User (1)

**State Transitions**:
```
pending → in_progress → awaiting_approval → approved → completed
                     ↓                    ↓
                   failed              rejected
```

**Validation Rules**:
- `type` must be one of defined categories
- `status` transitions must follow state machine
- `iteration_count` must not exceed 10
- `due_date` must be after `created_date`

---

### 2. Invoice
**Purpose**: Financial document for billing customers

**Attributes**:
- `invoice_number`: Unique identifier (e.g., INV-2026-001)
- `customer_name`: Customer display name
- `customer_id`: Odoo customer ID (after sync)
- `line_items`: Array of {description, quantity, unit_price, total}
- `subtotal`: Sum of line items
- `tax_amount`: Calculated tax
- `total_amount`: Subtotal + tax
- `currency`: ISO 4217 code (default: USD)
- `issue_date`: ISO 8601 timestamp
- `due_date`: ISO 8601 timestamp
- `status`: Current state (draft, sent, paid, overdue, cancelled)
- `odoo_id`: Odoo invoice ID (null until synced)
- `payment_status`: Payment state (unpaid, partial, paid)
- `notes`: Additional information

**Relationships**:
- Has many: Payments (0..*)
- Belongs to: Customer (1)
- Syncs with: Odoo Invoice (0..1)

**State Transitions**:
```
draft → sent → paid
            ↓
         overdue → paid
            ↓
        cancelled
```

**Validation Rules**:
- `invoice_number` must be unique
- `total_amount` must equal sum of line items + tax
- `due_date` must be after `issue_date`
- `status` cannot transition from paid to unpaid
- `odoo_id` is immutable once set

---

### 3. Payment
**Purpose**: Financial transaction recording payment received

**Attributes**:
- `payment_id`: Unique identifier (e.g., PAY-2026-001)
- `invoice_reference`: Invoice number being paid
- `amount`: Payment amount
- `currency`: ISO 4217 code
- `payment_date`: ISO 8601 timestamp
- `payment_method`: Method used (bank_transfer, credit_card, cash, check)
- `transaction_id`: External transaction reference
- `odoo_id`: Odoo payment ID (null until synced)
- `reconciliation_status`: Sync state (pending, synced, failed)
- `notes`: Additional information

**Relationships**:
- Belongs to: Invoice (1)
- Syncs with: Odoo Payment (0..1)

**State Transitions**:
```
pending → synced
       ↓
     failed → synced (after retry)
```

**Validation Rules**:
- `amount` must be positive
- `payment_date` must not be in future
- `invoice_reference` must exist
- `odoo_id` is immutable once set
- Cannot delete payment once synced to Odoo

---

### 4. Social Media Post
**Purpose**: Content for publishing to social media platforms

**Attributes**:
- `post_id`: Unique identifier (e.g., POST-2026-001)
- `platform`: Target platform (facebook, instagram, twitter)
- `content`: Post text/caption
- `images`: Array of image file paths
- `hashtags`: Array of hashtag strings (Instagram/Twitter)
- `link`: URL to include (Facebook/Twitter)
- `scheduled_time`: ISO 8601 timestamp for posting
- `approval_status`: Approval state (draft, pending_approval, approved, rejected, published)
- `platform_post_id`: Platform-assigned ID after publishing
- `published_at`: ISO 8601 timestamp of actual publication
- `engagement_metrics`: Object with {likes, comments, shares, reach, impressions}
- `metrics_collected_at`: ISO 8601 timestamp of last metrics update

**Relationships**:
- Has one: Approval Request (0..1)
- Belongs to: Business Update (1)

**State Transitions**:
```
draft → pending_approval → approved → published
                        ↓
                    rejected
```

**Validation Rules**:
- `platform` must be facebook, instagram, or twitter
- `content` length: Twitter ≤280 chars, Instagram ≤2200 chars, Facebook ≤63206 chars
- Instagram requires at least one image
- `scheduled_time` must be in future (when draft)
- `platform_post_id` is immutable once set
- Cannot edit after published

---

### 5. Audit Report
**Purpose**: Weekly business summary for CEO briefing

**Attributes**:
- `report_id`: Unique identifier (e.g., AUDIT-2026-W16)
- `report_date`: ISO 8601 timestamp (Monday of report week)
- `period_start`: ISO 8601 timestamp (previous Monday)
- `period_end`: ISO 8601 timestamp (Sunday before report)
- `revenue`: Total revenue for period
- `expenses`: Total expenses for period
- `profit`: Revenue - expenses
- `task_metrics`: Object with {completed_count, avg_completion_time, bottlenecks}
- `social_metrics`: Object with {total_engagement, best_post, platform_comparison}
- `cost_optimizations`: Array of {service, cost, recommendation}
- `recommendations`: Array of actionable suggestions
- `generated_at`: ISO 8601 timestamp of report generation

**Relationships**:
- Aggregates: Tasks (many)
- Aggregates: Invoices (many)
- Aggregates: Payments (many)
- Aggregates: Social Media Posts (many)

**Validation Rules**:
- `report_date` must be Monday
- `period_end` must be after `period_start`
- `profit` must equal `revenue` - `expenses`
- Report is immutable once generated

---

### 6. Error Log
**Purpose**: Record of system errors and recovery attempts

**Attributes**:
- `log_id`: Unique identifier (UUID)
- `timestamp`: ISO 8601 timestamp
- `error_type`: Category (transient, permanent, auth, validation, network)
- `component`: Source of error (ralph_wiggum, odoo_client, facebook_client, etc.)
- `message`: Human-readable error description
- `stack_trace`: Full error stack (for debugging)
- `retry_count`: Number of retry attempts
- `resolution_status`: Current state (pending, retrying, resolved, escalated)
- `task_id`: Associated task (if applicable)
- `context`: Additional error context (JSON)

**Relationships**:
- Belongs to: Task (0..1)
- Belongs to: Component (1)

**State Transitions**:
```
pending → retrying → resolved
              ↓
          escalated
```

**Validation Rules**:
- `error_type` must be one of defined categories
- `retry_count` must not exceed 5 for transient errors
- `resolution_status` must follow state machine
- Permanent errors skip retrying, go directly to escalated

---

### 7. MCP Server
**Purpose**: External integration endpoint status

**Attributes**:
- `name`: Server identifier (email, odoo, facebook, instagram, twitter)
- `type`: Integration category (communication, accounting, social_media)
- `status`: Current state (running, stopped, error, unreachable)
- `last_health_check`: ISO 8601 timestamp
- `capabilities`: Array of tool names exposed
- `authentication_status`: Auth state (valid, expired, invalid, missing)
- `error_count`: Number of consecutive failures
- `last_error`: Most recent error message

**Relationships**:
- Has many: Error Logs (0..*)

**State Transitions**:
```
stopped → running → error → running (after recovery)
                 ↓
            unreachable → running (after reconnect)
```

**Validation Rules**:
- `name` must be unique
- `status` transitions must follow state machine
- `authentication_status` must be valid for status=running
- Health check must occur every 60 seconds

---

## Entity Relationships Diagram

```
User (1)
  ├── has many Tasks (*)
  ├── has many Invoices (*)
  └── has many Social Media Posts (*)

Task (*)
  ├── has many Approval Requests (*)
  ├── has many Error Logs (*)
  └── references Invoice/Payment/Post (0..1)

Invoice (*)
  ├── has many Payments (*)
  ├── syncs with Odoo Invoice (0..1)
  └── belongs to Customer (1)

Payment (*)
  ├── belongs to Invoice (1)
  └── syncs with Odoo Payment (0..1)

Social Media Post (*)
  ├── has one Approval Request (0..1)
  └── belongs to Business Update (1)

Audit Report (*)
  ├── aggregates Tasks (*)
  ├── aggregates Invoices (*)
  ├── aggregates Payments (*)
  └── aggregates Social Media Posts (*)

Error Log (*)
  ├── belongs to Task (0..1)
  └── belongs to Component (1)

MCP Server (*)
  └── has many Error Logs (*)
```

---

## File Storage Mapping

### Vault Structure
```
AI_Employee_Vault/
├── Needs_Action/
│   ├── TASK_{id}.md              → Task (status=pending)
│   ├── EMAIL_{id}.md             → Task (type=email)
│   ├── WHATSAPP_{id}.md          → Task (type=whatsapp)
│   └── INVOICE_{id}.md           → Task (type=invoice)
│
├── Pending_Approval/
│   ├── APPROVAL_EMAIL_{id}.md    → Task (status=awaiting_approval)
│   ├── APPROVAL_PAYMENT_{id}.md  → Task (status=awaiting_approval)
│   └── APPROVAL_SOCIAL_{id}.md   → Social Media Post (approval_status=pending_approval)
│
├── Approved/
│   └── APPROVAL_{type}_{id}.md   → Task (status=approved)
│
├── Rejected/
│   └── APPROVAL_{type}_{id}.md   → Task (status=rejected)
│
├── Done/
│   └── TASK_{id}.md              → Task (status=completed)
│
├── Errors/
│   └── ERROR_{id}.md             → Error Log
│
├── Logs/
│   └── YYYY-MM-DD.json           → Array of Error Logs
│
├── Accounting/
│   ├── Invoices/
│   │   └── INV-{number}.md       → Invoice
│   ├── Payments/
│   │   └── PAY-{number}.md       → Payment
│   └── Reports/
│       └── YYYY-MM-DD_financial.md → Financial summary
│
├── Social_Media/
│   ├── Drafts/
│   │   └── POST-{id}.md          → Social Media Post (approval_status=draft)
│   ├── Published/
│   │   └── POST-{id}.md          → Social Media Post (approval_status=published)
│   └── Analytics/
│       └── YYYY-MM-DD_engagement.md → Engagement metrics
│
└── Briefings/
    └── YYYY-MM-DD_weekly_briefing.md → Audit Report
```

---

## Data Consistency Rules

### 1. Task Lifecycle
- Task file location must match status:
  - `pending` → Needs_Action/
  - `awaiting_approval` → Pending_Approval/
  - `approved` → Approved/
  - `rejected` → Rejected/
  - `completed` → Done/
  - `failed` → Errors/

### 2. Odoo Synchronization
- Invoice/Payment with `odoo_id` is immutable (cannot edit core fields)
- Sync failures must create Error Log and queue for retry
- Bidirectional sync: vault → Odoo (push), Odoo → vault (pull daily)

### 3. Social Media Posts
- Draft posts can be edited freely
- Pending approval posts are immutable until approved/rejected
- Published posts are immutable (cannot edit or delete)
- Engagement metrics updated 24 hours after publishing

### 4. Audit Reports
- Generated every Sunday 11:00 PM
- Immutable once generated
- References all entities from previous week
- Dashboard.md updated with link to latest report

### 5. Error Logs
- All errors must be logged (no silent failures)
- Transient errors retry with exponential backoff (max 5 attempts)
- Permanent errors escalate immediately (create alert file)
- Logs retained for 90 days, then archived

---

## Performance Considerations

### Indexing Strategy
- Task files indexed by status (folder-based)
- Invoices indexed by invoice_number (filename)
- Payments indexed by payment_id (filename)
- Social posts indexed by post_id (filename)
- Logs indexed by date (filename)

### Caching Strategy
- MCP server health status cached for 60 seconds
- Odoo authentication token cached until expiration
- Social media rate limits cached per platform
- Dashboard.md regenerated on significant events only

### Scalability Limits
- Max 50 tasks per day (design target)
- Max 100 invoices per month
- Max 30 social posts per month (10 per platform)
- Max 1000 log entries per day
- 90-day log retention (auto-cleanup)

---

## Migration Notes

### From Silver to Gold
- No schema changes to existing entities (Task, Invoice, Payment)
- Add new entities: Social Media Post, Audit Report, Error Log, MCP Server
- Add new vault folders: Accounting/, Social_Media/
- Existing Bronze/Silver data remains compatible
- No data migration required (additive changes only)
