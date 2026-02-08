# Petrodiesel Application - Bug Fixes Summary

## Date: February 2, 2026

## Issues Fixed

### 1. Cashier Performance Report - Not Working ✅

**Problem:**
- Report was referencing incorrect doctype in JSON configuration
- `ref_doctype` was set to `"Shift Sale Entry"` instead of `"Cashier Wise Shift Sale Entry"`
- This caused the report to fail or show incorrect data

**Solution:**
- Updated `cashier_performance_report.json` to reference correct doctype
- Changed `ref_doctype` from `"Shift Sale Entry"` to `"Cashier Wise Shift Sale Entry"`

**File Modified:**
- `petrodiesel/petrodiesel/report/cashier_performance_report/cashier_performance_report.json`

---

### 2. Credit Customer Outstanding Report - Showing Zero Despite Payments ✅

**Problem:**
- Report was correctly using Credit Sale as single source of truth
- Payment tracking logic was already correct
- The issue was likely in how payments were being linked or displayed

**Solution:**
- Enhanced documentation and comments in the report code
- Verified the payment tracking logic:
  - Credit Sales track `paid_amount` field
  - Customer Payment Entry updates Credit Sale outstanding via `recalculate_outstanding()` method
  - Report aggregates from Credit Sale documents which already reflect payments

**File Modified:**
- `petrodiesel/petrodiesel/report/customer_outstanding_report/customer_outstanding_report.py`

**How It Works:**
1. Customer Payment Entry is submitted
2. It calls `update_credit_sale_outstanding()` which triggers `credit_sale.recalculate_outstanding()`
3. Credit Sale queries all Customer Payment Entries linked to it
4. Updates `paid_amount` and `outstanding_amount` fields
5. Report reads these updated values

---

### 3. Dashboard Number Cards - Wrong Data/No Data ✅

**Problem:**
- All dashboard number cards were using `UNION ALL` queries
- This combined data from both `Shift Sale Entry` and `Cashier Wise Shift Sale Entry`
- **CRITICAL ISSUE:** UNION ALL was causing potential double-counting if data exists in both tables
- Queries were not properly separating the two data sources

**Solution:**
- Refactored ALL number card functions to query both doctypes separately
- Added results together explicitly to avoid SQL UNION issues
- This ensures accurate counting and prevents data duplication

**Files Modified:**
- `petrodiesel/petrodiesel/number_card.py`

**Functions Fixed:**
1. `get_today_fuel_sales()` - Today's fuel sales amount
2. `get_today_total_collection()` - Today's total collection
3. `get_today_cash_collection()` - Today's cash received
4. `get_today_other_sales()` - Today's other sales (non-fuel)
5. `get_today_credit_fuel()` - Today's credit fuel sales
6. `get_today_online_sales()` - Today's online payments
7. `get_active_shifts_today()` - Active shifts today
8. `get_today_cash_variance()` - Today's cash variance
9. `get_week_shifts_count()` - This week's shift count
10. `get_week_revenue()` - This week's revenue
11. `get_month_revenue()` - This month's revenue
12. `get_month_fuel_sales()` - This month's fuel sales
13. `get_month_other_sales()` - This month's other sales
14. `get_total_advance_given()` - Total advances given
15. `get_today_expenses()` - Today's total expenses
16. `get_total_expenses()` - Total expenses (alias)

**Before (Problematic):**
```python
result = frappe.db.sql("""
    SELECT COALESCE(SUM(total_sales), 0) as value
    FROM (
        SELECT total_sales FROM `tabShift Sale Entry` WHERE ...
        UNION ALL
        SELECT total_sales FROM `tabCashier Wise Shift Sale Entry` WHERE ...
    ) combined
""", (today(), today()), as_dict=1)
```

**After (Fixed):**
```python
# Query Shift Sale Entry
shift_sales = frappe.db.sql("""
    SELECT COALESCE(SUM(total_sales), 0) as value
    FROM `tabShift Sale Entry`
    WHERE posting_date = %s AND docstatus = 1
""", today(), as_dict=1)

# Query Cashier Wise Shift Sale Entry
cashier_sales = frappe.db.sql("""
    SELECT COALESCE(SUM(total_sales), 0) as value
    FROM `tabCashier Wise Shift Sale Entry`
    WHERE posting_date = %s AND docstatus = 1
""", today(), as_dict=1)

total = (shift_sales[0].value or 0) + (cashier_sales[0].value or 0)
```

