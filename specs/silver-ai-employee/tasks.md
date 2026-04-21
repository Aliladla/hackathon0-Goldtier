---
description: "Implementation tasks for Silver Tier Personal AI Employee"
---

# Tasks: Silver Tier Personal AI Employee

**Input**: Design documents from `/specs/silver-ai-employee/`
**Prerequisites**: plan.md (required), spec.md (required), Bronze tier complete

**Tests**: Manual testing for Silver tier (automated testing deferred to Gold+)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend Bronze tier with Silver tier infrastructure

- [ ] T001 Create new vault folders: Pending_Approval/, Approved/, Rejected/, Briefings/, Business_Updates/
- [ ] T002 Create src/orchestrators/ directory for approval and scheduling logic
- [ ] T003 Create mcp-servers/email-server/ directory for Node.js MCP server
- [ ] T004 Create config/ directory for credentials (add to .gitignore)
- [ ] T005 [P] Update requirements.txt with: google-api-python-client, google-auth-oauthlib, playwright, schedule
- [ ] T006 [P] Create mcp-servers/email-server/package.json with @modelcontextprotocol/sdk, nodemailer
- [ ] T007 Update .env.example with Gmail, WhatsApp, LinkedIn, MCP server configuration
- [ ] T008 Update .gitignore to exclude config/, gmail_token.json, whatsapp_session/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 Create src/utils/gmail_auth.py with OAuth2 flow, token refresh, credential validation
- [ ] T010 Create src/utils/retry_handler.py with exponential backoff, max retries, rate limit handling
- [ ] T011 Extend src/utils/vault_manager.py with approval workflow methods (check_pending, move_to_approved, etc.)
- [ ] T012 Create src/orchestrators/approval_orchestrator.py base class with folder watching logic
- [ ] T013 Create src/orchestrators/scheduler.py with schedule library integration and task registration
- [ ] T014 Update src/main.py to start approval orchestrator and scheduler alongside watchers

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Monitor Gmail (Priority: P1) 🎯 MVP

**Goal**: Enable Gmail monitoring, email action item creation, and draft reply workflow

**Independent Test**: Send test email, verify action item created, draft reply with Claude, approve and send

### Implementation for User Story 1

- [ ] T015 [US1] Implement src/watchers/gmail_watcher.py extending BaseWatcher
  - Use Gmail API to list messages with q='is:important OR is:starred'
  - Check interval: 120 seconds (2 minutes)
  - Track processed message IDs to avoid duplicates
- [ ] T016 [US1] Implement create_action_file() for Gmail in gmail_watcher.py
  - Generate filename: EMAIL_<message_id>_<timestamp>.md
  - Extract: from, subject, snippet, labels, importance
  - Create YAML frontmatter with email metadata
  - Write to Needs_Action/
- [ ] T017 [US1] Implement error handling and rate limit handling in gmail_watcher.py
  - Catch HttpError for rate limits (429)
  - Use retry_handler for exponential backoff
  - Log errors and continue monitoring
- [ ] T018 [US1] Create mcp-servers/email-server/index.js MCP server
  - Implement send_email tool with: to, subject, body, reply_to_message_id
  - Use nodemailer with Gmail SMTP
  - Return success/failure with message_id
  - Handle authentication errors
- [ ] T019 [US1] Implement src/orchestrators/email_approval_orchestrator.py
  - Watch Approved/ folder for APPROVAL_EMAIL_* files
  - Parse approval file to extract email parameters
  - Call MCP server to send email
  - Log result and move file to Done/
- [ ] T020 [US1] Create .claude/skills/process_email.md Agent Skill
  - Read email action items from Needs_Action/
  - Apply Company_Handbook rules for email responses
  - Draft reply based on context and rules
  - Create approval request in Pending_Approval/
- [ ] T021 [US1] Create .claude/skills/approve_action.md Agent Skill
  - List all pending approvals with details
  - Show action type, parameters, risk level
  - Provide commands to approve (move to Approved/) or reject (move to Rejected/)
- [ ] T022 [US1] Update src/main.py to start Gmail watcher and email approval orchestrator

**Checkpoint**: Gmail monitoring and email workflow fully functional

---

## Phase 4: User Story 4 - Approval Workflow (Priority: P1)

**Goal**: Implement human-in-the-loop approval workflow for all sensitive actions

**Independent Test**: Create approval request, move to Approved/, verify action executes and logs

