# Implementation Plan: Gold Tier Autonomous AI Employee

**Branch**: `001-gold-tier` | **Date**: 2026-04-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-gold-tier/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Transform the Silver tier Personal AI Employee into a fully autonomous Gold tier system capable of end-to-end multi-step task completion without human intervention between steps. Key capabilities include: Ralph Wiggum loop for autonomous operation, Odoo accounting integration via MCP server, multi-platform social media automation (Facebook, Instagram, Twitter), weekly business and accounting audits with CEO briefing generation, and comprehensive error recovery with graceful degradation. The system must maintain all Bronze and Silver tier functionality while adding autonomous decision-making, cross-system integration, and proactive business intelligence.

## Technical Context

**Language/Version**: Python 3.13+ (established in Bronze/Silver tiers)  
**Primary Dependencies**: 
- Core: watchdog, schedule, python-dotenv (from Bronze/Silver)
- Email: google-api-python-client, google-auth-oauthlib (from Silver)
- Social: playwright (from Silver), facebook-sdk, instagrapi, tweepy (new for Gold)
- Accounting: odoorpc (new for Gold)
- MCP: Node.js 24+ with @modelcontextprotocol/sdk (from Silver, expanded for Gold)
- Error handling: tenacity for retry logic (new for Gold)

**Storage**: 
- Primary: Obsidian vault (markdown files in AI_Employee_Vault/)
- External: Odoo Community Edition v19+ database (JSON-RPC API)
- Logs: JSON files in Logs/ with 90-day retention

**Testing**: pytest for unit and integration tests, manual testing for MCP servers and external integrations

**Target Platform**: Windows 10+ (local machine), designed for 24/7 operation with process management (PM2 or supervisord)

**Project Type**: Single Python project with multiple orchestrators, watchers, and Node.js MCP servers

**Performance Goals**: 
- Handle 50+ tasks per day across all domains
- Odoo sync latency <5 minutes
- Social media post publishing <5 minutes after approval
- Weekly audit generation <10 minutes
- System uptime 99%+ with automatic recovery

**Constraints**: 
- Must maintain all Bronze and Silver tier functionality
- Zero data loss during error scenarios (all operations queued and retried)
- Human approval required for all external actions (emails, posts, payments)
- All actions must be logged with complete audit trail
- Ralph Wiggum loop max 10 iterations per task
- Rate limits: 10 emails/hour, 3 payments/day, social media per platform API limits

**Scale/Scope**: 
- Single business owner user
- 3 social media platforms (Facebook, Instagram, Twitter)
- 1 accounting system (Odoo)
- 5+ MCP servers (email, Odoo, Facebook, Instagram, Twitter)
- 10+ Agent Skills
- Autonomous 24/7 operation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Local-First Privacy ✅ PASS
- **Requirement**: All sensitive data remains on local machine
- **Implementation**: Odoo credentials stored in .env (local), social media tokens in .env (local), WhatsApp session local, all vault data local
- **Compliance**: No automatic cloud sync, all external API calls use local credentials

### II. Human-in-the-Loop (HITL) for Critical Actions ✅ PASS
- **Requirement**: Irreversible/financial/external actions require approval
- **Implementation**: 
  - All social media posts require approval (FR-018)
  - All payments require approval (inherited from Silver)
  - All emails require approval (inherited from Silver)
  - Approval workflow via Pending_Approval/ → Approved/ folders
  - Approval expiration after 24 hours (moves to Rejected/)
- **Compliance**: Ralph Wiggum loop pauses at approval gates, resumes after approval granted

### III. Audit-First Operations ✅ PASS
- **Requirement**: Every action logged with full details
- **Implementation**: 
  - FR-030: JSON logs with timestamp, action_type, actor, target, parameters, approval_status, result
  - FR-031: Logs stored in Logs/YYYY-MM-DD.json with 90-day retention
  - All errors logged (FR-026, FR-027)
  - Watchdog logs component crashes (FR-032)
- **Compliance**: No silent failures, all operations traceable

### IV. Agent Skills Architecture ✅ PASS
- **Requirement**: All AI functionality as Agent Skills
- **Implementation**: 
  - FR-038: All Gold tier functionality as documented Agent Skills
  - FR-039: Each skill includes name, description, triggers, inputs, outputs, error handling
  - FR-040: New skills for process_odoo_invoice, post_social_media, generate_weekly_audit, handle_error_recovery
  - Inherits 9 Bronze/Silver skills, adds 4+ Gold skills
