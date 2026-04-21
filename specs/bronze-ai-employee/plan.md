# Implementation Plan: Bronze Tier Personal AI Employee

**Branch**: `bronze-ai-employee` | **Date**: 2026-04-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/bronze-ai-employee/spec.md`

## Summary

Build a foundational Personal AI Employee system that monitors a local folder for dropped files, creates action items in an Obsidian vault, and enables Claude Code to read and process those items. This Bronze tier establishes the core perception-reasoning-action loop with human oversight.

**Technical Approach**: Python-based file watcher using watchdog library monitors /Inbox folder. When files are detected, creates structured markdown files in /Needs_Action with metadata. Claude Code Agent Skills read from vault, process according to Company_Handbook.md rules, and update Dashboard.md. All operations logged for audit trail.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: watchdog (file monitoring), python-dotenv (environment variables), pathlib (file operations)  
**Storage**: Local filesystem - Obsidian vault (markdown files)  
**Testing**: Manual testing for Bronze tier (automated testing in Silver+)  
**Target Platform**: Windows 10+ (with bash shell via Git Bash or WSL)  
**Project Type**: Single project - Python scripts + Obsidian vault  
**Performance Goals**: File detection within 5 seconds, process 10+ files without degradation  
**Constraints**: Local-only (no cloud sync), dry-run default, human approval for sensitive actions  
**Scale/Scope**: Single user, 100+ files/day capacity, 24/7 operation capability

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Local-First Privacy**: All data stays in local Obsidian vault, no cloud dependencies  
✅ **Human-in-the-Loop**: Bronze tier is read-only for Claude (no automated external actions)  
✅ **Audit-First Operations**: All watcher activity logged to /Logs with timestamps  
✅ **Agent Skills Architecture**: Claude functionality implemented as Agent Skills  
✅ **Fail-Safe Defaults**: DRY_RUN=true by default, explicit opt-in for real actions  
✅ **Minimal Viable Implementation**: Bronze tier only - no Silver/Gold features

## Project Structure

### Documentation (this feature)

```text
specs/bronze-ai-employee/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Implementation tasks (created by /sp.tasks)
```

### Source Code (repository root)

```text
AI_Employee_Vault/           # Obsidian vault (created by setup)
├── .obsidian/               # Obsidian config (auto-generated)
├── Inbox/                   # Drop zone for files
├── Needs_Action/            # Action items created by watcher
├── Done/                    # Completed tasks
├── Errors/                  # Failed processing
├── Logs/                    # System logs
├── Dashboard.md             # Main status view
└── Company_Handbook.md      # AI behavior rules

src/                         # Python source code
├── watchers/
│   ├── __init__.py
│   ├── base_watcher.py      # Abstract base class
│   └── file_watcher.py      # File system watcher implementation
├── utils/
│   ├── __init__.py
│   ├── logger.py            # Logging utilities
│   └── vault_manager.py     # Vault operations helper
└── main.py                  # Entry point / orchestrator

.claude/                     # Claude Code configuration
└── skills/                  # Agent Skills
    ├── process_action.md    # Skill: Process items from Needs_Action
    ├── update_dashboard.md  # Skill: Update Dashboard.md
    └── check_handbook.md    # Skill: Read and apply handbook rules

tests/                       # Manual test scripts for Bronze
└── manual_test_plan.md      # Test procedures

.env.example                 # Environment variables template
requirements.txt             # Python dependencies
README.md                    # Setup and usage instructions
```

**Structure Decision**: Single project structure chosen because Bronze tier is a standalone system with no frontend/backend separation. All components (watcher, vault, Claude integration) operate on the same machine. The Obsidian vault serves as both data store and user interface.

## Complexity Tracking

No constitution violations. All complexity is justified by Bronze tier requirements.

## Architecture Overview

### Component Interaction Flow

```
1. USER drops file into Inbox/
   ↓
2. FileWatcher (Python) detects new file
   ↓
3. FileWatcher creates metadata .md in Needs_Action/
   ↓
