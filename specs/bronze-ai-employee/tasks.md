---
description: "Implementation tasks for Bronze Tier Personal AI Employee"
---

# Tasks: Bronze Tier Personal AI Employee

**Input**: Design documents from `/specs/bronze-ai-employee/`
**Prerequisites**: plan.md (required), spec.md (required)

**Tests**: Manual testing for Bronze tier (automated testing deferred to Silver+)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure: src/, src/watchers/, src/utils/, tests/
- [ ] T002 Create Obsidian vault directory: AI_Employee_Vault/ with subdirectories
- [ ] T003 [P] Create requirements.txt with dependencies: watchdog, python-dotenv, pathlib
- [ ] T004 [P] Create .env.example with configuration template
- [ ] T005 [P] Create .gitignore to exclude .env, __pycache__, .obsidian/workspace
- [ ] T006 Create README.md with setup instructions and Bronze tier overview

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create src/utils/logger.py with logging utilities (timestamp, levels, file output)
- [ ] T008 Create src/utils/vault_manager.py with vault path validation and folder creation
- [ ] T009 Create src/watchers/base_watcher.py abstract base class with check_for_updates() and create_action_file()
- [ ] T010 Create .claude/skills/ directory for Agent Skills
- [ ] T011 Setup environment configuration: load .env, validate VAULT_PATH, set DRY_RUN default

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Drop File for AI Processing (Priority: P1) 🎯 MVP

**Goal**: Enable file detection, action item creation, and Claude Code processing

**Independent Test**: Drop a file into Inbox/, verify action item appears in Needs_Action/, run Claude skill to process it

### Implementation for User Story 1

- [ ] T012 [US1] Implement src/watchers/file_watcher.py extending BaseWatcher
  - Monitor AI_Employee_Vault/Inbox/ for new files
  - Check interval: 30 seconds
  - Handle file creation events
- [ ] T013 [US1] Implement create_action_file() in file_watcher.py
  - Generate unique filename: FILE_<original>_<timestamp>.md
  - Create YAML frontmatter with: type, original_name, size, timestamp, status
  - Write to AI_Employee_Vault/Needs_Action/
  - Log event to Logs/YYYY-MM-DD.log
- [ ] T014 [US1] Implement error handling in file_watcher.py
  - Try/except around file operations
  - Log errors to Logs/ and continue monitoring
  - Move problematic files to Errors/ folder
- [ ] T015 [US1] Create src/main.py orchestrator
  - Initialize logger
  - Validate vault structure (create missing folders)
  - Start FileWatcher with vault path from .env
  - Graceful shutdown on Ctrl+C
- [ ] T016 [US1] Create .claude/skills/process_action.md Agent Skill
  - Read all files from Needs_Action/
  - Parse YAML frontmatter
  - Check Company_Handbook.md for applicable rules
  - Generate processing summary
  - Output next steps for user
- [ ] T017 [US1] Create .claude/skills/move_to_done.md Agent Skill
  - Move specified file from Needs_Action/ to Done/
  - Append completion timestamp to frontmatter
  - Update Dashboard.md with completion
  - Log the move operation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - View Dashboard Summary (Priority: P2)

**Goal**: Provide visual status overview in Obsidian Dashboard.md

**Independent Test**: Open Dashboard.md in Obsidian, verify it shows pending count, recent activity, and system status

### Implementation for User Story 2

- [ ] T018 [US2] Create AI_Employee_Vault/Dashboard.md template
  - Header with last updated timestamp
  - System Status section (Active/Inactive)
  - Pending Actions count and list (top 10)
  - Recent Activity section (last 10 events)
  - Quick links to Needs_Action/, Done/, Logs/
- [ ] T019 [US2] Implement dashboard update logic in src/utils/vault_manager.py
  - Function: update_dashboard(vault_path, event_type, event_data)
  - Read current Dashboard.md
  - Update timestamp
  - Append to Recent Activity (keep last 10)
  - Update Pending Actions count
  - Write back to Dashboard.md
- [ ] T020 [US2] Integrate dashboard updates into file_watcher.py
  - Call update_dashboard() after creating action item
  - Pass event: "File detected: <filename>"
- [ ] T021 [US2] Create .claude/skills/update_dashboard.md Agent Skill
  - Read current vault state (count files in Needs_Action/, Done/)
  - Regenerate Dashboard.md with current counts
  - Add timestamp
  - Preserve Recent Activity section
