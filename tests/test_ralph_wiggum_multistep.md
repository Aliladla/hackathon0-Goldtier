# Ralph Wiggum Multi-Step Task Test

## Purpose
Test the Ralph Wiggum autonomous loop with a complex multi-step task requiring invoice creation, email notification, and accounting entry.

## Test Scenario

**Task**: Process a new client invoice end-to-end
- Create invoice in Odoo
- Send email notification to client
- Record accounting entry
- Update dashboard

## Prerequisites

1. **Environment Configuration** (.env):
   ```bash
   ENABLE_RALPH_WIGGUM=true
   RALPH_MAX_ITERATIONS=10
   RALPH_CHECK_INTERVAL=60
   DRY_RUN=false
   ```

2. **System Running**:
   ```bash
   python src/main.py
   ```

3. **Vault Structure**:
   - AI_Employee_Vault/Needs_Action/ (monitored)
   - AI_Employee_Vault/Done/ (completion target)
   - AI_Employee_Vault/Approved/ (approval gate)

## Test Task File

Create this file in `AI_Employee_Vault/Needs_Action/TASK_invoice_client_acme.md`:

```markdown
---
type: multi_step_task
priority: high
client: Acme Corp
invoice_amount: 5000.00
created: 2026-04-17T10:00:00Z
---

## Multi-Step Task: Process Acme Corp Invoice

**Client**: Acme Corp
**Amount**: $5,000.00
**Due Date**: 2026-05-17

### Steps Required

1. **Create Invoice in Odoo**
   - Client: Acme Corp
   - Amount: $5,000.00
   - Line items:
     - Consulting Services (March 2026): $3,500.00
     - Software License: $1,500.00
   - Payment terms: Net 30
   - Due date: 2026-05-17

2. **Send Email Notification**
   - To: billing@acmecorp.com
   - Subject: Invoice #INV-2026-001 - Acme Corp
   - Body: Professional invoice notification with payment details
   - Attach: Invoice PDF (from Odoo)

3. **Record Accounting Entry**
   - Debit: Accounts Receivable - $5,000.00
   - Credit: Revenue - Consulting - $3,500.00
   - Credit: Revenue - Software - $1,500.00
   - Reference: INV-2026-001

4. **Update Dashboard**
   - Add to pending invoices list
   - Update revenue metrics
   - Log completion

### Success Criteria

- [ ] Invoice created in Odoo with correct details
- [ ] Email sent to client with invoice attached
- [ ] Accounting entry recorded with proper GL codes
- [ ] Dashboard updated with new invoice
- [ ] Task file moved to Done/ folder

### Notes

- This is a test of the Ralph Wiggum autonomous loop
- All steps should complete without manual intervention
- If approval required, file will be moved to Pending_Approval/
- Maximum 10 iterations before escalation
```

## Expected Behavior

### Iteration 1
- Ralph Wiggum detects new task file
- Reads task content and understands multi-step requirements
- Begins execution: Creates invoice in Odoo
- Logs action to daily log file
- Task remains in Needs_Action/ (incomplete)

### Iteration 2
- Ralph Wiggum re-checks task file (still in Needs_Action/)
- Continues execution: Sends email notification
- Logs action to daily log file
- Task remains in Needs_Action/ (incomplete)

### Iteration 3
- Ralph Wiggum re-checks task file
- Continues execution: Records accounting entry
- Logs action to daily log file
- Task remains in Needs_Action/ (incomplete)

### Iteration 4
- Ralph Wiggum re-checks task file
- Completes execution: Updates dashboard
- Moves task file to Done/ folder
- Logs completion
- Task state removed from active_tasks

### Final State
- Task file in `AI_Employee_Vault/Done/TASK_invoice_client_acme.md`
- All checkboxes marked [X] in task file
- Daily log contains all 4 iterations
- Dashboard shows new invoice
- Ralph Wiggum state file shows task completed

## Approval Gate Test

To test approval gate functionality, modify the task file to include:

```markdown
---
type: multi_step_task
priority: high
approval_required: true
---
```

### Expected Behavior with Approval Gate

1. Ralph Wiggum detects approval requirement
2. Creates `APPROVAL_REQUIRED_TASK_invoice_client_acme.md` in Needs_Action/
3. Task state changes to 'waiting_approval'
4. Ralph Wiggum pauses execution
5. Human moves approval file to Approved/
6. Ralph Wiggum detects approval and resumes execution
7. Task completes normally

## Escalation Test

To test escalation (max iterations exceeded):

1. Create a task that cannot be completed (e.g., invalid Odoo credentials)
2. Ralph Wiggum will retry up to 10 times
3. After 10 iterations, creates escalation file:
   - `ESCALATION_20260417_100000_TASK_invoice_client_acme.md`
4. Task state changes to 'escalated'
5. Human intervention required

## Verification Steps

### 1. Check Ralph Wiggum State
```bash
cat AI_Employee_Vault/Errors/ralph_wiggum_state.json
```

Expected:
```json
{
  "active_tasks": {},
  "processed_files": ["TASK_invoice_client_acme.md"],
  "last_updated": "2026-04-17T10:15:00Z"
}
```

### 2. Check Daily Logs
```bash
cat AI_Employee_Vault/Logs/2026-04-17.json
```

Expected: 4 entries with `action_type: "ralph_wiggum_execution"`

### 3. Check Task Completion
```bash
ls AI_Employee_Vault/Done/TASK_invoice_client_acme.md
```

Expected: File exists with all checkboxes marked [X]

### 4. Check Dashboard
```bash
cat AI_Employee_Vault/Dashboard.md
```

Expected: Shows new invoice in pending actions

## Performance Metrics

- **Total Time**: ~4-6 minutes (4 iterations × 60s check interval)
- **Iterations**: 4 (one per major step)
- **Success Rate**: 100% (all steps completed)
- **Human Intervention**: 0 (fully autonomous)

## Error Scenarios

### Scenario 1: Odoo Connection Failure
- Error recovery kicks in
- Exponential backoff retry (1s, 2s, 4s, 8s, 16s)
- If all retries fail, operation queued
- Ralph Wiggum continues with next step
- Queued operation retried when Odoo available

### Scenario 2: Email Send Failure
- Error recovery classifies as transient
- Retries with exponential backoff
- If max retries exceeded, creates alert file
- Ralph Wiggum continues with remaining steps

### Scenario 3: Invalid Task Format
- Ralph Wiggum logs error
- Creates escalation file immediately
- Task marked as 'escalated'
- Human intervention required

## Success Criteria

✅ Task file detected and processed automatically
✅ All 4 steps completed in sequence
✅ Task file moved to Done/ folder
✅ All checkboxes marked [X]
✅ Daily logs show all iterations
✅ Dashboard updated correctly
✅ No human intervention required
✅ State persisted correctly
✅ Error recovery handled gracefully

## Notes

- This test validates the core Gold tier capability: autonomous multi-step task completion
- Ralph Wiggum should handle the entire workflow without human intervention
- Approval gates and escalations provide safety mechanisms
- Error recovery ensures robustness against transient failures
- State persistence allows recovery from system restarts

## Future Enhancements

- Integration with actual Claude Code CLI (currently stubbed)
- Real-time progress updates in Dashboard
- Parallel task execution for independent tasks
- Machine learning for task prioritization
- Predictive escalation (detect likely failures early)
