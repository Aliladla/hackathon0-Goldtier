# Odoo Integration Test Suite

**Purpose**: Comprehensive testing for Odoo ERP integration (User Story 2)

**Prerequisites**:
- Odoo instance (v16.0+) accessible
- Valid Odoo credentials configured in .env
- Python dependencies installed (odoorpc)
- AI Employee system running with ENABLE_ODOO=true

---

## Test 1: Invoice Creation (Vault → Odoo)

### Objective
Verify that invoice files created in the vault are automatically synced to Odoo with correct details.

### Setup

1. **Configure Odoo credentials** (.env):
   ```bash
   ENABLE_ODOO=true
   ODOO_URL=https://your-odoo-instance.com
   ODOO_DB=your_database
   ODOO_USERNAME=your_username
   ODOO_PASSWORD=your_password
   ```

2. **Start AI Employee system**:
   ```bash
   python src/main.py
   ```

3. **Verify Odoo connection**:
   ```
   Expected log output:
   ✓ Odoo client initialized and connected
   ```

### Test Scenario 1.1: Create Simple Invoice

**Step 1**: Create invoice file in vault

File: `AI_Employee_Vault/Accounting/Invoices/INVOICE_acme_001.md`

```markdown
---
type: invoice_request
customer_name: Acme Corp
customer_email: billing@acmecorp.com
payment_terms: 30
status: pending
---

## Invoice Request

**Customer**: Acme Corp
**Date**: 2026-04-17

### Line Items

1. Consulting Services: $3,500.00
2. Software License: $1,500.00

**Total**: $5,000.00
**Payment Terms**: Net 30
```

**Step 2**: Trigger invoice creation

Using Python:
```python
from integrations.odoo_client import create_odoo_client

odoo = create_odoo_client(vault_path="AI_Employee_Vault")
odoo.connect()

invoice = odoo.create_invoice(
    partner_name="Acme Corp",
    partner_email="billing@acmecorp.com",
    invoice_lines=[
        {"description": "Consulting Services", "quantity": 1, "unit_price": 3500.00},
        {"description": "Software License", "quantity": 1, "unit_price": 1500.00}
    ],
    payment_term_days=30,
    date_invoice="2026-04-17"
)

print(f"Invoice created: {invoice['name']}")
```

**Expected Result**:
```json
{
  "id": 123,
  "name": "INV/2026/0001",
  "partner_name": "Acme Corp",
  "amount_total": 5000.0,
  "state": "draft",
  "invoice_date": "2026-04-17",
  "invoice_date_due": "2026-05-17"
}
```

**Verification Steps**:

1. **Check Odoo UI**:
   - Navigate to Accounting → Customers → Invoices
   - Find invoice INV/2026/0001
   - Verify customer: Acme Corp
   - Verify amount: $5,000.00
   - Verify line items match
   - Verify due date: 2026-05-17

2. **Check vault file updated**:
   ```bash
   cat AI_Employee_Vault/Accounting/Invoices/INVOICE_acme_001.md
   ```
   
   Should contain:
   ```markdown
   odoo_invoice_id: 123
   odoo_invoice_number: INV/2026/0001
   status: created
   ```

3. **Check logs**:
   ```bash
   cat AI_Employee_Vault/Logs/2026-04-17.json | grep create_invoice
   ```

**Success Criteria**:
- ✅ Invoice created in Odoo with correct details
- ✅ Invoice number assigned (INV/2026/0001)
- ✅ Customer created/found in Odoo
- ✅ Line items match exactly
- ✅ Payment terms set correctly (Net 30)
- ✅ Due date calculated correctly
- ✅ Vault file updated with Odoo details
- ✅ Operation logged

### Test Scenario 1.2: Create Invoice with New Customer

**Test**: Create invoice for customer that doesn't exist in Odoo

**Expected Behavior**:
- OdooClient searches for customer by name
- If not found, creates new partner record
- Creates invoice linked to new partner
- Logs partner creation

**Verification**:
- Check Odoo Contacts for new customer
- Verify customer_rank = 1 (is customer)
- Verify email address set correctly

---

## Test 2: Payment Recording (Vault → Odoo)

