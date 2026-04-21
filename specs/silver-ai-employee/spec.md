# Feature Specification: Silver Tier Personal AI Employee

**Feature Branch**: `silver-ai-employee`  
**Created**: 2026-04-16  
**Status**: Draft  
**Input**: User description: "Build Silver tier Personal AI Employee with Gmail/WhatsApp/LinkedIn watchers, MCP server, approval workflow, and scheduling"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Monitor Gmail for Important Messages (Priority: P1)

As a user, I want my AI Employee to monitor my Gmail inbox for important messages, create action items for urgent emails, and draft replies according to my handbook rules.

**Why this priority**: Email is the primary business communication channel. Automating email triage and draft responses saves significant time and ensures timely responses.

**Independent Test**: Can be fully tested by sending a test email to the monitored Gmail account, verifying that: (1) the email is detected within 2 minutes, (2) an action item is created in /Needs_Action, (3) Claude can draft a reply based on handbook rules.

**Acceptance Scenarios**:

1. **Given** Gmail watcher is running and monitoring inbox, **When** an important email arrives (flagged or from known contact), **Then** an action item appears in /Needs_Action within 2 minutes with email metadata
2. **Given** an email action item exists in /Needs_Action, **When** I run Claude's process_email skill, **Then** Claude drafts a reply based on Company_Handbook rules and creates an approval request
3. **Given** I approve an email draft in /Approved, **When** the orchestrator processes approvals, **Then** the email is sent via MCP server and logged

---

### User Story 2 - Monitor WhatsApp for Urgent Messages (Priority: P2)

As a user, I want my AI Employee to monitor WhatsApp Web for messages containing urgent keywords (e.g., "urgent", "asap", "invoice", "payment") and create action items for follow-up.

**Why this priority**: WhatsApp is increasingly used for business communication. Urgent messages need immediate attention, but monitoring manually is time-consuming.

**Independent Test**: Can be tested by sending a WhatsApp message with keyword "urgent" to yourself, verifying that: (1) the message is detected within 30 seconds, (2) an action item is created with message content, (3) Claude can suggest appropriate responses.

**Acceptance Scenarios**:

1. **Given** WhatsApp watcher is running with authenticated session, **When** a message arrives containing urgent keywords, **Then** an action item is created in /Needs_Action with sender and message content
2. **Given** a WhatsApp action item exists, **When** I run Claude's process_whatsapp skill, **Then** Claude suggests appropriate responses based on message context and handbook rules
3. **Given** multiple urgent messages arrive simultaneously, **When** the watcher processes them, **Then** all messages are captured without loss

---

### User Story 3 - Auto-Post to LinkedIn for Business (Priority: P2)

As a user, I want my AI Employee to automatically draft LinkedIn posts about my business activities, get my approval, and post them to generate sales leads.

**Why this priority**: Consistent LinkedIn presence generates business opportunities. Automating post creation and scheduling ensures regular engagement without manual effort.

**Independent Test**: Can be tested by creating a business update in /Business_Updates folder, verifying that: (1) Claude drafts a LinkedIn post, (2) post appears in /Pending_Approval, (3) after approval, post is scheduled or published.

**Acceptance Scenarios**:

1. **Given** I drop a business update file in /Business_Updates, **When** Claude processes it, **Then** a LinkedIn post draft is created with appropriate hashtags and call-to-action
2. **Given** a LinkedIn post draft in /Pending_Approval, **When** I approve it, **Then** the post is published to LinkedIn via API or automation
3. **Given** a post is published, **When** the system logs the event, **Then** the post URL and timestamp are recorded in /Logs and Dashboard

---

### User Story 4 - Human-in-the-Loop Approval Workflow (Priority: P1)

As a user, I want all sensitive actions (sending emails, posting to social media, making payments) to require my explicit approval before execution.

**Why this priority**: This is a constitution requirement and critical safety feature. Without approval workflow, the AI could take unintended actions.

**Independent Test**: Can be tested by triggering an email send action, verifying that: (1) approval request appears in /Pending_Approval, (2) action does NOT execute until file is moved to /Approved, (3) rejection moves file to /Rejected and cancels action.

**Acceptance Scenarios**:

1. **Given** Claude wants to send an email, **When** it creates the draft, **Then** an approval request file is created in /Pending_Approval with action details
2. **Given** an approval request in /Pending_Approval, **When** I move it to /Approved, **Then** the action executes within 30 seconds and result is logged
3. **Given** an approval request in /Pending_Approval, **When** I move it to /Rejected, **Then** the action is cancelled and rejection is logged

---

### User Story 5 - Scheduled Daily Briefing (Priority: P3)

As a user, I want my AI Employee to generate a daily briefing every morning at 8 AM summarizing pending actions, recent activity, and priorities for the day.

**Why this priority**: A daily briefing provides situational awareness and helps prioritize work. Lower priority because the system is useful without it.

**Independent Test**: Can be tested by manually triggering the briefing skill, verifying that: (1) briefing includes pending count, recent activity, and priorities, (2) briefing is saved to /Briefings folder, (3) Dashboard is updated with briefing link.

**Acceptance Scenarios**:

1. **Given** it is 8:00 AM, **When** the scheduled task runs, **Then** a daily briefing is generated and saved to /Briefings/YYYY-MM-DD_briefing.md
2. **Given** the briefing is generated, **When** I open it, **Then** it shows pending actions count, top 5 priorities, recent activity summary, and suggested focus areas
3. **Given** there are overdue items, **When** the briefing is generated, **Then** overdue items are highlighted with urgency indicators

---

### Edge Cases

- What happens when Gmail API rate limit is reached? (Exponential backoff, log warning)
- What happens when WhatsApp session expires? (Alert user, pause watcher until re-authenticated)
- What happens when LinkedIn API returns error? (Retry with backoff, move to /Errors if persistent)
- What happens when approval request expires (>24 hours)? (Auto-reject and notify user)
- What happens when multiple approvals are pending? (Process in order, show count in Dashboard)
- What happens when MCP server is unavailable? (Queue actions, retry when available)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST monitor Gmail inbox every 2 minutes for new important messages (flagged or from known contacts)
- **FR-002**: System MUST monitor WhatsApp Web every 30 seconds for messages containing urgent keywords
- **FR-003**: System MUST create action items in /Needs_Action for detected emails and messages with full metadata
- **FR-004**: System MUST provide MCP server for sending emails with authentication and error handling
- **FR-005**: System MUST implement approval workflow with /Pending_Approval, /Approved, /Rejected folders
- **FR-006**: System MUST NOT execute sensitive actions without explicit approval (moved to /Approved)
- **FR-007**: System MUST support LinkedIn post drafting and publishing via API or automation
- **FR-008**: System MUST provide scheduled task for daily briefing at configurable time (default 8 AM)
- **FR-009**: System MUST log all external actions (emails sent, posts published) with timestamps and results
- **FR-010**: System MUST provide Agent Skills for: process_email, process_whatsapp, draft_linkedin_post, approve_action, generate_briefing
- **FR-011**: System MUST handle API rate limits with exponential backoff and retry logic
- **FR-012**: System MUST alert user when authentication expires (Gmail OAuth, WhatsApp session)

### Key Entities

- **Email Action Item**: Action item created from Gmail message with: sender, subject, snippet, importance, labels
- **WhatsApp Action Item**: Action item created from WhatsApp message with: sender, message text, timestamp, urgency
- **Approval Request**: File in /Pending_Approval with: action type, parameters, expiration, risk level
- **LinkedIn Post Draft**: Draft post with: content, hashtags, scheduled time, target audience
- **Daily Briefing**: Summary document with: pending count, priorities, recent activity, focus areas

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Gmail watcher detects important emails within 2 minutes of arrival with 99% reliability
- **SC-002**: WhatsApp watcher detects urgent messages within 30 seconds with 95% reliability
- **SC-003**: Approval workflow prevents 100% of sensitive actions from executing without approval
- **SC-004**: MCP server successfully sends emails with 95% success rate (excluding user errors)
- **SC-005**: Daily briefing generates successfully every day at scheduled time
- **SC-006**: System handles API rate limits gracefully without crashes or data loss
- **SC-007**: User can set up Silver tier from Bronze tier in under 2 hours following documentation