- **Compliance**: No inline prompts, all functionality via .claude/skills/

### V. Fail-Safe Defaults ✅ PASS
- **Requirement**: DRY_RUN=true default, rate limiting enforced
- **Implementation**: 
  - DRY_RUN environment variable required for real actions
  - Rate limits: 10 emails/hour (inherited), 3 payments/day (inherited)
  - Social media rate limits per platform API (FR-014)
  - Ralph Wiggum loop max 10 iterations (FR-001)
- **Compliance**: Safe defaults, explicit opt-in for real actions

### VI. Minimal Viable Implementation ⚠️ JUSTIFIED EXPANSION
- **Requirement**: Smallest working system, no premature optimization
- **Justification**: Gold tier is the defined scope from hackathon requirements
  - Ralph Wiggum loop: Required for autonomous operation (core Gold tier feature)
  - Odoo integration: Required for accounting automation (Gold tier requirement)
  - Social media: Required for business growth automation (Gold tier requirement)
  - Weekly audit: Required for CEO briefing (Gold tier requirement)
  - Error recovery: Required for 24/7 autonomous operation (Gold tier requirement)
- **Compliance**: Building exactly to Gold tier spec, no features beyond requirements

### Post-Design Re-Check
*To be completed after Phase 1 design artifacts are generated*

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

## Project Structure

### Documentation (this feature)

```text
specs/001-gold-tier/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── odoo-mcp.json       # Odoo MCP server contract
│   ├── facebook-mcp.json   # Facebook MCP server contract
│   ├── instagram-mcp.json  # Instagram MCP server contract
│   └── twitter-mcp.json    # Twitter MCP server contract
├── checklists/
│   └── requirements.md  # Spec quality checklist (already created)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Single Python project with orchestrators, watchers, and MCP servers

src/
├── watchers/                    # Monitoring components (Bronze/Silver + Gold)
│   ├── __init__.py
│   ├── base_watcher.py         # Base class (existing)
│   ├── file_watcher.py         # Bronze tier (existing)
│   ├── gmail_watcher.py        # Silver tier (existing)
│   ├── whatsapp_watcher.py     # Silver tier (existing)
│   └── linkedin_watcher.py     # Silver tier (existing)
│
├── orchestrators/               # Coordination components (Silver + Gold)
│   ├── __init__.py
│   ├── approval_orchestrator.py    # Silver tier (existing)
│   ├── scheduler.py                # Silver tier (existing)
│   ├── ralph_wiggum.py             # Gold tier (NEW) - Autonomous loop
│   └── audit_orchestrator.py       # Gold tier (NEW) - Weekly audits
│
├── integrations/                # External system integrations (Gold - NEW)
│   ├── __init__.py
│   ├── odoo_client.py          # Odoo JSON-RPC client
│   ├── facebook_client.py      # Facebook Graph API client
│   ├── instagram_client.py     # Instagram Graph API client
│   └── twitter_client.py       # Twitter API v2 client
│
├── utils/                       # Shared utilities (Bronze/Silver + Gold)
│   ├── __init__.py
│   ├── gmail_auth.py           # Silver tier (existing)
│   ├── retry_handler.py        # Silver tier (existing)
│   ├── error_recovery.py       # Gold tier (NEW) - Error handling
│   └── watchdog.py             # Gold tier (NEW) - Process monitoring
│
└── main.py                      # Main entry point (updated for Gold)

mcp-servers/                     # MCP server implementations (Silver + Gold)
├── email-server/               # Silver tier (existing)
│   ├── index.js
│   ├── package.json
│   └── .env.example
│
├── odoo-server/                # Gold tier (NEW)
│   ├── index.js
│   ├── package.json
│   └── .env.example
│
├── facebook-server/            # Gold tier (NEW)
│   ├── index.js
│   ├── package.json
│   └── .env.example
│
├── instagram-server/           # Gold tier (NEW)
│   ├── index.js
│   ├── package.json
│   └── .env.example
│
└── twitter-server/             # Gold tier (NEW)
    ├── index.js
    ├── package.json
    └── .env.example

.claude/
└── skills/                      # Agent Skills (Bronze/Silver + Gold)
    ├── README.md
    ├── process_action.md       # Bronze (existing)
    ├── update_dashboard.md     # Bronze (existing)
    ├── move_to_done.md         # Bronze (existing)
    ├── check_handbook.md       # Bronze (existing)
    ├── process_email.md        # Silver (existing)
    ├── process_whatsapp.md     # Silver (existing)
    ├── draft_linkedin_post.md  # Silver (existing)
    ├── approve_action.md       # Silver (existing)
    ├── generate_briefing.md    # Silver (existing)
    ├── process_odoo_invoice.md # Gold (NEW)
    ├── post_social_media.md    # Gold (NEW)
    ├── generate_weekly_audit.md # Gold (NEW)
    └── handle_error_recovery.md # Gold (NEW)

AI_Employee_Vault/               # Obsidian vault (Bronze/Silver + Gold)
├── Dashboard.md
├── Company_Handbook.md
├── Inbox/
├── Needs_Action/
├── Done/
├── Errors/
├── Logs/
├── Pending_Approval/
├── Approved/
├── Rejected/
├── Briefings/                  # Silver/Gold
├── Business_Updates/           # Silver/Gold
├── Accounting/                 # Gold (NEW) - Odoo sync data
│   ├── Invoices/
│   ├── Payments/
│   └── Reports/
└── Social_Media/               # Gold (NEW) - Post tracking
    ├── Drafts/
    ├── Published/
    └── Analytics/

tests/
├── unit/
│   ├── test_ralph_wiggum.py
│   ├── test_odoo_client.py
│   ├── test_social_clients.py
│   └── test_error_recovery.py
├── integration/
│   ├── test_odoo_integration.py
│   ├── test_social_integration.py
│   └── test_audit_workflow.py
└── contract/
    ├── test_odoo_mcp.py
    ├── test_facebook_mcp.py
    ├── test_instagram_mcp.py
    └── test_twitter_mcp.py

config/                          # Configuration files
├── gmail_credentials.json      # Silver (existing)
├── odoo_config.json           # Gold (NEW)
└── social_media_config.json   # Gold (NEW)

.env.example                     # Environment variables template
requirements.txt                 # Python dependencies
```