### Objective
Verify that payment files created in the vault are recorded in Odoo and reconciled with invoices.

### Test Scenario 2.1: Record Full Payment

**Step 1**: Create payment file

File: `AI_Employee_Vault/Accounting/Payments/PAYMENT_acme_001.md`

```markdown
---
type: payment_received
invoice_number: INV/2026/0001
amount: 5000.00
payment_date: 2026-05-10
payment_method: bank_transfer
status: pending
---

## Payment Received

**Invoice**: INV/2026/0001
**Amount**: $5,000.00
**Date**: 2026-05-10
**Method**: Bank Transfer
**Reference**: TXN-20260510-001
```

**Step 2**: Record payment

```python
payment = odoo.record_payment(
    invoice_number="INV/2026/0001",
    amount=5000.00,
    payment_date="2026-05-10",
    payment_method="manual",
    memo="Bank Transfer - TXN-20260510-001"
)

print(f"Payment recorded: {payment['name']}")
```

**Expected Result**:
```json
{
  "id": 456,
  "name": "PAY/2026/0001",
  "amount": 5000.0,
  "date": "2026-05-10",
  "state": "posted",
  "invoice_number": "INV/2026/0001"
}
```

**Verification Steps**:

1. **Check Odoo UI**:
   - Navigate to Accounting → Customers → Payments
   - Find payment PAY/2026/0001
   - Verify amount: $5,000.00
   - Verify date: 2026-05-10
   - Verify state: Posted

2. **Check invoice reconciliation**:
   - Open invoice INV/2026/0001
   - Verify payment_state: "paid"
   - Verify payment linked to invoice
   - Check journal entries reconciled

3. **Check vault file updated**:
   ```markdown
   odoo_payment_id: 456
   odoo_payment_number: PAY/2026/0001
   status: recorded
   ```

**Success Criteria**:
- ✅ Payment created in Odoo
- ✅ Payment posted (not draft)
- ✅ Payment reconciled with invoice
- ✅ Invoice marked as paid
- ✅ Journal entries created and reconciled
- ✅ Vault file updated
- ✅ Operation logged

### Test Scenario 2.2: Record Partial Payment

**Test**: Record payment less than invoice total

**Expected Behavior**:
- Payment recorded for partial amount
- Invoice payment_state: "partial"
- Remaining balance tracked
- Can record additional payments

---

## Test 3: Bidirectional Sync (Odoo ↔ Vault)

### Objective
Verify that data syncs correctly in both directions between Odoo and vault.

### Test Scenario 3.1: Sync from Odoo to Vault

**Step 1**: Create invoices directly in Odoo UI
- Create 3 invoices manually in Odoo
- Date range: 2026-04-01 to 2026-04-30

**Step 2**: Sync from Odoo

```python
results = odoo.sync_from_odoo(
    date_from="2026-04-01",
    date_to="2026-04-30"
)

print(f"Synced {results['synced_invoices']} invoices")
```

**Expected Result**:
```json
{
  "direction": "from_odoo",
  "synced_invoices": 3,
  "synced_payments": 0,
  "errors": []
}
```

**Verification Steps**:

1. **Check vault directory**:
   ```bash
   ls AI_Employee_Vault/Accounting/Invoices/
   ```
   
   Should contain 3 new JSON files:
   - INV_2026_0001.json
   - INV_2026_0002.json
   - INV_2026_0003.json

2. **Check file contents**:
   ```bash
   cat AI_Employee_Vault/Accounting/Invoices/INV_2026_0001.json
   ```
   
   Should contain complete invoice data from Odoo

**Success Criteria**:
- ✅ All invoices in date range synced
- ✅ Invoice files created in vault
- ✅ Complete invoice data preserved
- ✅ No errors during sync
- ✅ Sync logged

### Test Scenario 3.2: Sync from Vault to Odoo

**Step 1**: Create queued operations

Simulate failed operations by creating entries in operation queue:

File: `AI_Employee_Vault/Errors/operation_queue.json`