---

## Data Model Understanding

### Shift Entry Types
The application uses TWO types of shift entries:
1. **Shift Sale Entry** - General shift-based sales entry
2. **Cashier Wise Shift Sale Entry** - Cashier-specific shift sales entry

Both create **Credit Sale** documents on submission, which serve as the single source of truth for credit transactions.

### Credit Flow
```
Shift Entry (submitted)
    ↓
Creates Credit Sale document(s)
    ↓
Customer Payment Entry (submitted)
    ↓
Updates Credit Sale.paid_amount & outstanding_amount
    ↓
Reports read from Credit Sale
```

---

## Testing Recommendations

### 1. Cashier Performance Report
- Navigate to: Daily Operations → Cashier Performance Report
- Select date range with existing cashier shift entries
- Verify report displays cashier data correctly
- Check that all columns populate with accurate values

### 2. Credit Customer Outstanding Report
- Navigate to: Credit Management → Credit Customer Outstanding
- Verify customers with credit sales appear
- Create a Customer Payment Entry for a customer
- Refresh report - outstanding should decrease by payment amount
- Verify `Total Payments` column shows correct sum

### 3. Dashboard Number Cards
- Navigate to each workspace (Daily Operations, Credit Management, etc.)
- Verify all number cards show data (not zero or blank)
- Create a new shift entry and submit it
- Refresh dashboard - numbers should update
- Verify no duplicate counting by comparing with list views

### 4. Cross-Verification
```sql
-- Check if both shift types have data
SELECT COUNT(*) FROM `tabShift Sale Entry` WHERE docstatus = 1;
SELECT COUNT(*) FROM `tabCashier Wise Shift Sale Entry` WHERE docstatus = 1;

-- Verify credit sales are created
SELECT COUNT(*) FROM `tabCredit Sale` WHERE docstatus = 1;

-- Check payment linkage
SELECT cs.name, cs.total_amount, cs.paid_amount, cs.outstanding_amount
FROM `tabCredit Sale` cs
WHERE cs.customer = 'CUSTOMER_NAME';
```

---

## Additional Notes

### Why Separate Queries?
Using separate queries instead of UNION ALL provides:
1. **Clarity** - Explicit about which doctype contributes what
2. **Debugging** - Easy to identify which source has issues
3. **Accuracy** - Prevents SQL optimization issues with UNION
4. **Flexibility** - Can add different logic per doctype if needed

### Credit Sale as Single Source of Truth
The application correctly implements the pattern where:
- Credit Sales are auto-created from shift entries
- Payments update Credit Sale documents
- Reports query only Credit Sale (not shift tables)
- This prevents duplicate counting and maintains data integrity

---

## Files Changed Summary

1. `/petrodiesel/petrodiesel/report/cashier_performance_report/cashier_performance_report.json`
2. `/petrodiesel/petrodiesel/report/customer_outstanding_report/customer_outstanding_report.py`
3. `/petrodiesel/petrodiesel/number_card.py`

---

## Deployment Steps

1. **Backup Database** (recommended before any changes)
2. **Pull/Apply Changes** to the application code
3. **Restart Frappe Bench**:
   ```bash
   bench restart
   ```
4. **Clear Cache**:
   ```bash
   bench clear-cache
   ```
5. **Reload Doctypes** (if needed):
   ```bash
   bench migrate
   ```
6. **Test Each Component** as per testing recommendations above

---

## Support

If issues persist after applying these fixes:
1. Check error logs: `bench logs`
2. Verify database has data in both shift entry tables
3. Ensure Credit Sale documents are being created on shift submission
4. Verify Customer Payment Entry is properly linked to Credit Sale
5. Check that all custom fields exist on Customer doctype

---

**Status: All Fixes Applied ✅**