### Implementation for User Story 4

- [ ] T023 [US4] Extend src/orchestrators/approval_orchestrator.py with generic action handling
  - Support multiple action types: send_email, post_linkedin, send_whatsapp
  - Route to appropriate handler based on action type
  - Implement expiration check (reject if >24 hours old)
- [ ] T024 [US4] Implement approval request template in vault_manager.py
  - Standard format for all approval requests
  - Include: action type, parameters, created_at, expires_at, risk_level
  - Add approval instructions
- [ ] T025 [US4] Implement rejection handling in approval_orchestrator.py
  - Watch Rejected/ folder
  - Log rejection with reason
  - Move file to Done/ with rejection status
  - Update Dashboard with rejection event
- [ ] T026 [US4] Add approval metrics to Dashboard
  - Pending approvals count
  - Recent approvals (approved/rejected)
  - Expired approvals alert

**Checkpoint**: Approval workflow operational for all action types

---

## Phase 5: User Story 2 - Monitor WhatsApp (Priority: P2)

**Goal**: Enable WhatsApp Web monitoring for urgent messages

**Independent Test**: Send WhatsApp message with "urgent" keyword, verify action item created

### Implementation for User Story 2

- [ ] T027 [US2] Implement src/watchers/whatsapp_watcher.py extending BaseWatcher
  - Use Playwright to connect to WhatsApp Web
  - Maintain persistent session in config/whatsapp_session/
  - Check for unread messages every 30 seconds
  - Filter by urgent keywords: urgent, asap, invoice, payment, help
- [ ] T028 [US2] Implement session management in whatsapp_watcher.py
  - Check if session exists and is valid
  - Prompt user to scan QR code if session expired
  - Save session data for persistence
  - Handle session expiration gracefully
- [ ] T029 [US2] Implement create_action_file() for WhatsApp
  - Generate filename: WHATSAPP_<contact>_<timestamp>.md
  - Extract: sender name, message text, timestamp
  - Mark urgency level based on keywords
  - Write to Needs_Action/
- [ ] T030 [US2] Create .claude/skills/process_whatsapp.md Agent Skill
  - Read WhatsApp action items from Needs_Action/
  - Analyze message context and urgency
  - Suggest appropriate responses based on handbook
  - Note: Silver tier does not auto-send WhatsApp (manual only)
- [ ] T031 [US2] Update src/main.py to start WhatsApp watcher

**Checkpoint**: WhatsApp monitoring operational

---

## Phase 6: User Story 3 - LinkedIn Auto-Posting (Priority: P2)

**Goal**: Enable LinkedIn post drafting and publishing workflow

**Independent Test**: Drop business update file, verify LinkedIn post draft created, approve and publish

### Implementation for User Story 3

- [ ] T032 [US3] Implement src/watchers/linkedin_watcher.py extending BaseWatcher
  - Monitor Business_Updates/ folder for new files
  - Check interval: 60 seconds
  - Process markdown or text files
- [ ] T033 [US3] Create .claude/skills/draft_linkedin_post.md Agent Skill
  - Read business update from Business_Updates/
  - Generate LinkedIn post with:
    - Engaging opening
    - Key points from update
    - Relevant hashtags
    - Call-to-action
  - Create approval request in Pending_Approval/
- [ ] T034 [US3] Implement LinkedIn posting logic (choose one approach):
  - Option A: LinkedIn API (requires app approval)
  - Option B: Playwright automation (simpler, no approval needed)
  - Option C: Manual copy-paste (Silver tier fallback)
- [ ] T035 [US3] Implement src/orchestrators/linkedin_approval_orchestrator.py
  - Watch Approved/ for APPROVAL_LINKEDIN_* files
  - Execute LinkedIn post (via chosen method)
  - Log result with post URL
  - Move file to Done/
- [ ] T036 [US3] Update src/main.py to start LinkedIn watcher and orchestrator

**Checkpoint**: LinkedIn posting workflow operational

---

## Phase 7: User Story 5 - Scheduled Daily Briefing (Priority: P3)

**Goal**: Generate daily briefing at scheduled time

**Independent Test**: Manually trigger briefing, verify content and format

### Implementation for User Story 5

- [ ] T037 [US5] Implement scheduled task registration in scheduler.py
  - Use schedule library to register daily task
  - Default time: 8:00 AM (configurable in .env)
  - Handle timezone correctly
