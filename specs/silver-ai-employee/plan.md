# Implementation Plan: Silver Tier Personal AI Employee

**Branch**: `silver-ai-employee` | **Date**: 2026-04-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/silver-ai-employee/spec.md`

## Summary

Extend Bronze tier AI Employee with multi-channel monitoring (Gmail, WhatsApp, LinkedIn), external action capabilities via MCP server, human-in-the-loop approval workflow, and scheduled automation. This transforms the system from passive file monitoring to active business communication management.

**Technical Approach**: Add Gmail API watcher (OAuth2), WhatsApp Web watcher (Playwright), LinkedIn automation. Implement Node.js MCP server for email sending. Create approval orchestrator that watches /Pending_Approval folder and executes approved actions. Use Python schedule library for daily briefings. All new functionality exposed as Agent Skills.

## Technical Context

**Language/Version**: Python 3.13+ (watchers, orchestrator), Node.js 24+ (MCP server)  
**Primary Dependencies**: 
- Python: google-api-python-client, google-auth, playwright, schedule
- Node.js: @modelcontextprotocol/sdk, nodemailer
**Storage**: Local filesystem - Obsidian vault (markdown files)  
**Testing**: Manual testing for Silver tier (automated testing in Gold+)  
**Target Platform**: Windows 10+ (with bash shell via Git Bash or WSL)  
**Project Type**: Multi-component - Python watchers + Node.js MCP server  
**Performance Goals**: Gmail check <2min, WhatsApp check <30s, approval processing <30s  
**Constraints**: Local-only (no cloud sync), approval required for all external actions, API rate limits respected  
**Scale/Scope**: Single user, 50+ emails/day, 20+ WhatsApp messages/day, 1-2 LinkedIn posts/week

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Local-First Privacy**: Gmail OAuth tokens stored locally, WhatsApp session local, no cloud dependencies  
✅ **Human-in-the-Loop**: All external actions (email send, LinkedIn post) require approval  
✅ **Audit-First Operations**: All external actions logged with full details  
✅ **Agent Skills Architecture**: All new Claude functionality as skills  
✅ **Fail-Safe Defaults**: DRY_RUN=true by default, explicit opt-in for real actions  
✅ **Minimal Viable Implementation**: Silver tier only - no Gold features

## Project Structure

### Documentation (this feature)

```text
specs/silver-ai-employee/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Implementation tasks (created by /sp.tasks)
```

### Source Code (repository root)

```text
AI_Employee_Vault/           # Obsidian vault (extended from Bronze)
├── .obsidian/
├── Inbox/
├── Needs_Action/
├── Done/
├── Errors/
├── Logs/
├── Pending_Approval/        # NEW: Approval requests
├── Approved/                # NEW: Approved actions
├── Rejected/                # NEW: Rejected actions
├── Briefings/               # NEW: Daily briefings
├── Business_Updates/        # NEW: LinkedIn post sources
├── Dashboard.md
└── Company_Handbook.md

src/                         # Python source (extended from Bronze)
├── watchers/
│   ├── base_watcher.py      # (existing)
│   ├── file_watcher.py      # (existing)
│   ├── gmail_watcher.py     # NEW: Gmail monitoring
│   ├── whatsapp_watcher.py  # NEW: WhatsApp monitoring
│   └── linkedin_watcher.py  # NEW: LinkedIn post monitoring
├── orchestrators/           # NEW: Action orchestration
│   ├── approval_orchestrator.py  # Approval workflow
│   └── scheduler.py         # Scheduled tasks
├── utils/
│   ├── logger.py            # (existing)
│   ├── vault_manager.py     # (existing - extended)
│   ├── gmail_auth.py        # NEW: Gmail OAuth2
│   └── retry_handler.py     # NEW: Retry logic with backoff
└── main.py                  # (existing - extended)

mcp-servers/                 # NEW: MCP servers
└── email-server/
    ├── package.json
    ├── index.js             # Email MCP server
    └── .env.example

.claude/
└── skills/                  # Agent Skills (extended from Bronze)
    ├── process_action.md    # (existing)
    ├── update_dashboard.md  # (existing)
    ├── move_to_done.md      # (existing)
    ├── check_handbook.md    # (existing)
    ├── process_email.md     # NEW: Process email action items
    ├── process_whatsapp.md  # NEW: Process WhatsApp messages
    ├── draft_linkedin_post.md  # NEW: Draft LinkedIn posts
    ├── approve_action.md    # NEW: Approve pending actions
    ├── generate_briefing.md # NEW: Generate daily briefing
    └── README.md