**Structure Decision**: Single Python project structure maintained from Bronze/Silver tiers. Gold tier adds new modules (integrations/, expanded orchestrators/) and MCP servers (odoo, facebook, instagram, twitter) while preserving all existing Bronze/Silver functionality. The vault structure expands with Accounting/ and Social_Media/ folders for Gold tier data. All components follow the established pattern: watchers detect changes, orchestrators coordinate actions, MCP servers execute external operations, Agent Skills provide Claude Code interface.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Minimal Viable Implementation (expanded scope) | Gold tier is the defined hackathon requirement with 12 specific features: Ralph Wiggum loop, Odoo integration, 3 social platforms, weekly audit, error recovery, 5+ MCP servers | Bronze/Silver tiers already complete; Gold tier is the next defined milestone in the hackathon progression; building less would not meet Gold tier requirements |

**Justification**: This is not premature optimization or feature creep - it's building exactly to the Gold tier specification from the hackathon document. Each component (autonomous loop, Odoo, social media, audits, error recovery) is a required Gold tier feature with clear acceptance criteria and measurable success metrics.

---

## Key Architectural Decisions

### Decision 1: Ralph Wiggum Loop with File-Based Completion Detection

**Context**: Need autonomous multi-step task completion without manual intervention between steps.

**Decision**: Implement custom Ralph Wiggum loop that monitors task file location (Needs_Action/ → Done/) rather than relying solely on promise tags.

**Rationale**:
- File movement is natural part of existing Bronze/Silver workflow
- More reliable than AI remembering to output promise tags
- Completion is verifiable by filesystem state
- Supports state persistence across system restarts
- Integrates seamlessly with existing approval workflow

**Alternatives Considered**:
- Promise-based only: Rejected due to reliability concerns (AI must remember tags)
- External orchestration tool: Rejected to maintain local-first architecture
- Using /loop skill: Rejected because it's for recurring tasks, not multi-step completion

**Trade-offs**:
- Pro: Reliable, verifiable, integrates with existing patterns
- Pro: No changes to Agent Skills (they already move files)
- Con: Requires filesystem monitoring overhead
- Con: Max 10 iterations limit (acceptable for defined scope)

**Implementation Impact**:
- New module: src/orchestrators/ralph_wiggum.py
- Monitors Needs_Action/ folder
- Executes Claude Code with task context
- Checks Done/ folder for completion
- Re-injects prompt if incomplete (max 10 iterations)

---

### Decision 2: Separate MCP Server Per Integration

**Context**: Need to integrate with 5 external systems (email, Odoo, Facebook, Instagram, Twitter).

**Decision**: Implement separate Node.js MCP server for each integration rather than single monolithic server.

