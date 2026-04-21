# Company Handbook

This handbook defines the rules and behaviors for your Personal AI Employee (Gold Tier).

## Purpose

The AI Employee reads this handbook to understand how to process files, prioritize tasks, and make decisions on your behalf. Update these rules to customize the AI's behavior.

---

## General Rules

### File Processing
- Review all files within 24 hours of detection
- Flag any files over 10 MB for manual review
- Categorize files by type (invoice, contract, report, etc.)
- Process files in priority order (urgent → high → normal → low)

### Prioritization
- Client communications are highest priority
- Financial documents require careful review
- Administrative tasks can be processed in batch
- Multi-step tasks are executed autonomously by Ralph Wiggum

### Decision Making
- When in doubt, ask for human approval
- Never make financial commitments without approval
- Always log reasoning for decisions
- Create approval requests for sensitive operations

---

## Gold Tier Capabilities

### Autonomous Task Execution (Ralph Wiggum)
- **Multi-Step Tasks**: Automatically breaks down and executes complex tasks
- **Max Iterations**: 10 steps per task (configurable)
- **Approval Workflow**: Creates approval requests for sensitive operations
- **Error Recovery**: Automatically retries failed operations with exponential backoff

**Rules**:
- All multi-step tasks must have clear acceptance criteria
- Tasks requiring financial commitments need approval
- Failed tasks are logged with full context
- Completed tasks are moved to Done/ folder

### Odoo ERP Integration
- **Invoice Creation**: Automatically creates invoices from approved requests
- **Payment Recording**: Records payments and updates invoice status
- **Financial Queries**: Generates financial reports on demand

**Rules**:
- All invoices over $500 require approval before creation
- Payment recordings must match invoice amounts
- Financial data is synced bidirectionally with vault
- Failed operations are queued for retry

### Social Media Automation
- **Platforms**: Facebook, Instagram, Twitter
- **Content Adaptation**: Automatically formats content for each platform
- **Approval Workflow**: Sensitive posts require approval before publishing
- **Engagement Tracking**: Collects metrics 24 hours after posting

**Rules**:
- All business updates require approval before posting
- Posts are adapted to platform-specific formats and limits
- Engagement metrics are collected and reported weekly
- Failed posts are queued for retry

### Weekly Audit Reports
- **Schedule**: Every Sunday at 11:00 PM
- **Data Sources**: Odoo (financials), Vault (tasks), Social Media (engagement)
- **Output**: Comprehensive CEO briefing in Briefings/ folder
- **Dashboard Integration**: Automatic link added to Dashboard.md

**Rules**:
- Audits run automatically without human intervention
- Briefings include financial performance, operational metrics, and recommendations
- Bottlenecks (tasks >2x expected time) are flagged
- Cost optimization opportunities are identified

### Error Recovery & Resilience
- **Retry Strategy**: Exponential backoff for transient errors (max 5 attempts)
- **Error Classification**: 10 error types with appropriate handling
- **Graceful Degradation**: Read-only mode during multiple failures
- **Alert System**: Automatic alerts for auth, config, data, and crash errors

**Rules**:
- Transient errors (network, timeout, rate limit) are retried automatically
- Permanent errors (auth, validation, config) are escalated immediately
- All errors are logged with complete context and stack traces
- Logs are retained for 90 days then automatically cleaned up

---

## Specific Rules

### Invoices
- Flag all invoices over $500 for review
- Check for duplicate invoice numbers
- Verify payment terms and due dates
- Log to accounting folder
- **Gold Tier**: Automatically create invoices in Odoo after approval
- **Gold Tier**: Sync invoice status bidirectionally with vault

### Contracts
- All contracts require human review before signing
- Check for expiration dates and renewal terms
- Flag any unusual clauses or terms
- **Gold Tier**: Create approval requests for contract-related tasks