```json
[
  {
    "type": "create_invoice",
    "partner_name": "Beta Inc",
    "partner_email": "billing@betainc.com",
    "invoice_lines": [
      {"description": "Service A", "quantity": 1, "unit_price": 2000.00}
    ],
    "queued_at": "2026-04-17T10:00:00Z",
    "retry_count": 0
  }
]
```

**Step 2**: Process queued operations

```python
results = odoo.sync_to_odoo()

print(f"Processed {results['synced_invoices']} queued invoices")
```

**Expected Result**:
```json
{
  "direction": "to_odoo",
  "synced_invoices": 1,
  "synced_payments": 0,
  "errors": []
}
```

**Verification Steps**:

1. **Check Odoo for new invoice**:
   - Find invoice for Beta Inc
   - Verify amount: $2,000.00

2. **Check operation queue cleared**:
   ```bash
   cat AI_Employee_Vault/Errors/operation_queue.json
   ```
   
   Should be empty: `[]`

**Success Criteria**:
- ✅ Queued operations processed
- ✅ Invoices created in Odoo
- ✅ Queue cleared after success
- ✅ No errors

### Test Scenario 3.3: Full Bidirectional Sync

**Test**: Run complete bidirectional sync

```python
results = odoo.bidirectional_sync(
    date_from="2026-04-01",
    date_to="2026-04-30"
)
```

**Expected Result**:
```json
{
  "direction": "bidirectional",
  "from_odoo": {
    "synced_invoices": 5,
    "synced_payments": 0,
    "errors": []
  },
  "to_odoo": {
    "synced_invoices": 1,
    "synced_payments": 0,
    "errors": []
  }
}
```

**Success Criteria**:
- ✅ Both directions sync successfully
- ✅ Vault and Odoo in sync
- ✅ No data loss
- ✅ No duplicate entries

---

## Test 4: Error Recovery with Odoo Offline

### Objective
Verify that error recovery handles Odoo offline scenarios gracefully with operation queuing.

### Test Scenario 4.1: Connection Timeout

**Step 1**: Simulate Odoo offline

Stop Odoo instance or block network access:
```bash
# Block Odoo URL in hosts file (Windows)
echo "127.0.0.1 your-odoo-instance.com" >> C:\Windows\System32\drivers\etc\hosts
```

**Step 2**: Attempt invoice creation

```python
try:
    invoice = odoo.create_invoice(
        partner_name="Gamma LLC",
        partner_email="billing@gammallc.com",
        invoice_lines=[
            {"description": "Product X", "quantity": 1, "unit_price": 1000.00}
        ]
    )
except Exception as e:
    print(f"Error: {e}")
```

**Expected Behavior**:

1. **Retry attempts** (exponential backoff):
   - Attempt 1: 1 second delay
   - Attempt 2: 2 seconds delay
   - Attempt 3: 4 seconds delay
   - Attempt 4: 8 seconds delay
   - Attempt 5: 16 seconds delay

2. **After max retries**:
   - Operation queued to operation_queue.json
   - Error logged to daily log file
   - Exception raised with clear message

**Verification Steps**:

1. **Check operation queue**:
   ```bash
   cat AI_Employee_Vault/Errors/operation_queue.json
   ```
   
   Should contain queued operation:
   ```json
   [
     {
       "type": "create_invoice",
       "partner_name": "Gamma LLC",
       "partner_email": "billing@gammallc.com",
       "invoice_lines": [...],
       "queued_at": "2026-04-17T11:00:00Z",
       "retry_count": 0
     }
   ]
   ```

2. **Check error log**:
   ```bash
   cat AI_Employee_Vault/Logs/2026-04-17.json | grep error
   ```
   
   Should contain error entry with:
   - error_type: "network"
   - error_message: "Connection timeout"
   - context: operation details

**Success Criteria**:
- ✅ 5 retry attempts with exponential backoff
- ✅ Operation queued after max retries
- ✅ Error logged with full context
- ✅ No data loss
- ✅ System continues running

### Test Scenario 4.2: Authentication Failure

**Step 1**: Use invalid credentials

Update .env with wrong password:
```bash
ODOO_PASSWORD=wrong_password
```

**Step 2**: Attempt connection

