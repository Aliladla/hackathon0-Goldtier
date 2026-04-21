# Research: Gold Tier Autonomous AI Employee

**Feature**: 001-gold-tier  
**Date**: 2026-04-16  
**Purpose**: Document technical research and decisions for Gold tier implementation

## Phase 0: Technical Research and Decisions

### 1. Ralph Wiggum Loop Implementation

**Decision**: Implement custom Ralph Wiggum loop based on Anthropic reference implementation

**Research Findings**:
- Reference implementation: github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum
- Two completion strategies available:
  1. Promise-based: AI outputs `<promise>TASK_COMPLETE</promise>` tag
  2. File movement: Detect when task file moves to Done/ folder
- File movement strategy is more reliable for our use case (natural part of workflow)

**Rationale**:
- File movement integrates naturally with existing Bronze/Silver workflow
- No need for AI to remember to output promise tags
- Completion is verifiable by checking filesystem state
- Supports state persistence across restarts

**Alternatives Considered**:
- Using existing /loop skill: Rejected because it's for recurring tasks, not multi-step task completion
- Promise-based only: Rejected because it requires AI to remember to output tags, less reliable
- External orchestration tool: Rejected to maintain local-first architecture

**Implementation Approach**:
- Create src/orchestrators/ralph_wiggum.py
- Monitor task files in Needs_Action/
- Execute Claude Code with task context
- Check for completion (file in Done/)
- Re-inject prompt if incomplete (max 10 iterations)
- Log all iterations and completion status

---

### 2. Odoo Integration Architecture

**Decision**: Use odoorpc Python library with custom MCP server for Claude Code integration

**Research Findings**:
- Odoo Community Edition v19+ supports JSON-RPC API
- Official documentation: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html
- Python library odoorpc provides clean interface to JSON-RPC
- MCP server pattern established in Silver tier (email-server)

**Rationale**:
- odoorpc handles authentication, session management, and API versioning
- MCP server provides Claude Code integration following established pattern
- JSON-RPC is official Odoo API (stable, well-documented)
- Supports all required operations: create invoices, record payments, query reports

**Alternatives Considered**:
- Direct XML-RPC calls: Rejected because odoorpc provides better abstraction
- Odoo Python API (internal): Rejected because requires Odoo installation on same machine
- REST API: Rejected because Odoo's REST API is less mature than JSON-RPC

**Implementation Approach**:
- Python client: src/integrations/odoo_client.py using odoorpc
- MCP server: mcp-servers/odoo-server/index.js exposing tools for Claude Code
- Operations: create_invoice, record_payment, query_financials, sync_transactions
- Error handling: Retry transient errors, queue operations during downtime

---

### 3. Social Media Integration Strategy

**Decision**: Use official platform SDKs with platform-specific MCP servers

**Research Findings**:
- **Facebook**: Graph API v18+ with facebook-sdk Python library
  - Requires pages_manage_posts permission
  - Supports text, images, links
  - Rate limit: 200 calls/hour per user
  
- **Instagram**: Graph API (Instagram Basic Display + Content Publishing)
  - Requires instagram_basic and instagram_content_publish permissions
  - Supports images with captions (max 2200 chars)
  - Must be Instagram Business Account
  - Rate limit: 200 calls/hour per user
  
- **Twitter**: API v2 with tweepy Python library
  - Requires tweet.read and tweet.write permissions
  - Supports text (280 chars), images, threads
  - Rate limit: 300 tweets per 3 hours

**Rationale**:
- Official SDKs provide stable, maintained interfaces
- Each platform has unique requirements (permissions, formats, limits)
- Separate MCP servers allow independent failure handling
- Platform-specific clients handle authentication and rate limiting

**Alternatives Considered**:
- Single unified social media MCP: Rejected because platforms have different APIs and requirements
- Direct API calls without SDKs: Rejected because SDKs handle auth, retries, and API changes
- Third-party aggregators (Buffer, Hootsuite): Rejected to maintain local-first architecture

**Implementation Approach**:
- Python clients: src/integrations/{facebook,instagram,twitter}_client.py
- MCP servers: mcp-servers/{facebook,instagram,twitter}-server/index.js
- Content adaptation: Platform-specific formatting in Agent Skills
- Rate limiting: Track calls per platform, queue when limits approached

---

### 4. Weekly Audit Architecture

**Decision**: Scheduled orchestrator with multi-source data aggregation

**Research Findings**:
- Silver tier scheduler already uses Python schedule library
- Audit requires data from: Odoo (financials), vault (tasks), social media (engagement)
- CEO briefing format established in hackathon document
- Audit should run Sunday 11:00 PM, deliver by Monday 7:00 AM

**Rationale**:
- Extend existing scheduler pattern from Silver tier
- Separate orchestrator (audit_orchestrator.py) for audit-specific logic
- Aggregates data from multiple sources into single briefing
- Generates actionable insights (bottlenecks, cost optimization, recommendations)

**Alternatives Considered**:
- Manual trigger only: Rejected because weekly automation is Gold tier requirement
- Real-time dashboard: Rejected because CEO briefing is specific weekly deliverable
- External BI tool: Rejected to maintain local-first architecture