### Client Communications
- Respond to client emails within 24 hours
- Maintain professional and friendly tone
- Escalate urgent requests immediately
- **Gold Tier**: Monitor Gmail for urgent keywords (if configured)
- **Gold Tier**: Create tasks for client requests automatically

### Reports
- Summarize key findings and recommendations
- Highlight any anomalies or concerns
- Archive completed reports to Done folder
- **Gold Tier**: Generate weekly CEO briefings automatically
- **Gold Tier**: Include financial, operational, and marketing metrics

### Social Media Posts
- **Gold Tier**: All business updates require approval before posting
- **Gold Tier**: Posts are automatically adapted for each platform:
  - Facebook: Detailed posts (up to 63,206 chars)
  - Instagram: Visual-focused with hashtags (up to 2,200 chars)
  - Twitter: Concise with thread support (280 chars per tweet)
- **Gold Tier**: Engagement metrics collected 24 hours after posting
- **Gold Tier**: Failed posts are queued and retried automatically

### Multi-Step Tasks
- **Gold Tier**: Ralph Wiggum executes multi-step tasks autonomously
- **Gold Tier**: Tasks are broken down into discrete steps
- **Gold Tier**: Each step is validated before proceeding
- **Gold Tier**: Failed steps trigger error recovery
- **Gold Tier**: Completed tasks are logged with full execution trace

---

## Approval Workflows

### When Approval is Required
1. **Financial Operations**:
   - Invoices over $500
   - Payment recordings over $1,000
   - Any financial commitments

2. **Social Media Posts**:
   - All business updates (default)
   - Posts mentioning clients or partners
   - Posts with external links

3. **Sensitive Operations**:
   - Contract signing or modifications
   - Client communications requiring commitments
   - System configuration changes

### Approval Process
1. AI creates approval request in Pending_Approval/
2. Approval request includes full context and preview
3. Human reviews and moves to Approved/ or Done/ (rejected)
4. AI processes approved items automatically
5. Rejected items are archived with reason

---

## Error Handling

### Transient Errors (Automatic Retry)
- Network timeouts
- Rate limiting (429 errors)
- Service temporarily unavailable (503 errors)
- Connection errors

**Action**: Retry with exponential backoff (1s, 2s, 4s, 8s, 16s)

### Permanent Errors (Immediate Escalation)
- Authentication failures (401, 403)
- Configuration errors (missing env vars)
- Data corruption (malformed JSON)
- Validation errors (400 errors)

**Action**: Create alert in Needs_Action/, log error, queue operation

### Graceful Degradation
When 2+ critical components fail:
- System enters read-only mode
- Read operations continue normally
- Write operations are queued for later
- Alert created in Needs_Action/
- Dashboard updated with degradation status

**Recovery**: Automatic when components recover

---

## Monitoring & Health Checks

### Component Health
- **Ralph Wiggum Loop**: Monitored by watchdog, auto-restart on crash
- **File Watcher**: Monitored by watchdog, auto-restart on crash
- **MCP Servers**: Health checked every 60 seconds
- **Integration Clients**: Connection status tracked

### Health Status Levels
- ✅ **Healthy**: All critical components operational
- ⚠️ **Degraded**: 1 critical component down, limited functionality
- 🔴 **Critical**: 2+ critical components down, read-only mode

### Alerts
Automatic alerts created for:
- Authentication failures (AUTH_ALERT)
- Configuration errors (CONFIG_ALERT)
- Data corruption (DATA_ALERT)
- Component crashes (CRASH_ALERT)
- System degradation (DEGRADATION_ALERT)
- MCP server failures (MCP_SERVER_ALERT)

**Action Required**: Review alerts in Needs_Action/, resolve issues, move to Done/

---

## Logging & Audit Trail

### Log Types
1. **Error Logs**: Logs/errors/ (90-day retention)
   - All errors with complete context
   - Stack traces and severity levels
   - Retry counts and error classification

2. **Watchdog Logs**: Logs/watchdog/ (90-day retention)
   - Component health checks
   - Restart operations
   - MCP server status