4. FileWatcher logs event to Logs/YYYY-MM-DD.log
   ↓
5. USER opens Obsidian vault
   ↓
6. USER sees new item in Dashboard.md (manual refresh)
   ↓
7. USER invokes Claude Code with Agent Skill
   ↓
8. Claude reads Needs_Action/, Company_Handbook.md
   ↓
9. Claude processes according to handbook rules
   ↓
10. Claude updates Dashboard.md with findings
    ↓
11. USER reviews and manually moves file to Done/
```

### Key Design Decisions

**Decision 1: File-Based Communication**
- **Options Considered**: Database, API, File system
- **Trade-offs**: DB adds complexity, API requires server, Files are simple and auditable
- **Rationale**: Files align with Obsidian's markdown-first approach, enable human inspection, and require no additional infrastructure
- **Principle**: Minimal Viable Implementation

**Decision 2: Watchdog Library for File Monitoring**
- **Options Considered**: Polling with os.listdir(), watchdog library, inotify (Linux-only)
- **Trade-offs**: Polling is CPU-intensive, inotify is platform-specific, watchdog is cross-platform
- **Rationale**: Watchdog provides event-driven monitoring with cross-platform support (Windows/Mac/Linux)
- **Principle**: Fail-Safe Defaults (reliable detection)

**Decision 3: Agent Skills for Claude Functionality**
- **Options Considered**: Inline prompts, Agent Skills, Custom MCP servers
- **Trade-offs**: Inline prompts are not reusable, MCP servers are overkill for Bronze
- **Rationale**: Agent Skills provide reusability, clear interfaces, and align with constitution requirement
- **Principle**: Agent Skills Architecture (constitution mandate)

**Decision 4: Manual Dashboard Updates (Bronze)**
- **Options Considered**: Auto-refresh, Manual refresh, Real-time sync
- **Trade-offs**: Auto-refresh requires background process, Real-time adds complexity
- **Rationale**: Bronze tier focuses on foundation. Manual refresh is acceptable for MVP. Auto-refresh deferred to Silver tier.
- **Principle**: Minimal Viable Implementation

## Interfaces and API Contracts

### FileWatcher → Vault Interface

**Input**: File dropped in `Inbox/`
**Output**: Markdown file created in `Needs_Action/`

```yaml
# Needs_Action/FILE_<filename>_<timestamp>.md
---
type: file_drop
original_name: invoice.pdf
size: 245678
timestamp: 2026-04-16T10:30:00Z
status: pending
---

## File Details
- **Name**: invoice.pdf
- **Size**: 245.7 KB
- **Detected**: 2026-04-16 10:30:00

## Suggested Actions
- [ ] Review file contents
- [ ] Determine next steps
- [ ] Move to Done when complete
```

### Claude Agent Skill → Vault Interface

**Input**: Read from `Needs_Action/` and `Company_Handbook.md`
**Output**: Update `Dashboard.md`

```markdown
# Dashboard

**Last Updated**: 2026-04-16 10:35:00
**System Status**: Active

## Pending Actions (3)
- FILE_invoice.pdf_20260416103000.md (10:30 AM)
- FILE_contract.docx_20260416102500.md (10:25 AM)
- FILE_report.xlsx_20260416101500.md (10:15 AM)

