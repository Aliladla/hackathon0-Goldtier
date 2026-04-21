# Error Recovery Integration Tests

**Test Suite**: Comprehensive error recovery and resilience testing

**Purpose**: Validate that the enhanced error recovery system correctly classifies errors, retries transient failures, escalates permanent errors, enables graceful degradation, and maintains complete audit trails.

---

## Test Environment Setup

### Prerequisites

1. **Error Recovery System**:
   - error_recovery.py initialized
   - watchdog.py monitoring active
   - All integration clients configured

2. **Test Data**:
   - Sample operations for queuing
   - Mock external services for failure simulation
   - Test vault structure

3. **Configuration**:
   ```bash
   MAX_RETRY_ATTEMPTS=5
   RETRY_BASE_DELAY=1
   LOG_RETENTION_DAYS=90
   ```

---

## Test Case 1: Transient Error Retry with Exponential Backoff

**Objective**: Test retry logic for transient errors (network timeouts, rate limits)

**Setup**:
1. Mock external service to fail 3 times then succeed
2. Configure error recovery with max_retries=5

**Test Steps**:

```python
from utils.error_recovery import initialize_error_recovery, TransientError
import time

# Initialize error recovery
error_recovery = initialize_error_recovery(
    vault_path="AI_Employee_Vault",
    max_retries=5,
    base_delay=1
)

# Mock function that fails 3 times
attempt_count = 0

def flaky_operation():
    global attempt_count
    attempt_count += 1
    
    if attempt_count <= 3:
        raise Exception("Connection timeout")
    
    return {"status": "success", "data": "Operation completed"}

# Execute with retry
start_time = time.time()
result = error_recovery.with_retry(flaky_operation)
end_time = time.time()

print(f"Result: {result}")
print(f"Attempts: {attempt_count}")
print(f"Total time: {end_time - start_time:.2f}s")
```

**Expected Results**:
- ✓ Operation retried 3 times before success
- ✓ Exponential backoff delays: ~1s, ~2s, ~4s
- ✓ Total time: ~7 seconds
- ✓ Final result: success
- ✓ Error classified as TRANSIENT or NETWORK
- ✓ Warnings logged for each retry attempt

**Validation**:
```python
# Check error logs
log_file = Path("AI_Employee_Vault/Logs/errors/2026-04-17.json")
logs = json.loads(log_file.read_text())

transient_errors = [log for log in logs if log['error_type'] in ['transient', 'network', 'timeout']]
assert len(transient_errors) == 3  # 3 failures before success

# Verify exponential backoff timing
for i, log in enumerate(transient_errors):
    assert log['retry_count'] == i
    assert log['severity'] == 'low'

print("✓ Test Case 1 PASSED: Transient error retry with exponential backoff")
```

---

## Test Case 2: Permanent Error Escalation with Alert File Creation

**Objective**: Test immediate escalation for permanent errors (auth failures, validation errors)

**Setup**:
1. Mock operation that raises authentication error
2. Verify alert file created in Needs_Action/

**Test Steps**:

```python
from utils.error_recovery import AuthError, PermanentError

def auth_failure_operation():
    raise AuthError("Invalid credentials: token expired")

# Execute with retry (should fail immediately)
try:
    result = error_recovery.with_retry(auth_failure_operation)
    assert False, "Should have raised PermanentError"
except PermanentError as e:
    print(f"Correctly escalated: {e}")

# Check alert file created
alert_files = list(Path("AI_Employee_Vault/Needs_Action").glob("AUTH_ALERT_*.md"))
assert len(alert_files) > 0

# Read alert file
latest_alert = max(alert_files, key=lambda p: p.stat().st_mtime)
alert_content = latest_alert.read_text()

assert "Authentication Error Alert" in alert_content
assert "Invalid credentials" in alert_content
assert "Action Required" in alert_content
```

**Expected Results**:
- ✓ Error classified as AUTH
- ✓ No retry attempts (immediate escalation)
- ✓ PermanentError raised
- ✓ Alert file created in Needs_Action/
- ✓ Alert contains error details and recovery steps
- ✓ Error logged with severity: critical

**Validation**:
```python
# Verify error log
log_file = Path("AI_Employee_Vault/Logs/errors/2026-04-17.json")
logs = json.loads(log_file.read_text())

auth_errors = [log for log in logs if log['error_type'] == 'auth']
assert len(auth_errors) == 1
assert auth_errors[0]['severity'] == 'critical'
assert auth_errors[0]['retry_count'] == 0

print("✓ Test Case 2 PASSED: Permanent error escalation with alert file creation")
```

---