3. **Component Logs**: Logs/ (90-day retention)
   - Ralph Wiggum execution traces
   - File watcher activity
   - Orchestrator operations

### Audit Trail Requirements
- All operations logged with timestamp
- Full context (component, operation, parameters)
- Error details (type, message, stack trace)
- Retry attempts and outcomes
- User approvals and rejections

---

## Performance & Optimization

### Task Execution
- Multi-step tasks: Max 10 iterations
- Check intervals: 30-60 seconds (configurable)
- Retry delays: Exponential backoff (1s to 60s max)

### Resource Management
- Log retention: 90 days (automatic cleanup)
- Operation queue: Unlimited (cleared on success)
- Memory usage: Monitored by watchdog

### Rate Limiting
- Odoo: Built-in retry logic
- Facebook: 200 requests/hour
- Instagram: 200 requests/hour
- Twitter: 300 requests/15 minutes

---

## Security & Privacy

### Credentials Management
- All credentials stored in .env file (not in vault)
- Never commit .env to version control
- Rotate credentials regularly
- Use environment-specific credentials

### Data Protection
- Sensitive data never logged in plain text
- PII redacted from logs and reports
- Approval required for external data sharing
- Audit trail for all data access

### Access Control
- Human approval required for sensitive operations
- Financial commitments require explicit approval
- System configuration changes logged
- Alert files for security-related errors

---

## Custom Rules

Add your own rules here:

### Business-Specific Rules
- [Your custom rule 1]
- [Your custom rule 2]
- [Your custom rule 3]

### Client-Specific Rules
- [Client A: Special handling instructions]
- [Client B: Priority escalation rules]
- [Client C: Communication preferences]

### Industry-Specific Rules
- [Compliance requirements]
- [Regulatory guidelines]
- [Industry best practices]

---

## Troubleshooting

### Common Issues

**Issue**: Ralph Wiggum not executing tasks
- Check: Is Ralph Wiggum enabled in .env? (ENABLE_RALPH_WIGGUM=true)
- Check: Are there tasks in Multi_Step_Tasks/ folder?
- Check: Review Logs/RalphWiggum.log for errors

**Issue**: Odoo integration not working
- Check: Are Odoo credentials correct in .env?
- Check: Is Odoo server accessible?
- Check: Review Logs/errors/ for auth or connection errors
- Check: Look for AUTH_ALERT in Needs_Action/

**Issue**: Social media posts not publishing
- Check: Are social media credentials correct in .env?
- Check: Are posts in Approved/ folder (if approval required)?
- Check: Review Logs/errors/ for API errors
- Check: Verify rate limits not exceeded

**Issue**: Weekly audit not generating
- Check: Is weekly audit enabled in .env? (ENABLE_WEEKLY_AUDIT=true)
- Check: Is scheduler running?
- Check: Review Logs/AuditOrchestrator.log for errors

**Issue**: System in degraded mode
- Check: Dashboard.md for health status
- Check: Needs_Action/ for DEGRADATION_ALERT
- Check: Logs/watchdog/ for component failures
- Action: Resolve component failures, system will auto-recover

---

## Notes

- Rules are applied in order from top to bottom
- More specific rules override general rules
- Update this handbook as your needs evolve
- Gold tier features require proper configuration in .env
- Review Dashboard.md daily for system health and alerts
- Check Needs_Action/ folder regularly for items requiring attention

---

## Version History

- **v2.0** (2026-04-17): Gold tier capabilities added
  - Autonomous task execution (Ralph Wiggum)
  - Odoo ERP integration
  - Social media automation
  - Weekly audit reports
  - Enhanced error recovery
  
- **v1.0** (2026-04-16): Initial handbook
  - Bronze tier file processing
  - Basic rules and guidelines

---

*Last Updated*: 2026-04-17
*Tier*: Gold (Bronze + Silver + Gold)
*Version*: 2.0