## Recent Activity
- [10:30] New file detected: invoice.pdf
- [10:25] New file detected: contract.docx
- [10:15] New file detected: report.xlsx
```

### Logger Interface

**Input**: Event data (timestamp, level, message, context)
**Output**: Log entry in `Logs/YYYY-MM-DD.log`

```
2026-04-16 10:30:00 | INFO | FileWatcher | File detected: invoice.pdf (245678 bytes)
2026-04-16 10:30:01 | INFO | FileWatcher | Created action item: FILE_invoice.pdf_20260416103000.md
2026-04-16 10:30:01 | INFO | FileWatcher | Updated dashboard with new item
```

## Non-Functional Requirements (NFRs)

### Performance
- **File Detection**: < 5 seconds from drop to action item creation
- **Watcher CPU**: < 5% CPU usage during idle monitoring
- **Memory**: < 50 MB for watcher process
- **Throughput**: Handle 10 files dropped simultaneously without loss

### Reliability
- **Uptime**: Watcher runs continuously for 24+ hours without crash
- **Error Recovery**: Watcher continues after individual file processing errors
- **Data Integrity**: No file overwrites, all files logged

### Security
- **Credentials**: No credentials required for Bronze tier (local-only)
- **File Access**: Watcher has read/write only to vault directory
- **Logging**: No sensitive data logged (filenames only, not contents)

### Usability
- **Setup Time**: < 30 minutes from zero to working system
- **Documentation**: README with step-by-step setup instructions
- **Error Messages**: Clear, actionable error messages in logs

## Data Management

### Source of Truth
- **Vault State**: Obsidian vault folder structure is authoritative
- **Logs**: Append-only log files for audit trail
- **No Database**: All state in filesystem

### Schema Evolution
- Markdown frontmatter is extensible (add fields without breaking)
- Version field in frontmatter for future compatibility

### Data Retention
- **Logs**: Retain for 90 days minimum (constitution requirement)
- **Done Files**: User decides when to archive/delete
- **Error Files**: Retain until manually reviewed

## Operational Readiness

### Observability
- **Logs**: All watcher events logged with timestamps
- **Dashboard**: Visual status in Obsidian
- **File Counts**: Pending/Done counts visible in Dashboard

### Deployment
- **Installation**: Python script + pip install requirements
- **Startup**: Manual start for Bronze (systemd/PM2 in Silver+)
- **Configuration**: .env file for vault path and settings

### Runbooks
- **Start Watcher**: `python src/main.py`
- **Stop Watcher**: Ctrl+C (graceful shutdown)
- **Check Logs**: Open `Logs/YYYY-MM-DD.log` in text editor
- **Reset System**: Delete all files in Needs_Action/ and Done/

## Risk Analysis and Mitigation

### Risk 1: Watcher Crashes Overnight
- **Likelihood**: Medium (unhandled exceptions)
- **Impact**: High (files not detected)
- **Mitigation**: Comprehensive error handling, try/except around file operations
- **Blast Radius**: Single user, local only
- **Kill Switch**: Ctrl+C stops watcher immediately

### Risk 2: File Overwrites
- **Likelihood**: Low (timestamp in filename)
- **Impact**: High (data loss)
- **Mitigation**: Timestamp-based unique filenames, check for existence before write
- **Blast Radius**: Single file
- **Kill Switch**: N/A (preventable)

### Risk 3: Disk Space Exhaustion
- **Likelihood**: Low (Bronze tier, small files)
- **Impact**: Medium (watcher fails)
- **Mitigation**: Log warning when disk < 1GB free, user manual cleanup
- **Blast Radius**: System-wide
- **Kill Switch**: Stop watcher, free space, restart

## Evaluation and Validation

### Definition of Done
- [ ] FileWatcher detects files in Inbox/ within 5 seconds
- [ ] Action items created in Needs_Action/ with correct metadata
- [ ] Dashboard.md shows pending count and recent activity
- [ ] Company_Handbook.md template exists with example rules
- [ ] Claude Agent Skill can read Needs_Action/ and update Dashboard
- [ ] All operations logged to Logs/ with timestamps
- [ ] README with setup instructions complete
- [ ] Manual test plan executed successfully

### Output Validation
- **Format**: All .md files have valid YAML frontmatter
- **Requirements**: All FR-001 through FR-010 met
- **Safety**: DRY_RUN=true by default, no external actions

## Next Steps

1. Run `/sp.tasks` to generate implementation tasks from this plan
2. Implement tasks in order (setup → watcher → vault → skills)
3. Manual testing against Bronze tier acceptance criteria
4. Document lessons learned for Silver tier planning
