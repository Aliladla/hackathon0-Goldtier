# Manual Test Plan - Bronze Tier Personal AI Employee

**Test Date**: 2026-04-16  
**Tester**: [Your Name]  
**Version**: Bronze Tier v1.0

## Prerequisites

- [ ] Python 3.13+ installed
- [ ] Obsidian installed
- [ ] Claude Code installed
- [ ] Repository cloned
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] .env file configured with correct VAULT_PATH

## Test Suite

### Test 1: System Initialization

**Objective**: Verify that the system initializes correctly and creates required vault structure.

**Steps**:
1. Delete AI_Employee_Vault folder if it exists
2. Run `python src/main.py`
3. Observe console output
4. Check that AI_Employee_Vault folder is created
5. Verify all subfolders exist: Inbox, Needs_Action, Done, Errors, Logs
6. Verify Dashboard.md and Company_Handbook.md are created
7. Press Ctrl+C to stop

**Expected Results**:
- Console shows "Personal AI Employee (Bronze Tier) Starting"
- All folders created successfully
- Dashboard.md exists with template content
- Company_Handbook.md exists with example rules
- System status shows "Active"
- No errors in console or logs

**Actual Results**:
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test 2: File Detection

**Objective**: Verify that the file watcher detects new files in Inbox folder.

**Steps**:
1. Start the system: `python src/main.py`
2. Wait for "System is now running" message
3. Create a test file: `echo "Test invoice" > AI_Employee_Vault/Inbox/test_invoice.txt`
4. Wait 30-35 seconds (check interval)
5. Check console output for "File detected" message
6. Check Needs_Action folder for new .md file
7. Open the created .md file and verify contents

**Expected Results**:
- Console shows "File detected: test_invoice.txt"
- Console shows "Created action item: FILE_test_invoice.txt_[timestamp].md"
- File appears in Needs_Action/ within 35 seconds
- .md file has correct YAML frontmatter (type, original_name, size, timestamp, status)
- .md file has "File Details" and "Suggested Actions" sections
- Log entry created in Logs/YYYY-MM-DD.log

**Actual Results**:
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test 3: Dashboard Updates

**Objective**: Verify that Dashboard.md updates with new activity.

**Steps**:
1. With system running, drop a file into Inbox/
2. Wait for file detection
3. Open AI_Employee_Vault/Dashboard.md in Obsidian
4. Check "Pending Actions" count
5. Check "Recent Activity" section
6. Verify timestamp is updated

**Expected Results**:
- Pending Actions count increases by 1
- Recent Activity shows "New file detected: [filename]"
- Last Updated timestamp is current
- System Status shows "Active"

**Actual Results**:
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test 4: Multiple Files

**Objective**: Verify that the system handles multiple files correctly.

**Steps**:
1. Start the system
2. Drop 3 different files into Inbox/ simultaneously:
   - test1.txt
   - test2.pdf
   - test3.docx
3. Wait 35 seconds
4. Check Needs_Action folder
5. Verify all 3 files are processed

**Expected Results**:
- 3 action items created in Needs_Action/
- Each has unique filename with timestamp
- No file overwrites or collisions
- Dashboard shows 3 pending actions
- All 3 files logged

**Actual Results**:
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test 5: Claude Code Integration - process_action

**Objective**: Verify that Claude Code can read action items and apply handbook rules.

**Steps**:
1. Ensure there are action items in Needs_Action/
2. Open terminal in AI_Employee_Vault directory
3. Run `claude code` (or open Claude Code)
4. Type `/process_action`
5. Review Claude's output

**Expected Results**:
- Claude reads all files in Needs_Action/
- Claude reads Company_Handbook.md
- Claude provides processing recommendations
- Claude references specific handbook rules
- Output is clear and actionable

**Actual Results**:
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test 6: Claude Code Integration - check_handbook

**Objective**: Verify that Claude Code can read and validate handbook rules.

**Steps**:
1. Open Claude Code in AI_Employee_Vault directory
2. Type `/check_handbook`
3. Review output

**Expected Results**:
- Claude reads Company_Handbook.md
- Claude displays all rules organized by category
- Claude validates rule format
- Claude provides suggestions if applicable

**Actual Results**:
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test 7: Claude Code Integration - update_dashboard

**Objective**: Verify that Claude Code can update Dashboard.md.

**Steps**:
1. Open Claude Code in AI_Employee_Vault directory
2. Type `/update_dashboard`
3. Check Dashboard.md for updates

**Expected Results**:
- Dashboard.md is updated with current counts
- Timestamp is refreshed
- Pending actions count is accurate
- No data loss in Recent Activity

**Actual Results**:
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test 8: Claude Code Integration - move_to_done

**Objective**: Verify that Claude Code can move completed items to Done folder.

**Steps**:
1. Note a filename in Needs_Action/ (e.g., FILE_test1.txt_20260416103000.md)
2. Open Claude Code in AI_Employee_Vault directory
3. Type `/move_to_done FILE_test1.txt_20260416103000.md`
4. Check that file moved from Needs_Action/ to Done/
5. Check Dashboard.md for updates

**Expected Results**:
- File successfully moved to Done/
- Completion timestamp added to frontmatter
- Dashboard updated with completion event
- Pending count decreased by 1

**Actual Results**:
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test 9: Error Handling - Invalid File

**Objective**: Verify that the system handles problematic files gracefully.

**Steps**:
1. Start the system
2. Create a file with special characters: `echo "test" > "AI_Employee_Vault/Inbox/test<>file.txt"`
3. Wait for processing
4. Check Errors folder and logs

**Expected Results**:
- System continues running (no crash)
- Error logged to Logs/
- Error report created in Errors/ (if applicable)
- Other files continue to be processed

**Actual Results**:
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test 10: Graceful Shutdown

**Objective**: Verify that the system shuts down cleanly.

**Steps**:
1. Start the system
2. Wait for "System is now running" message
3. Press Ctrl+C
4. Observe shutdown messages
5. Check Dashboard.md

**Expected Results**:
- Console shows "Shutdown signal received"
- Console shows "Shutdown complete"
- Dashboard.md System Status changes to "Inactive"
- No errors during shutdown
- All logs flushed to disk

**Actual Results**:
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test 11: Logging

**Objective**: Verify that all operations are logged correctly.

**Steps**:
1. Run the system for 5 minutes with various operations
2. Open Logs/YYYY-MM-DD.log
3. Review log entries

**Expected Results**:
- All events have timestamps
- Log levels are appropriate (INFO, WARNING, ERROR)
- Component names are included (Orchestrator, FileWatcher)
- File detection events logged
- Action item creation logged
- Errors logged with details

**Actual Results**:
- [ ] Pass
- [ ] Fail (describe issue):

---

### Test 12: 24-Hour Stability (Optional)

**Objective**: Verify that the system runs continuously without crashes.

**Steps**:
1. Start the system
2. Let it run for 24 hours
3. Periodically drop files into Inbox/
4. Check logs for errors
5. Verify system is still responsive

**Expected Results**:
- System runs for 24+ hours without crash
- All files processed correctly
- No memory leaks or performance degradation
- Logs show continuous operation

**Actual Results**:
- [ ] Pass
- [ ] Fail (describe issue):

---

## Test Summary

**Total Tests**: 12  
**Passed**: ___  
**Failed**: ___  
**Pass Rate**: ___%

## Issues Found

1. [Issue description]
2. [Issue description]

## Recommendations

1. [Recommendation]
2. [Recommendation]

## Sign-off

**Tester**: _______________  
**Date**: _______________  
**Status**: [ ] Approved for Bronze Tier [ ] Needs Fixes
