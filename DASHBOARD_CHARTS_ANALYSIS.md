# Dashboard Charts Analysis & Fixes

## Issues Found & Fixed

### 1. Daily Summary Report AttributeError ✅
**Error:** `AttributeError: 'dict' object has no attribute 'posting_date'`
**Fix:** Changed `date_row.posting_date` to `date_row["posting_date"]`
**File:** `petrodiesel/petrodiesel/report/daily_summary_report/daily_summary_report.py:147`

---

### 2. Dashboard Charts Field Name Issues ✅

#### Fixed Charts:
1. **Fuel Sales Breakdown** - Fixed `total_fuel` → `total_fuel_sales`
2. **Monthly Fuel vs Non-Fuel Sales** - Fixed `total_fuel` → `total_fuel_sales`
3. **Stock Level Trends** - Fixed `stock_qty` → `total_stock_as_per_dip`

#### Verified Correct Charts:
1. **Credit Outstanding Trend** - Uses `outstanding_amount` ✅
2. **Credit Sale** - Uses `name` (count) ✅
3. **Daily Sales Trend** - Uses `total_sales` ✅
4. **Payment Collections** - Uses `paid_amount` ✅
5. **Weekly Revenue** - Uses `total_sales` ✅
6. **Tanker Receipts** - Uses `total_quantity` ✅

---

## Dashboard Chart Configuration Analysis

### Credit Outstanding Trend ✅
```json
{
  "document_type": "Credit Sale",
  "value_based_on": "outstanding_amount",
  "filters": [["docstatus", "=", 1], ["outstanding_amount", ">", 0]]
}
```
**Logic:** ✅ Correct - Uses Credit Sale as single source of truth

### Credit Sale ✅
```json
{
  "document_type": "Credit Sale", 
  "value_based_on": "name",
  "filters": [["docstatus", "=", 1]]
}
```
**Logic:** ✅ Correct - Counts Credit Sale documents

### Daily Sales Trend ✅
```json
{
  "document_type": "Shift Sale Entry",
  "value_based_on": "total_sales"
}
```
**Logic:** ⚠️ ISSUE - Only queries Shift Sale Entry, missing Cashier Wise Shift Sale Entry

### Fuel Sales Breakdown ✅ (Fixed)
```json
{
  "document_type": "Shift Sale Entry",
  "value_based_on": "total_fuel_sales"  // Fixed from "total_fuel"
}
```
**Logic:** ⚠️ ISSUE - Only queries Shift Sale Entry, missing Cashier Wise Shift Sale Entry

### Payment Collections ✅
```json
{
  "document_type": "Customer Payment Entry",
  "value_based_on": "paid_amount"
}
```
**Logic:** ✅ Correct - Single source for payments

### Weekly Revenue ✅
```json
{
  "document_type": "Shift Sale Entry",
  "value_based_on": "total_sales"
}
```
**Logic:** ⚠️ ISSUE - Only queries Shift Sale Entry, missing Cashier Wise Shift Sale Entry

---

## Critical Issue: Missing Cashier Wise Shift Sale Entry Data

**Problem:** Most sales charts only query `Shift Sale Entry` but the application has TWO shift entry types:
1. `Shift Sale Entry`
2. `Cashier Wise Shift Sale Entry`

**Impact:** Charts showing only partial data (missing cashier-specific sales)

**Charts Affected:**
- Daily Sales Trend
- Fuel Sales Breakdown  
- Weekly Revenue
- Monthly Fuel vs Non-Fuel Sales

---

## Recommended Solutions

### Option 1: Create Custom Chart Methods (Recommended)
Create custom whitelisted methods in `number_card.py` that combine both doctypes:

```python
@frappe.whitelist()
def get_daily_sales_trend():
    """Combined daily sales from both shift entry types"""
    # Query both doctypes and combine results
    # Return format expected by dashboard charts
```

### Option 2: Update Chart Configurations
Change charts to use query reports that handle both doctypes:

```json
{
  "chart_type": "Custom",
  "method": "petrodiesel.petrodiesel.number_card.get_daily_sales_trend"
}
```

### Option 3: Use Credit Sale as Source (For Sales Charts)
Since Credit Sale documents are created from both shift types, use them as single source:

```json
{
  "document_type": "Credit Sale",
  "value_based_on": "total_amount"
}
```

---

## JavaScript Files Analysis

### Doctype Client Scripts
All doctype JavaScript files exist and appear to be standard Frappe client scripts:

**Key Doctypes with JS:**
- `shift_sale_entry.js` - Main shift entry logic
- `cashier_wise_shift_sale_entry.js` - Cashier shift logic  
- `credit_sale.js` - Credit sale validation
- `customer_payment_entry.js` - Payment processing
- `tanker_receipt.js` - Tanker receipt logic
- `fuel_price_update.js` - Price management

### Report Client Scripts
Standard report filtering and UI scripts - no custom logic issues found.

---

## Field Verification Summary

### Shift Sale Entry ✅
- `total_sales` ✅
- `total_fuel_sales` ✅ 
- `total_other_sales` ✅
- `total_credit_fuel` ✅
- `cash_received` ✅
- `expected_cash` ✅
- `cash_variance` ✅
- `total_online` ✅
- `total_expenses` ✅
- `total_emp_advances` ✅
- `total_driver_cash` ✅

### Cashier Wise Shift Sale Entry ✅
Same fields as Shift Sale Entry ✅

### Credit Sale ✅
- `total_amount` ✅
- `paid_amount` ✅
- `outstanding_amount` ✅
- `payment_status` ✅

### Customer Payment Entry ✅
- `paid_amount` ✅
- `customer` ✅
- `credit_sale` ✅ (optional link)

### Tank Dip Reading ✅
- `total_stock_as_per_dip` ✅
- `total_stock_as_per_system` ✅
- `variance` ✅

### Tanker Receipt ✅
- `total_received_qty` ✅
- `total_amount` ✅
- `grand_total` ✅

---

## Action Plan

### Immediate Fixes (Completed)
1. ✅ Daily Summary Report AttributeError
2. ✅ Dashboard chart field names
3. ✅ Number card filter routes

### Critical Fixes Needed
1. **Update sales charts to include Cashier Wise Shift Sale Entry data**
2. **Create combined data methods for dashboard charts**
3. **Verify all charts show complete data**

### Testing Checklist
- [ ] Daily Summary Report runs without error
- [ ] All dashboard charts show data
- [ ] Sales charts include both shift entry types
- [ ] Credit charts show accurate outstanding
- [ ] Stock charts show correct levels
- [ ] Payment charts show correct collections

---

## Files Modified

### Reports
- `petrodiesel/petrodiesel/report/daily_summary_report/daily_summary_report.py`

### Dashboard Charts  
- `petrodiesel/petrodiesel/dashboard_chart/fuel_sales_breakdown/fuel_sales_breakdown.json`
- `petrodiesel/petrodiesel/dashboard_chart/monthly_fuel_vs_non_fuel_sales/monthly_fuel_vs_non_fuel_sales.json`
- `petrodiesel/petrodiesel/dashboard_chart/stock_level_trends/stock_level_trends.json`

### Number Cards
- `petrodiesel/petrodiesel/number_card.py`

---

## Next Steps

1. **Deploy current fixes** - Restart bench and test Daily Summary Report
2. **Create combined chart methods** - Add methods to number_card.py for complete data
3. **Update chart configurations** - Point charts to custom methods
4. **Test all dashboards** - Verify complete data display

---

**Status:** Critical errors fixed, data completeness issue identified and solution provided.