config/                      # NEW: Configuration
├── gmail_credentials.json   # Gmail OAuth2 credentials (gitignored)
├── gmail_token.json         # Gmail OAuth2 token (gitignored)
└── whatsapp_session/        # WhatsApp session data (gitignored)

tests/
└── manual_test_plan_silver.md  # Silver tier test procedures

.env                         # Extended with new config
requirements.txt             # Extended with new dependencies
README.md                    # Updated for Silver tier
```

**Structure Decision**: Extended Bronze tier structure with new components. Separated orchestrators from watchers for clarity. Added mcp-servers directory for Node.js MCP server. Config directory for sensitive credentials (gitignored).

## Complexity Tracking

No constitution violations. All complexity justified by Silver tier requirements.

## Architecture Overview

### Component Interaction Flow

```
1. GMAIL WATCHER (Python + Gmail API)
   ↓
2. Detects important email → Creates EMAIL_*.md in Needs_Action/
   ↓
3. USER runs Claude /process_email skill
   ↓
4. Claude drafts reply → Creates APPROVAL_EMAIL_*.md in Pending_Approval/
   ↓
5. USER moves to Approved/
   ↓
6. APPROVAL ORCHESTRATOR detects approved file
   ↓
7. Calls EMAIL MCP SERVER (Node.js)
   ↓
8. Email sent → Logged → File moved to Done/

PARALLEL FLOW:

1. WHATSAPP WATCHER (Python + Playwright)
   ↓
2. Detects urgent message → Creates WHATSAPP_*.md in Needs_Action/
   ↓
3. USER runs Claude /process_whatsapp skill
   ↓
4. Claude suggests response → USER handles manually (Silver tier)

SCHEDULED FLOW:

1. SCHEDULER (Python schedule library)
   ↓
2. Triggers at 8:00 AM daily
   ↓
3. Runs /generate_briefing skill
   ↓
4. Briefing saved to Briefings/YYYY-MM-DD_briefing.md
   ↓
5. Dashboard updated with briefing link
```

### Key Design Decisions

**Decision 1: Gmail API vs IMAP**
- **Options Considered**: Gmail API (OAuth2), IMAP (username/password), Email forwarding
- **Trade-offs**: Gmail API requires OAuth setup but is more secure and feature-rich. IMAP is simpler but less secure. Forwarding adds latency.
- **Rationale**: Gmail API chosen for security (OAuth2), reliability (official API), and features (labels, importance flags). Setup complexity is one-time cost.
- **Principle**: Local-First Privacy (tokens stored locally), Audit-First (full API logging)

**Decision 2: WhatsApp Web Automation vs API**
- **Options Considered**: WhatsApp Web (Playwright), WhatsApp Business API (paid), Third-party APIs (unreliable)
- **Trade-offs**: Web automation is fragile (UI changes) but free. Business API is reliable but costs $0.005/message. Third-party violates ToS.
- **Rationale**: WhatsApp Web automation chosen for zero cost and no ToS violations. Fragility mitigated by error handling and session persistence.
- **Principle**: Minimal Viable Implementation (free solution), Fail-Safe Defaults (graceful degradation)

**Decision 3: MCP Server for Email vs Direct SMTP**
- **Options Considered**: MCP server (Node.js), Direct SMTP (Python smtplib), Gmail API send
- **Trade-offs**: MCP server adds complexity but provides Claude Code integration. Direct SMTP is simpler but no Claude integration. Gmail API requires OAuth.
- **Rationale**: MCP server chosen to align with Claude Code ecosystem and enable future MCP integrations. Node.js chosen for MCP SDK support.
- **Principle**: Agent Skills Architecture (MCP enables Claude to send emails)

**Decision 4: Approval Workflow via File Movement**
- **Options Considered**: File movement (mv to /Approved), Database flags, API endpoints
- **Trade-offs**: File movement is simple and auditable but requires polling. Database adds complexity. API requires server.
- **Rationale**: File movement chosen for simplicity, auditability (files are self-documenting), and alignment with Obsidian workflow. Polling overhead is acceptable for Silver tier.
- **Principle**: Human-in-the-Loop (explicit file movement = explicit approval), Audit-First (approval files are permanent record)

**Decision 5: Python schedule vs Cron/Task Scheduler**
- **Options Considered**: Python schedule library, Windows Task Scheduler, Cron (Linux)
- **Trade-offs**: Python schedule is cross-platform and in-process but requires running orchestrator. Task Scheduler is native but Windows-only. Cron is Linux-only.
- **Rationale**: Python schedule chosen for cross-platform support and simplicity (no external configuration). Runs within main orchestrator process.
- **Principle**: Minimal Viable Implementation (no external dependencies)

## Interfaces and API Contracts

### Gmail Watcher → Vault Interface

**Input**: Gmail API message object
**Output**: Markdown file created in `Needs_Action/`

```yaml
# Needs_Action/EMAIL_<message_id>_<timestamp>.md
---
type: email
message_id: 18d4f2a3b5c6d7e8
from: client@example.com
from_name: John Client
to: me@example.com
subject: Urgent: Invoice Payment Question
received: 2026-04-16T10:30:00Z
importance: high
labels: [INBOX, IMPORTANT]
status: pending
---

