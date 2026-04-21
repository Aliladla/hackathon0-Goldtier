# Feature Specification: Bronze Tier Personal AI Employee

**Feature Branch**: `bronze-ai-employee`  
**Created**: 2026-04-16  
**Status**: Draft  
**Input**: User description: "Build Bronze tier Personal AI Employee with Obsidian vault, file watcher, and Claude Code integration"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Drop File for AI Processing (Priority: P1)

As a user, I want to drop a file into a monitored folder and have my AI Employee automatically detect it, create an action item in my Obsidian vault, and process it according to my handbook rules.

**Why this priority**: This is the core perception-reasoning-action loop. Without this, there's no autonomous behavior. It's the foundation for all higher tiers.

**Independent Test**: Can be fully tested by dropping a text file into /Inbox and verifying that: (1) a .md file appears in /Needs_Action, (2) Claude Code can read it, (3) the file moves to /Done after processing.

**Acceptance Scenarios**:

1. **Given** the file watcher is running and /Inbox is empty, **When** I drop "invoice.pdf" into /Inbox, **Then** a file "FILE_invoice.pdf.md" appears in /Needs_Action within 5 seconds with metadata
2. **Given** a file exists in /Needs_Action, **When** I run Claude Code with the vault path, **Then** Claude reads the file and creates a plan in Dashboard.md
3. **Given** Claude has processed a file, **When** the task is complete, **Then** the file moves from /Needs_Action to /Done with timestamp

---

### User Story 2 - View Dashboard Summary (Priority: P2)

As a user, I want to open my Obsidian vault and see a Dashboard.md that shows me all pending actions, recent activity, and system status at a glance.

**Why this priority**: The dashboard is the user's window into what the AI is doing. Critical for trust and oversight, but the system can function without it initially.

**Independent Test**: Can be tested by manually creating sample files in /Needs_Action and /Done, then verifying Dashboard.md displays them correctly with timestamps and status.

**Acceptance Scenarios**:

1. **Given** there are 3 files in /Needs_Action, **When** I open Dashboard.md, **Then** I see a list of 3 pending items with creation timestamps
2. **Given** the AI has completed 5 tasks today, **When** I check Dashboard.md, **Then** I see "Recent Activity" section with 5 completed items
3. **Given** the file watcher is running, **When** I check Dashboard.md, **Then** I see "System Status: Active" with last check timestamp

---

### User Story 3 - Define AI Behavior Rules (Priority: P3)

As a user, I want to write rules in Company_Handbook.md that guide how my AI Employee should behave, prioritize tasks, and make decisions.

**Why this priority**: Customization is important for long-term use, but the system can operate with default behavior initially. This enables personalization.

**Independent Test**: Can be tested by adding a rule like "Always flag invoices over $500 for review" and verifying Claude Code references this rule when processing invoice files.

**Acceptance Scenarios**:

1. **Given** Company_Handbook.md contains "Flag all invoices over $500", **When** Claude processes an invoice for $600, **Then** it creates an approval request instead of auto-processing
2. **Given** the handbook says "Respond to client emails within 24 hours", **When** Claude sees a client email in /Needs_Action, **Then** it prioritizes it over other tasks
3. **Given** I update a rule in the handbook, **When** Claude processes the next task, **Then** it uses the updated rule

---

### Edge Cases

- What happens when the /Inbox folder doesn't exist? (System should create it on startup)
- What happens when a file is dropped while the watcher is offline? (Should be detected on next startup)
- What happens when Claude Code can't parse a file? (Should log error and move to /Errors folder)
- What happens when /Needs_Action has 100+ files? (Dashboard should paginate or show top 10 most recent)
- What happens when the same file is dropped twice? (Should append timestamp to avoid overwrite)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST monitor /Inbox folder for new files continuously (check every 30 seconds)
- **FR-002**: System MUST create metadata .md files in /Needs_Action for each detected file with: original filename, size, timestamp, file type
- **FR-003**: System MUST maintain an Obsidian vault with folders: /Inbox, /Needs_Action, /Done, /Errors, /Logs
- **FR-004**: System MUST provide Dashboard.md that displays: pending actions count, recent activity (last 10), system status
- **FR-005**: System MUST provide Company_Handbook.md template with example rules for AI behavior
- **FR-006**: Claude Code MUST be able to read files from /Needs_Action and write updates to Dashboard.md
- **FR-007**: System MUST log all watcher activity to /Logs/YYYY-MM-DD.log with timestamps
- **FR-008**: System MUST support dry-run mode (DRY_RUN=true) that logs actions without executing them
- **FR-009**: System MUST move processed files from /Needs_Action to /Done with completion timestamp
- **FR-010**: All AI functionality MUST be implemented as Claude Code Agent Skills

### Key Entities

- **Vault**: The Obsidian workspace containing all folders and markdown files
- **Action Item**: A .md file in /Needs_Action representing work to be done, with metadata frontmatter
- **Watcher**: A Python script that monitors /Inbox and creates Action Items
- **Dashboard**: A markdown file (Dashboard.md) showing system state and activity
- **Handbook**: A markdown file (Company_Handbook.md) containing behavioral rules for the AI

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can drop a file into /Inbox and see it appear in /Needs_Action within 5 seconds
- **SC-002**: Claude Code can successfully read all files in /Needs_Action and generate appropriate responses
- **SC-003**: Dashboard.md accurately reflects system state (pending count, recent activity) at all times
- **SC-004**: File watcher runs continuously for 24 hours without crashing or missing files
- **SC-005**: All operations are logged with timestamps and can be audited in /Logs
- **SC-006**: User can set up the entire system from scratch in under 30 minutes following documentation