**Rationale**:
- Independent failure: One server crash doesn't affect others
- Clear separation of concerns: Each server handles one integration
- Easier testing and debugging: Test each integration independently
- Follows established Silver tier pattern (email-server)
- Allows different authentication methods per platform

**Alternatives Considered**:
- Single monolithic MCP server: Rejected due to cascading failure risk
- Python MCP servers: Rejected because Node.js has better MCP SDK support
- Direct API calls from Python: Rejected because MCP provides Claude Code integration

**Trade-offs**:
- Pro: Fault isolation, independent scaling, easier maintenance
- Pro: Each server can be developed/tested independently
- Con: More processes to manage (5 servers vs 1)
- Con: More configuration overhead (5 .env files)

**Implementation Impact**:
- 5 MCP servers: email, odoo, facebook, instagram, twitter
- Each in mcp-servers/{name}-server/
- Standard structure: index.js, package.json, .env.example
- Configure in Claude Code mcp.json

---

### Decision 3: Odoo Integration via odoorpc Library

**Context**: Need to integrate with Odoo Community Edition for accounting automation.

**Decision**: Use odoorpc Python library with custom MCP server for Claude Code integration.

**Rationale**:
- odoorpc provides clean abstraction over Odoo's JSON-RPC API
- Handles authentication, session management, API versioning
- Well-maintained library with good documentation
- MCP server pattern established in Silver tier
- Supports all required operations (invoices, payments, reports)

**Alternatives Considered**:
- Direct XML-RPC calls: Rejected because odoorpc provides better abstraction
- Odoo Python API (internal): Rejected because requires Odoo on same machine
- REST API: Rejected because Odoo's REST API less mature than JSON-RPC

**Trade-offs**:
- Pro: Clean API, handles auth/sessions, well-documented
- Pro: Supports all required Odoo operations
- Con: Additional dependency (odoorpc)
- Con: Requires Odoo v19+ (acceptable constraint)

**Implementation Impact**:
- Python client: src/integrations/odoo_client.py
- MCP server: mcp-servers/odoo-server/index.js
- Operations: create_invoice, record_payment, query_financials, sync_transactions

---

### Decision 4: Platform-Specific Social Media Clients

**Context**: Need to post to Facebook, Instagram, and Twitter with different requirements per platform.

**Decision**: Implement separate Python client for each platform using official SDKs, with separate MCP servers.

**Rationale**:
- Each platform has unique API requirements and constraints
- Official SDKs handle authentication, rate limiting, API changes
- Separate clients allow platform-specific error handling
- Content adaptation happens in Agent Skills (platform-aware)
- Independent failure: One platform down doesn't affect others

**Alternatives Considered**:
- Single unified social media client: Rejected due to different APIs/requirements
- Direct API calls without SDKs: Rejected because SDKs handle auth/retries
- Third-party aggregators (Buffer, Hootsuite): Rejected for local-first architecture

**Trade-offs**:
- Pro: Platform-specific optimization, independent failure handling
- Pro: Official SDKs stay updated with API changes
- Con: More code to maintain (3 clients vs 1)
- Con: Different authentication flows per platform

**Implementation Impact**:
- Python clients: src/integrations/{facebook,instagram,twitter}_client.py
- MCP servers: mcp-servers/{facebook,instagram,twitter}-server/
- Libraries: facebook-sdk, instagrapi, tweepy
- Content adaptation in Agent Skills

---

### Decision 5: Comprehensive Error Recovery with Exponential Backoff

**Context**: 24/7 autonomous operation requires resilience to transient failures.

**Decision**: Implement error classification (transient vs permanent) with exponential backoff retry and operation queuing.

**Rationale**:
- Transient errors (network, rate limits) should retry automatically
- Permanent errors (auth, invalid data) should escalate to human
- Exponential backoff prevents API hammering during outages
- Operation queuing ensures zero data loss
- Watchdog monitors and restarts crashed components

**Alternatives Considered**:
- Simple try/catch: Rejected because doesn't distinguish error types
- External monitoring service: Rejected for local-first architecture
- Manual intervention for all errors: Rejected because defeats autonomous operation

**Trade-offs**:
- Pro: Automatic recovery from 95% of transient errors
- Pro: Zero data loss (operations queued and retried)
- Pro: Component isolation prevents cascading failures
- Con: Increased complexity in error handling logic
- Con: Retry delays can accumulate (acceptable for reliability)