```python
odoo = create_odoo_client(vault_path="AI_Employee_Vault")
try:
    odoo.connect()
except Exception as e:
    print(f"Auth error: {e}")
```

**Expected Behavior**:

1. **Error classification**: AUTH error
2. **Alert file created**: `AUTH_ALERT_20260417_110000.md`
3. **No retries** (permanent error)
4. **Clear error message**

**Verification Steps**:

1. **Check alert file**:
   ```bash
   cat AI_Employee_Vault/Needs_Action/AUTH_ALERT_*.md
   ```
   
   Should contain:
   - Error message: "Odoo authentication failed"
   - Action steps: Update credentials
   - Services to check: Odoo

2. **Check error log**:
   - error_type: "auth"
   - error_class: "AuthError"

**Success Criteria**:
- ✅ Auth error detected immediately
- ✅ Alert file created in Needs_Action/
- ✅ No retry attempts (permanent error)
- ✅ Clear action steps provided
- ✅ Error logged

### Test Scenario 4.3: Recovery After Offline

**Step 1**: Restore Odoo connection

Remove hosts file block or restart Odoo instance.

**Step 2**: Process queued operations

```python
results = odoo.sync_to_odoo()
```

**Expected Behavior**:
- Queued operations processed successfully
- Invoices created in Odoo
- Queue cleared
- Success logged

**Verification Steps**:

1. **Check Odoo for queued invoices**:
   - Find invoice for Gamma LLC
   - Verify all details correct

2. **Check queue cleared**:
   ```bash
   cat AI_Employee_Vault/Errors/operation_queue.json
   ```
   
   Should be empty: `[]`

3. **Check success log**:
   - Operation type: "sync_to_odoo"
   - Synced invoices: 1
   - No errors

**Success Criteria**:
- ✅ Queued operations processed after recovery
- ✅ All data synced correctly
- ✅ Queue cleared
- ✅ No data loss during offline period
- ✅ System fully operational

---

## Test Summary

### Test Coverage

| Test | Scenario | Status |
|------|----------|--------|
| T061 | Invoice creation (vault → Odoo) | ⬜ |
| T061.1 | Simple invoice | ⬜ |
| T061.2 | New customer | ⬜ |
| T062 | Payment recording (vault → Odoo) | ⬜ |
| T062.1 | Full payment | ⬜ |
| T062.2 | Partial payment | ⬜ |
| T063 | Bidirectional sync | ⬜ |
| T063.1 | Odoo → Vault | ⬜ |
| T063.2 | Vault → Odoo | ⬜ |
| T063.3 | Full bidirectional | ⬜ |
| T064 | Error recovery | ⬜ |
| T064.1 | Connection timeout | ⬜ |
| T064.2 | Authentication failure | ⬜ |
| T064.3 | Recovery after offline | ⬜ |

### Success Metrics

**Functional Requirements**:
- ✅ Invoice creation works correctly
- ✅ Payment recording and reconciliation works
- ✅ Bidirectional sync maintains data consistency
- ✅ Error recovery handles all failure modes
- ✅ Operation queuing prevents data loss

**Non-Functional Requirements**:
- ✅ Response time < 5 seconds for invoice creation
- ✅ Retry logic completes within 30 seconds
- ✅ No data corruption during errors
- ✅ All operations logged
- ✅ Clear error messages

### Known Limitations

1. **MCP Server**: Node.js dependencies may fail to install (odoo-xmlrpc version issues)
   - **Workaround**: Use Python client directly (fully functional)
   - **Status**: Python client is production-ready

2. **Odoo Version**: Tested with Odoo 16.0+
   - **Note**: Older versions may have different API

3. **Concurrent Operations**: Not tested for race conditions
   - **Recommendation**: Use operation queue for serialization

### Next Steps

After completing these tests:

1. **Mark tasks complete** in tasks.md (T061-T064)
2. **Document test results** in this file
3. **Create production deployment guide**
4. **Move to User Story 3** (Social Media Automation)

---

**Test Environment**:
- Python: 3.13+
- Odoo: 16.0+
- odoorpc: 0.9.0+
- AI Employee: Gold Tier

**Last Updated**: 2026-04-17