- [ ] T038 [US5] Create .claude/skills/generate_briefing.md Agent Skill
  - Count pending actions in Needs_Action/
  - Identify high priority items (overdue, urgent keywords)
  - Summarize recent activity from logs
  - Generate focus areas based on handbook rules
  - Save to Briefings/YYYY-MM-DD_briefing.md
- [ ] T039 [US5] Implement briefing generation in scheduler.py
  - Call Claude skill via subprocess or API
  - Handle errors gracefully
  - Log briefing generation
  - Update Dashboard with briefing link
- [ ] T040 [US5] Add briefing link to Dashboard
  - Show "Today's Briefing" section
  - Link to latest briefing
  - Show generation timestamp

**Checkpoint**: Daily briefing operational

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Update README.md with Silver tier setup instructions
  - Gmail OAuth setup steps
  - WhatsApp session setup steps
  - MCP server installation and configuration
  - LinkedIn setup (chosen method)
  - Approval workflow usage
- [ ] T042 [P] Create tests/manual_test_plan_silver.md
  - Test 1: Gmail detection and email workflow
  - Test 2: WhatsApp detection
  - Test 3: LinkedIn posting workflow
  - Test 4: Approval workflow (approve and reject)
  - Test 5: Daily briefing generation
  - Test 6: Error handling (rate limits, session expiration)
- [ ] T043 Update .claude/skills/README.md with new skills documentation
- [ ] T044 [P] Create setup wizard scripts
  - setup_gmail.py for OAuth flow
  - setup_whatsapp.py for session creation
  - setup_mcp.sh for MCP server installation
- [ ] T045 Add comprehensive error handling across all watchers
  - API rate limits with exponential backoff
  - Network errors with retry logic
  - Authentication errors with user alerts
- [ ] T046 Verify all constitution requirements still met
  - Local-first: Credentials stored locally ✓
  - HITL: All external actions require approval ✓
  - Audit-first: All actions logged ✓
  - Agent Skills: All functionality as skills ✓
  - Fail-safe: DRY_RUN default ✓
- [ ] T047 Create SILVER_TIER_COMPLETE.md with deliverables summary

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (Gmail) and US4 (Approval) should be done together (tightly coupled)
  - US2 (WhatsApp) can proceed in parallel after Foundational
  - US3 (LinkedIn) can proceed in parallel after Foundational
  - US5 (Briefing) should be done last (depends on other features for content)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Gmail) + US4 (Approval)**: Tightly coupled - implement together
- **US2 (WhatsApp)**: Independent after Foundational
- **US3 (LinkedIn)**: Independent after Foundational
- **US5 (Briefing)**: Depends on US1-4 for meaningful content

### Critical Path

1. Setup (Phase 1) → 1 hour
2. Foundational (Phase 2) → 3 hours
3. US1 + US4 (Gmail + Approval) → 6 hours
4. US2 (WhatsApp) → 3 hours
5. US3 (LinkedIn) → 3 hours
6. US5 (Briefing) → 2 hours
7. Polish (Phase 8) → 2 hours

**Total estimated time**: 20 hours (Silver tier target: 20-30 hours)

---

## Implementation Strategy

### MVP First (US1 + US4 Only)

1. Complete Phase 1: Setup (T001-T008)
2. Complete Phase 2: Foundational (T009-T014)
3. Complete Phase 3: Gmail (T015-T022)
4. Complete Phase 4: Approval (T023-T026)
5. **STOP and VALIDATE**: Test Gmail → Draft → Approve → Send workflow
6. Demo: Email arrives → Action item → Claude drafts → Approve → Email sent

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add Gmail + Approval → Test independently → Demo (MVP!)
3. Add WhatsApp → Test independently → Demo
4. Add LinkedIn → Test independently → Demo
5. Add Briefing → Test independently → Demo
6. Add Polish → Complete Silver tier

### Parallel Strategy (if multiple developers)

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: Gmail + Approval (US1 + US4)
   - Developer B: WhatsApp (US2)
   - Developer C: LinkedIn (US3)
3. Developer A: Briefing (US5) after US1-4 complete
4. All: Polish together

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Gmail + Approval are tightly coupled - implement together
- WhatsApp and LinkedIn can be done in parallel
- Briefing should be done last (needs other features for content)
- All file paths are relative to repository root
- Vault path (AI_Employee_Vault/) is configurable via .env
- MCP server runs as separate Node.js process