**Implementation Impact**:
- Error classification: Transient (retry) vs Permanent (escalate)
- Retry logic: 1s, 2s, 4s, 8s, 16s (max 5 attempts)
- Operation queuing: Failed operations stored locally
- Watchdog: src/utils/watchdog.py monitors PIDs, restarts on crash
- Alert files: Created in Needs_Action/ for auth failures

---

### Decision 6: Weekly Audit with Multi-Source Aggregation

**Context**: Need to generate comprehensive CEO briefing from multiple data sources.

**Decision**: Implement scheduled orchestrator that aggregates data from Odoo, vault, and social media platforms.

**Rationale**:
- Extends existing Silver tier scheduler pattern
- Separate orchestrator for audit-specific logic
- Aggregates data from multiple sources into single briefing
- Generates actionable insights (bottlenecks, cost optimization)
- Scheduled Sunday 11:00 PM, delivers Monday 7:00 AM

**Alternatives Considered**:
- Manual trigger only: Rejected because weekly automation is Gold tier requirement
- Real-time dashboard: Rejected because CEO briefing is specific weekly deliverable
- External BI tool: Rejected for local-first architecture

**Trade-offs**:
- Pro: Proactive business intelligence, actionable insights
- Pro: Consistent weekly cadence, automated delivery
- Con: Requires data from multiple sources (complexity)
- Con: Audit generation takes ~10 minutes (acceptable)

**Implementation Impact**:
- New module: src/orchestrators/audit_orchestrator.py
- Queries: Odoo (financials), vault (tasks), social media (engagement)
- Analysis: Bottlenecks, cost optimization, recommendations
- Output: Briefings/YYYY-MM-DD_weekly_briefing.md
- Dashboard update with briefing link

---

## Phase 0 Completion: Research

✅ **Status**: Complete  
✅ **Artifact**: [research.md](research.md)  
✅ **Decisions**: 6 technical decisions documented with rationale

All NEEDS CLARIFICATION items resolved through research.

---

## Phase 1 Completion: Design & Contracts

✅ **Status**: Complete  
✅ **Artifacts**:
- [data-model.md](data-model.md) - 7 entities with relationships and validation rules
- [contracts/odoo-mcp.json](contracts/odoo-mcp.json) - Odoo MCP server contract
- [contracts/facebook-mcp.json](contracts/facebook-mcp.json) - Facebook MCP server contract
- [contracts/instagram-mcp.json](contracts/instagram-mcp.json) - Instagram MCP server contract
- [contracts/twitter-mcp.json](contracts/twitter-mcp.json) - Twitter MCP server contract
- [quickstart.md](quickstart.md) - Setup and usage guide

✅ **Agent Context**: Updated CLAUDE.md with Gold tier technologies

---

## Post-Design Constitution Re-Check

### I. Local-First Privacy ✅ PASS
- All design artifacts maintain local-first architecture
- Credentials in .env (local), vault data local, no cloud sync
- External APIs called with local credentials only

### II. Human-in-the-Loop (HITL) ✅ PASS
- All MCP contracts include approval workflow
- Social media posts require approval before publishing
- Payments require approval (inherited from Silver)
- Ralph Wiggum loop pauses at approval gates

### III. Audit-First Operations ✅ PASS
- All operations logged in data model (Error Log entity)
- MCP contracts specify error handling and logging
- Watchdog logs component crashes
- 90-day log retention in design

### IV. Agent Skills Architecture ✅ PASS
- Quickstart guide references Agent Skills for all operations
- No inline prompts in design
- Skills: process_odoo_invoice, post_social_media, generate_weekly_audit, handle_error_recovery

### V. Fail-Safe Defaults ✅ PASS
- Quickstart guide specifies DRY_RUN=true default
- Rate limits documented in MCP contracts
- Ralph Wiggum max 10 iterations in design

### VI. Minimal Viable Implementation ✅ PASS
- Design covers exactly Gold tier requirements, no extra features
- All components justified in Complexity Tracking section
- No premature optimization in design

**Final Verdict**: All constitution checks PASS. Design is ready for implementation.

---

## Next Steps

1. ✅ **Phase 0**: Research complete
2. ✅ **Phase 1**: Design and contracts complete
3. ⏭️ **Phase 2**: Generate tasks.md with `/sp.tasks` command
4. ⏭️ **Phase 3**: Implement tasks with `/sp.implement` command

---

**Planning Status**: ✅ COMPLETE  
**Ready for**: `/sp.tasks` to generate implementation tasks  
**Branch**: 001-gold-tier  
**Date**: 2026-04-16