**Implementation Approach**:
- Create src/orchestrators/audit_orchestrator.py
- Query Odoo for weekly financials (revenue, expenses, overdue invoices)
- Analyze vault Done/ folder for task metrics (completion rate, bottlenecks)
- Collect social media engagement from platform APIs
- Identify cost optimizations (unused subscriptions, cost increases)
- Generate briefing in Briefings/YYYY-MM-DD_weekly_briefing.md
- Update Dashboard.md with briefing link and highlights

---

### 5. Error Recovery and Graceful Degradation

**Decision**: Implement comprehensive error handling with exponential backoff and component isolation

**Research Findings**:
- Transient errors (network timeouts, rate limits) should retry
- Permanent errors (auth failures, invalid data) should escalate
- Python tenacity library provides robust retry decorators
- Watchdog pattern monitors and restarts crashed components

**Rationale**:
- 24/7 autonomous operation requires resilience to transient failures
- Component isolation prevents cascading failures
- Exponential backoff prevents API hammering during outages
- Graceful degradation maintains read operations when write operations fail

**Alternatives Considered**:
- Simple try/catch: Rejected because doesn't handle transient vs permanent errors
- External monitoring service: Rejected to maintain local-first architecture
- Manual intervention for all errors: Rejected because defeats autonomous operation goal

**Implementation Approach**:
- Error classification: Transient (retry) vs Permanent (escalate)
- Retry logic: Exponential backoff 1s, 2s, 4s, 8s, 16s (max 5 attempts)
- Operation queuing: Failed operations stored locally, retried when service restored
- Watchdog: src/utils/watchdog.py monitors component PIDs, restarts on crash
- Alert files: Create in Needs_Action/ for auth failures requiring human intervention
- Graceful degradation: Continue read operations, queue write operations, alert user

---

### 6. MCP Server Architecture

**Decision**: Separate MCP server per external integration (5 total: email, Odoo, Facebook, Instagram, Twitter)

**Research Findings**:
- MCP (Model Context Protocol) is Anthropic's standard for Claude Code integrations
- Silver tier established pattern with email-server
- Each server exposes tools that Claude Code can invoke
- Servers run as separate Node.js processes

**Rationale**:
- Independent failure: One server crash doesn't affect others
- Clear separation of concerns: Each server handles one integration
- Easier testing and debugging: Test each integration independently
- Follows established Silver tier pattern

**Alternatives Considered**:
- Single monolithic MCP server: Rejected because failure affects all integrations
- Python MCP servers: Rejected because Node.js ecosystem has better MCP tooling
- Direct API calls from Python: Rejected because MCP provides Claude Code integration

**Implementation Approach**:
- Each server in mcp-servers/{name}-server/
- Standard structure: index.js, package.json, .env.example
- Expose tools via @modelcontextprotocol/sdk
- Configure in Claude Code settings (mcp.json)
- Health checks and error reporting

---

## Technology Stack Summary

### Python Dependencies (requirements.txt)
```
# Core (Bronze/Silver)
watchdog>=3.0.0
schedule>=1.2.0
python-dotenv>=1.0.0

# Email (Silver)
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.1.0

# Social Media (Gold)
playwright>=1.40.0
facebook-sdk>=3.1.0
instagrapi>=2.0.0
tweepy>=4.14.0

# Accounting (Gold)
odoorpc>=0.9.0

# Error Handling (Gold)
tenacity>=8.2.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

### Node.js Dependencies (each MCP server)
```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0",
    "dotenv": "^16.0.0"
  }
}
```

### External Services
- Odoo Community Edition v19+
- Facebook Graph API v18+
- Instagram Graph API
- Twitter API v2
- Gmail API (Silver tier)

---

## Risk Assessment

### High Risk
1. **Social media API changes**: Platforms frequently update APIs
   - Mitigation: Use official SDKs, monitor deprecation notices, version pin dependencies

2. **Odoo connectivity**: Network issues or Odoo downtime
   - Mitigation: Queue operations locally, retry with exponential backoff, never lose data

3. **Ralph Wiggum loop infinite loops**: Task never completes
   - Mitigation: Max 10 iterations, log incomplete state, escalate to human

### Medium Risk
1. **Rate limiting**: Exceeding platform API limits
   - Mitigation: Track calls per platform, queue when approaching limits, respect rate limit headers

2. **Authentication token expiration**: Tokens expire during operation
   - Mitigation: Detect auth errors, pause operations, create alert file, resume when refreshed

3. **Component crashes**: Orchestrators or watchers crash
   - Mitigation: Watchdog monitors PIDs, auto-restart within 60 seconds, log crashes

### Low Risk
1. **Disk space**: Logs and vault data grow over time
   - Mitigation: 90-day log retention, periodic cleanup of old briefings

2. **Performance degradation**: System slows with many tasks
   - Mitigation: Designed for 50+ tasks/day, monitor performance, optimize if needed

---

## Next Steps

1. **Phase 1**: Create data-model.md defining entities and relationships
2. **Phase 1**: Create MCP server contracts in contracts/
3. **Phase 1**: Create quickstart.md for setup and usage
4. **Phase 2**: Generate tasks.md with implementation breakdown (/sp.tasks)
5. **Phase 3**: Implement tasks (/sp.implement)