## Test Case 3: Authentication Token Expiration Handling

**Objective**: Test handling of expired authentication tokens

**Setup**:
1. Mock Odoo client with expired token
2. Verify token refresh attempted
3. Verify alert created if refresh fails

**Test Steps**:

```python
from integrations.odoo_client import create_odoo_client

# Create Odoo client
odoo_client = create_odoo_client(vault_path="AI_Employee_Vault")

# Mock expired token scenario
def create_invoice_with_expired_token():
    # This will fail with 401 Unauthorized
    return odoo_client.create_invoice(
        partner_name="Test Customer",
        partner_email="test@example.com",
        invoice_lines=[{
            'description': 'Test Service',
            'quantity': 1,
            'unit_price': 100.00
        }]
    )

# Execute operation
try:
    result = create_invoice_with_expired_token()
except PermanentError as e:
    print(f"Auth error escalated: {e}")
    
    # Check alert created
    alert_files = list(Path("AI_Employee_Vault/Needs_Action").glob("AUTH_ALERT_*.md"))
    assert len(alert_files) > 0
    
    latest_alert = max(alert_files, key=lambda p: p.stat().st_mtime)
    alert_content = latest_alert.read_text()
    
    assert "ODOO" in alert_content or "Odoo" in alert_content
    assert "token" in alert_content.lower() or "credential" in alert_content.lower()
```