## Email Details

- **From**: John Client <client@example.com>
- **Subject**: Urgent: Invoice Payment Question
- **Received**: 2026-04-16 10:30:00
- **Importance**: High

## Email Snippet

Hi, I have a question about invoice #1234. When is the payment due?

## Suggested Actions

- [ ] Draft reply based on Company Handbook rules
- [ ] Check invoice #1234 details
- [ ] Respond within 24 hours (client communication rule)
```

### Approval Request → MCP Server Interface

**Input**: Approval file in `/Approved/`
**Output**: MCP server call + result log

```yaml
# Approved/APPROVAL_EMAIL_send_reply_<timestamp>.md
---
type: approval_request
action: send_email
approved_at: 2026-04-16T10:45:00Z
status: approved
---

## Action Details

**Action**: Send Email
**To**: client@example.com
**Subject**: Re: Urgent: Invoice Payment Question
**Body**:

Hi John,

Thank you for your question. Invoice #1234 is due on April 30, 2026.
Payment terms are Net 30 from invoice date (March 31).

Please let me know if you have any other questions.

Best regards

## Approval

Approved by: User
Approved at: 2026-04-16 10:45:00
```

**MCP Server Call**:
```javascript
// Email MCP server receives:
{
  action: "send_email",
  to: "client@example.com",
  subject: "Re: Urgent: Invoice Payment Question",
  body: "Hi John,\n\nThank you for your question...",
  reply_to_message_id: "18d4f2a3b5c6d7e8"
}

// Returns:
{
  success: true,
  message_id: "18d4f2a3b5c6d7e9",
  timestamp: "2026-04-16T10:45:15Z"
}
```

### Daily Briefing Output

```markdown
# Daily Briefing - 2026-04-16

**Generated**: 2026-04-16 08:00:00

## Executive Summary

Good morning! You have 5 pending actions and 3 items completed yesterday.

## Pending Actions (5)

### High Priority (2)
1. **Email**: Client question about invoice #1234 (received 10:30 AM yesterday)
2. **WhatsApp**: Urgent payment request from Supplier A (received 4:30 PM yesterday)

### Medium Priority (3)
3. **File**: Contract review needed (detected 2 days ago)
4. **Email**: Meeting request from Partner B
5. **LinkedIn**: Draft post about new product launch

## Recent Activity (Last 24 Hours)

- ✅ Sent 3 emails (all approved)
- ✅ Processed 8 files
- ✅ Published 1 LinkedIn post
- ⚠️ 2 WhatsApp messages flagged as urgent

## Focus Areas for Today

1. **Respond to client invoice question** (overdue by 2 hours per 24-hour rule)
2. **Handle urgent payment request** (financial matter - high priority)
3. **Review and approve LinkedIn post draft** (scheduled for today)

## System Health

- Gmail watcher: ✅ Active (last check: 07:58 AM)
- WhatsApp watcher: ✅ Active (last check: 07:59 AM)
- Approval orchestrator: ✅ Active
- Pending approvals: 1