- [ ] T022 [US2] Add dashboard refresh to main.py startup
  - Call update_dashboard() on startup to show "System Status: Active"
  - Update timestamp to show watcher is running

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Define AI Behavior Rules (Priority: P3)

**Goal**: Enable user customization of AI behavior through Company_Handbook.md

**Independent Test**: Add a rule to Company_Handbook.md, run process_action skill, verify Claude references the rule

### Implementation for User Story 3

- [ ] T023 [US3] Create AI_Employee_Vault/Company_Handbook.md template
  - Introduction explaining purpose
  - Example rules section with 3-5 sample rules
  - Rule format: clear, actionable statements
  - Examples: "Flag invoices over $500", "Prioritize client emails", "Log all financial documents"
- [ ] T024 [US3] Update .claude/skills/process_action.md to read handbook
  - Add step: Read Company_Handbook.md before processing
  - Extract applicable rules based on file type/content
  - Reference specific rules in processing output
  - Show which rules were applied
- [ ] T025 [US3] Create .claude/skills/check_handbook.md Agent Skill
  - Read Company_Handbook.md
  - Display all current rules
  - Validate rule format (clear, actionable)
  - Suggest improvements if rules are vague
- [ ] T026 [US3] Add handbook validation to main.py startup
  - Check if Company_Handbook.md exists
  - Create from template if missing
  - Log warning if handbook is empty

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Create tests/manual_test_plan.md with step-by-step test procedures
  - Test 1: File detection and action item creation
  - Test 2: Dashboard updates
  - Test 3: Claude skills execution
  - Test 4: Handbook rule application
  - Test 5: Error handling (invalid files, missing folders)
- [ ] T028 [P] Update README.md with complete setup instructions
  - Prerequisites (Python 3.13+, Obsidian, Claude Code)
  - Installation steps (clone, pip install, .env setup)
  - Usage instructions (start watcher, open vault, run skills)
  - Troubleshooting section
- [ ] T029 Add comprehensive logging throughout all components
  - Startup/shutdown events
  - File detection events
  - Action item creation
  - Dashboard updates
  - Errors with stack traces
- [ ] T030 [P] Create example files for testing in tests/fixtures/
  - sample_invoice.pdf (empty file for testing)
  - sample_document.txt
  - sample_spreadsheet.xlsx
- [ ] T031 Verify all constitution requirements are met
  - Local-first: No cloud dependencies ✓
  - HITL: No automated external actions ✓
  - Audit-first: All operations logged ✓
  - Agent Skills: All Claude functionality as skills ✓
  - Fail-safe: DRY_RUN default ✓
  - Minimal: Bronze tier only ✓
- [ ] T032 Create .claude/skills/README.md documenting all skills
  - process_action.md: Purpose, inputs, outputs, usage
  - update_dashboard.md: Purpose, inputs, outputs, usage
  - move_to_done.md: Purpose, inputs, outputs, usage
  - check_handbook.md: Purpose, inputs, outputs, usage

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Enhances US1 but independently testable

### Within Each User Story

- Core implementation before integration
- Error handling after core functionality
- Agent Skills after core Python implementation
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All Polish tasks marked [P] can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T011) - CRITICAL
3. Complete Phase 3: User Story 1 (T012-T017)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Demo: Drop file → See action item → Run Claude skill → Process

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (MVP!)
3. Add User Story 2 → Test independently → Demo (Dashboard works)
4. Add User Story 3 → Test independently → Demo (Customization works)
5. Add Polish → Complete Bronze tier

### Sequential Strategy (Recommended for Solo Developer)

1. T001-T006 (Setup) - 1 hour
2. T007-T011 (Foundational) - 2 hours
3. T012-T017 (US1) - 3 hours
4. **Validate US1** - 30 minutes
5. T018-T022 (US2) - 2 hours
6. **Validate US2** - 30 minutes
7. T023-T026 (US3) - 1 hour
8. **Validate US3** - 30 minutes
9. T027-T032 (Polish) - 2 hours
10. **Final validation** - 1 hour

**Total estimated time**: 12-14 hours (Bronze tier target: 8-12 hours)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All file paths are relative to repository root
- Vault path (AI_Employee_Vault/) is configurable via .env