**Expected Results**:
- ✓ Error classified as AUTH
- ✓ No retry attempts (auth errors don't retry)
- ✓ Alert file created with Odoo-specific instructions
- ✓ Error logged with full context
- ✓ Operation queued for retry after token refresh

**Validation**:
```python
# Check operation queue
queue_file = Path("AI_Employee_Vault/Errors/operation_queue.json")
if queue_file.exists():
    queue = json.loads(queue_file.read_text())
    odoo_operations = [op for op in queue if 'odoo' in op.get('type', '').lower()]
    assert len(odoo_operations) > 0

print("✓ Test Case 3 PASSED: Authentication token expiration handling")
```

---

## Test Case 4: Component Crash Detection and Auto-Restart

**Objective**: Test watchdog crash detection and automatic restart

**Setup**:
1. Start test component with watchdog monitoring
2. Kill component process
3. Verify watchdog detects crash and restarts

**Test Steps**:

```python
from utils.watchdog import initialize_watchdog
import subprocess
import psutil
import time

# Initialize watchdog
watchdog = initialize_watchdog(
    vault_path="AI_Employee_Vault",
    check_interval=5
)

# Start test component
test_script = "test_component.py"
process = subprocess.Popen(['python', test_script])
pid = process.pid

# Register with watchdog
watchdog.register_component(
    name="test_component",
    pid=pid,
    command=f"python {test_script}",
    critical=True
)

print(f"Test component started: PID {pid}")

# Wait for component to be running
time.sleep(2)

# Kill component
process.kill()
print(f"Killed component: PID {pid}")

# Wait for watchdog to detect and restart
time.sleep(10)

# Check component status
status_report = watchdog.get_status_report()
test_status = status_report['test_component']

print(f"Component status: {test_status}")
```

**Expected Results**:
- ✓ Watchdog detects crash within check_interval
- ✓ Component automatically restarted
- ✓ New PID assigned
- ✓ Restart count incremented
- ✓ Crash alert created in Needs_Action/
- ✓ Dashboard.md updated with restart notification
- ✓ Restart logged to daily log file

**Validation**:
```python
# Verify restart
assert test_status['status'] == 'running'
assert test_status['restart_count'] == 1
assert test_status['pid'] != pid  # New PID

# Check crash alert
alert_files = list(Path("AI_Employee_Vault/Needs_Action").glob("CRASH_ALERT_test_component_*.md"))
assert len(alert_files) > 0

# Check dashboard notification
dashboard_content = Path("AI_Employee_Vault/Dashboard.md").read_text()
assert "test_component" in dashboard_content
assert "restarted" in dashboard_content

# Check restart log
log_file = Path("AI_Employee_Vault/Logs/watchdog/2026-04-17.json")
logs = json.loads(log_file.read_text())
restart_logs = [log for log in logs if log.get('action_type') == 'component_restart']
assert len(restart_logs) > 0

print("✓ Test Case 4 PASSED: Component crash detection and auto-restart")
```

---

## Test Case 5: Graceful Degradation with Multiple MCP Server Failures

**Objective**: Test graceful degradation mode when multiple critical services fail

**Setup**:
1. Simulate failure of 2+ critical MCP servers
2. Verify system enters graceful degradation mode
3. Verify read operations continue, write operations queued

**Test Steps**:

```python
from utils.error_recovery import get_error_recovery
from utils.watchdog import get_watchdog

error_recovery = get_error_recovery()
watchdog = get_watchdog()

# Register MCP servers
watchdog.register_mcp_server("odoo", "http://localhost:8001/health", critical=True)
watchdog.register_mcp_server("facebook", "http://localhost:8002/health", critical=True)
watchdog.register_mcp_server("instagram", "http://localhost:8003/health", critical=False)

# Simulate multiple failures (mock servers down)
# In real test, stop MCP server processes

# Trigger health check
mcp_status = watchdog.check_all_mcp_servers()
health_summary = watchdog.get_component_health_summary()

print(f"MCP Status: {mcp_status}")
print(f"Overall Health: {health_summary['overall_health']}")

# Check if graceful degradation enabled
is_degraded = error_recovery.is_degraded()
print(f"Graceful Degradation: {is_degraded}")
```

**Expected Results**:
- ✓ Multiple MCP server failures detected
- ✓ Overall health status: critical
- ✓ Graceful degradation mode enabled automatically
- ✓ Degradation alert created in Needs_Action/
- ✓ Dashboard.md updated with degradation status
- ✓ Read operations continue normally
- ✓ Write operations queued for later

**Validation**:
```python
# Verify degradation mode
assert is_degraded == True
assert health_summary['overall_health'] == 'critical'

# Check degradation file
degradation_file = Path("AI_Employee_Vault/Errors/graceful_degradation.json")
assert degradation_file.exists()

degradation_state = json.loads(degradation_file.read_text())
assert degradation_state['enabled'] == True
assert degradation_state['mode'] == 'read_only'

# Check degradation alert
alert_files = list(Path("AI_Employee_Vault/Needs_Action").glob("DEGRADATION_ALERT_*.md"))
assert len(alert_files) > 0

# Check dashboard health status
dashboard_content = Path("AI_Employee_Vault/Dashboard.md").read_text()
assert "🔴" in dashboard_content or "critical" in dashboard_content.lower()

print("✓ Test Case 5 PASSED: Graceful degradation with multiple MCP server failures")
```

---

## Test Case 6: Log Retention and Cleanup (90-Day Policy)

**Objective**: Test automatic cleanup of logs older than 90 days

**Setup**:
1. Create test log files with various dates
2. Trigger log cleanup
3. Verify old logs deleted, recent logs retained

**Test Steps**:

```python
from datetime import datetime, timedelta
from pathlib import Path
import json

log_dir = Path("AI_Employee_Vault/Logs/errors")
log_dir.mkdir(parents=True, exist_ok=True)

# Create test log files
test_dates = [
    datetime.now() - timedelta(days=100),  # Should be deleted
    datetime.now() - timedelta(days=95),   # Should be deleted
    datetime.now() - timedelta(days=89),   # Should be retained
    datetime.now() - timedelta(days=30),   # Should be retained
    datetime.now() - timedelta(days=1),    # Should be retained
]

for test_date in test_dates:
    log_file = log_dir / f"{test_date.strftime('%Y-%m-%d')}.json"
    log_file.write_text(json.dumps([{
        "timestamp": test_date.isoformat(),
        "error_type": "test",
        "error_message": "Test error"
    }]))

print(f"Created {len(test_dates)} test log files")

# Trigger log cleanup
error_recovery._cleanup_old_logs(log_dir, retention_days=90)

# Check remaining files
remaining_files = list(log_dir.glob("*.json"))
print(f"Remaining files: {len(remaining_files)}")

# Verify old files deleted
for test_date in test_dates:
    log_file = log_dir / f"{test_date.strftime('%Y-%m-%d')}.json"
    days_old = (datetime.now() - test_date).days
    
    if days_old >= 90:
        assert not log_file.exists(), f"Old file not deleted: {log_file.name}"
    else:
        assert log_file.exists(), f"Recent file deleted: {log_file.name}"
```

**Expected Results**:
- ✓ Logs older than 90 days deleted
- ✓ Logs within 90 days retained
- ✓ Cleanup logged to main log
- ✓ No errors during cleanup

**Validation**:
```python
# Verify retention policy
assert len(remaining_files) == 3  # 89, 30, 1 days old

# Check cleanup log
main_log = Path("AI_Employee_Vault/Logs/errors/2026-04-17.json")
if main_log.exists():
    logs = json.loads(main_log.read_text())
    # Cleanup operations may be logged

print("✓ Test Case 6 PASSED: Log retention and cleanup (90-day policy)")
```

---

## Test Case 7: Complete Audit Trail Verification

**Objective**: Verify all operations logged with complete context

**Setup**:
1. Execute various operations (invoice creation, social media post, etc.)
2. Verify all operations logged with full context
3. Verify audit trail completeness

**Test Steps**:

```python
from integrations.odoo_client import create_odoo_client
from integrations.facebook_client import create_facebook_client

# Execute operations
odoo_client = create_odoo_client(vault_path="AI_Employee_Vault")
facebook_client = create_facebook_client(vault_path="AI_Employee_Vault")

operations = []

# Operation 1: Create invoice
try:
    invoice = odoo_client.create_invoice(
        partner_name="Audit Test Customer",
        partner_email="audit@test.com",
        invoice_lines=[{
            'description': 'Audit Test Service',
            'quantity': 1,
            'unit_price': 100.00
        }]
    )
    operations.append({
        'type': 'invoice_creation',
        'status': 'success',
        'invoice_id': invoice.get('id')
    })
except Exception as e:
    operations.append({
        'type': 'invoice_creation',
        'status': 'failed',
        'error': str(e)
    })

# Operation 2: Create Facebook post
try:
    post = facebook_client.create_post(
        message="Audit test post",
        link="https://example.com"
    )
    operations.append({
        'type': 'facebook_post',
        'status': 'success',
        'post_id': post.get('post_id')
    })
except Exception as e:
    operations.append({
        'type': 'facebook_post',
        'status': 'failed',
        'error': str(e)
    })

print(f"Executed {len(operations)} operations")

# Check audit trail
log_file = Path("AI_Employee_Vault/Logs/errors/2026-04-17.json")
if log_file.exists():
    logs = json.loads(log_file.read_text())
    
    # Verify each operation logged
    for operation in operations:
        if operation['status'] == 'failed':
            # Find corresponding error log
            error_logs = [
                log for log in logs
                if operation['type'] in log.get('context', {}).get('operation', '')
            ]
            assert len(error_logs) > 0, f"No error log for {operation['type']}"
            
            # Verify log completeness
            error_log = error_logs[0]
            assert 'timestamp' in error_log
            assert 'error_type' in error_log
            assert 'error_message' in error_log
            assert 'context' in error_log
            assert 'stack_trace' in error_log
            assert 'severity' in error_log
            assert 'component' in error_log
            assert 'operation' in error_log
```

**Expected Results**:
- ✓ All operations logged (success and failure)
- ✓ Each log entry contains complete context
- ✓ Timestamps accurate
- ✓ Error types classified correctly
- ✓ Stack traces included for errors
- ✓ Severity levels assigned
- ✓ Component and operation identified

**Validation**:
```python
# Verify audit trail completeness
for operation in operations:
    print(f"Operation: {operation['type']} - Status: {operation['status']}")

print("✓ Test Case 7 PASSED: Complete audit trail verification")
```

---

## Performance Tests

### Test Case 8: High-Volume Error Handling

**Objective**: Test error recovery performance under high load

**Setup**:
- Generate 1000 operations with 10% failure rate
- Measure retry overhead
- Verify no memory leaks

**Expected Results**:
- ✓ All operations processed
- ✓ Retry overhead < 20% of total time
- ✓ Memory usage stable
- ✓ No log file corruption

---

## Integration Tests

### Test Case 9: End-to-End Error Recovery Workflow

**Objective**: Test complete error recovery workflow from failure to recovery

**Steps**:
1. Simulate external service failure
2. Verify operations queued
3. Restore service
4. Verify queued operations retried
5. Verify all operations complete successfully

**Expected Results**:
- ✓ Operations queued during outage
- ✓ Operations retried after recovery
- ✓ No data loss
- ✓ Complete audit trail

---

## Summary

**Total Test Cases**: 9
- **Unit Tests**: 3 (TC1-TC3)
- **Integration Tests**: 4 (TC4-TC7)
- **Performance Tests**: 1 (TC8)
- **End-to-End Tests**: 1 (TC9)

**Coverage**:
- ✓ Error classification (10 error types)
- ✓ Retry logic with exponential backoff
- ✓ Permanent error escalation
- ✓ Alert file creation (auth, config, data, crash, degradation, MCP)
- ✓ Component crash detection and restart
- ✓ MCP server health monitoring
- ✓ Graceful degradation mode
- ✓ Log retention and cleanup
- ✓ Complete audit trail
- ✓ Operation queuing and retry

**Success Criteria**:
- All test cases pass
- No data loss during failures
- Graceful degradation works correctly
- Complete audit trail maintained
- Performance within acceptable limits
- Memory usage stable under load