---
*Generated by Personal AI Employee (Silver Tier)*
```

## Non-Functional Requirements (NFRs)

### Performance
- **Gmail Check**: < 2 minutes from email arrival to action item creation
- **WhatsApp Check**: < 30 seconds from message to action item creation
- **Approval Processing**: < 30 seconds from approval to action execution
- **MCP Server Response**: < 5 seconds for email send operation
- **Briefing Generation**: < 10 seconds for daily briefing

### Reliability
- **Uptime**: Watchers run continuously for 24+ hours without crash
- **Error Recovery**: Watchers continue after individual message processing errors
- **API Rate Limits**: Exponential backoff with max 5 retries
- **Session Persistence**: WhatsApp session survives orchestrator restarts

### Security
- **Gmail OAuth**: Tokens stored in config/ (gitignored), refreshed automatically
- **WhatsApp Session**: Session data in config/ (gitignored), encrypted at rest
- **MCP Server**: Email credentials in .env (gitignored), no plaintext passwords
- **Approval Audit**: All approvals logged with timestamp and user

### Usability
- **Setup Time**: < 2 hours from Bronze tier to working Silver tier
- **Documentation**: Step-by-step OAuth setup, WhatsApp session creation
- **Error Messages**: Clear instructions when authentication fails

## Data Management

### Source of Truth
- **Vault State**: Obsidian vault folder structure is authoritative
- **Gmail State**: Gmail API is source of truth for emails (no local cache)
- **WhatsApp State**: WhatsApp Web is source of truth (no local storage)
- **Approval State**: File location (/Pending_Approval, /Approved, /Rejected) is authoritative

### Schema Evolution
- Markdown frontmatter is extensible (add fields without breaking)
- Version field in frontmatter for future compatibility
- MCP server API versioned (v1)

### Data Retention
- **Logs**: Retain for 90 days minimum (constitution requirement)
- **Approved Actions**: Retain indefinitely (audit trail)
- **Rejected Actions**: Retain for 30 days (review period)
- **Briefings**: Retain for 90 days (historical reference)

## Operational Readiness

### Observability
- **Logs**: All watcher events, API calls, MCP calls logged with timestamps
- **Dashboard**: Visual status shows watcher health, pending approvals count
- **Metrics**: Email count, WhatsApp count, approval count visible in Dashboard

### Deployment
- **Installation**: pip install (Python deps) + npm install (MCP server)
- **Startup**: Single command starts all watchers + orchestrators + MCP server
- **Configuration**: .env file for all settings, OAuth setup wizard

### Runbooks
- **Start System**: `python src/main.py` (starts all components)
- **Stop System**: Ctrl+C (graceful shutdown of all components)
- **Gmail OAuth Setup**: `python src/utils/gmail_auth.py --setup`
- **WhatsApp Session**: `python src/watchers/whatsapp_watcher.py --setup`
- **Check Logs**: Open `Logs/YYYY-MM-DD.log`
- **Process Approvals**: Move files from /Pending_Approval to /Approved

## Risk Analysis and Mitigation

### Risk 1: Gmail API Rate Limits
- **Likelihood**: Medium (100 requests/100 seconds quota)
- **Impact**: High (emails not detected)
- **Mitigation**: Check every 2 minutes (30 requests/hour), exponential backoff on 429 errors
- **Blast Radius**: Single user, temporary
- **Kill Switch**: Disable Gmail watcher in .env

### Risk 2: WhatsApp Session Expiration
- **Likelihood**: High (sessions expire after inactivity)
- **Impact**: Medium (messages not detected until re-auth)
- **Mitigation**: Session persistence, automatic re-auth prompt, graceful degradation
- **Blast Radius**: WhatsApp only, other watchers continue
- **Kill Switch**: Disable WhatsApp watcher in .env

### Risk 3: Accidental Email Send
- **Likelihood**: Low (approval workflow required)
- **Impact**: High (embarrassing or damaging email sent)
- **Mitigation**: Approval workflow (file must be in /Approved), DRY_RUN mode for testing, email preview in approval request
- **Blast Radius**: Single email
- **Kill Switch**: DRY_RUN=true in .env

### Risk 4: MCP Server Crash
- **Likelihood**: Medium (Node.js process can crash)
- **Impact**: High (emails cannot be sent)
- **Mitigation**: Process monitoring, automatic restart, queue approved actions for retry
- **Blast Radius**: Email sending only, other functions continue
- **Kill Switch**: Manual restart of MCP server

## Evaluation and Validation

### Definition of Done
- [ ] Gmail watcher detects important emails within 2 minutes
- [ ] WhatsApp watcher detects urgent messages within 30 seconds
- [ ] Approval workflow prevents email send without approval
- [ ] MCP server successfully sends emails
- [ ] Daily briefing generates at scheduled time
- [ ] All operations logged to Logs/
- [ ] README updated with Silver tier setup instructions
- [ ] Manual test plan executed successfully

### Output Validation
- **Format**: All .md files have valid YAML frontmatter
- **Requirements**: All FR-001 through FR-012 met
- **Safety**: Approval workflow enforced, no external actions without approval

## Next Steps

1. Run `/sp.tasks` to generate implementation tasks from this plan
2. Implement tasks in order (setup → watchers → MCP → orchestrators → skills)
3. Manual testing against Silver tier acceptance criteria
4. Document lessons learned for Gold tier planning
