# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, get_first_day, getdate, add_days, nowdate

# ============================================================================
# DAILY OPERATIONS - TODAY'S METRICS
# ============================================================================

@frappe.whitelist()
def get_today_fuel_sales():
    """Today's fuel sales amount - from both shift entry types"""
    # Query Shift Sale Entry
    shift_sales = frappe.db.sql("""
        SELECT COALESCE(SUM(total_fuel_sales), 0) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_sales = frappe.db.sql("""
        SELECT COALESCE(SUM(total_fuel_sales), 0) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    total = (shift_sales[0].value or 0) + (cashier_sales[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_today_total_collection():
    """Today's total collection - from both shift entry types"""
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
    
    return {
        "value": total,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_today_cash_collection():
    """Today's cash received - from both shift entry types"""
    # Query Shift Sale Entry
    shift_cash = frappe.db.sql("""
        SELECT COALESCE(SUM(cash_received), 0) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_cash = frappe.db.sql("""
        SELECT COALESCE(SUM(cash_received), 0) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    total = (shift_cash[0].value or 0) + (cashier_cash[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_today_other_sales():
    """Today's other sales (non-fuel) - from both shift entry types"""
    # Query Shift Sale Entry
    shift_other = frappe.db.sql("""
        SELECT COALESCE(SUM(total_other_sales), 0) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_other = frappe.db.sql("""
        SELECT COALESCE(SUM(total_other_sales), 0) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    total = (shift_other[0].value or 0) + (cashier_other[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_today_credit_fuel():
    """Today's credit fuel sales - from both shift entry types"""
    # Query Shift Sale Entry
    shift_credit = frappe.db.sql("""
        SELECT COALESCE(SUM(total_credit_fuel), 0) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_credit = frappe.db.sql("""
        SELECT COALESCE(SUM(total_credit_fuel), 0) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    total = (shift_credit[0].value or 0) + (cashier_credit[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_today_online_sales():
    """Today's online payments - from both shift entry types"""
    # Query Shift Sale Entry
    shift_online = frappe.db.sql("""
        SELECT COALESCE(SUM(total_online), 0) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_online = frappe.db.sql("""
        SELECT COALESCE(SUM(total_online), 0) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    total = (shift_online[0].value or 0) + (cashier_online[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_active_shifts_today():
    """Active shifts today - from both shift entry types"""
    # Query Shift Sale Entry
    shift_count = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s
    """, today(), as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_count = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date = %s
    """, today(), as_dict=1)
    
    total = (shift_count[0].value or 0) + (cashier_count[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Int",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_today_cash_variance():
    """Today's cash variance - from both shift entry types"""
    # Query Shift Sale Entry
    shift_variance = frappe.db.sql("""
        SELECT COALESCE(SUM(cash_variance), 0) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_variance = frappe.db.sql("""
        SELECT COALESCE(SUM(cash_variance), 0) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    total = (shift_variance[0].value or 0) + (cashier_variance[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

# ============================================================================
# WEEKLY METRICS
# ============================================================================

@frappe.whitelist()
def get_week_shifts_count():
    """This week's shift count - from both shift entry types"""
    week_start = add_days(today(), -7)
    
    # Query Shift Sale Entry
    shift_count = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, week_start, as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_count = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, week_start, as_dict=1)
    
    total = (shift_count[0].value or 0) + (cashier_count[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Int",
        "route": ["List", "Shift Sale Entry"]
    }

@frappe.whitelist()
def get_week_revenue():
    """This week's revenue - from both shift entry types"""
    week_start = add_days(today(), -7)
    
    # Query Shift Sale Entry
    shift_revenue = frappe.db.sql("""
        SELECT COALESCE(SUM(total_sales), 0) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, week_start, as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_revenue = frappe.db.sql("""
        SELECT COALESCE(SUM(total_sales), 0) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, week_start, as_dict=1)
    
    total = (shift_revenue[0].value or 0) + (cashier_revenue[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry"]
    }

# ============================================================================
# MONTHLY METRICS
# ============================================================================

@frappe.whitelist()
def get_month_revenue():
    """This month's revenue - from both shift entry types"""
    month_start = get_first_day(today())
    
    # Query Shift Sale Entry
    shift_revenue = frappe.db.sql("""
        SELECT COALESCE(SUM(total_sales), 0) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_revenue = frappe.db.sql("""
        SELECT COALESCE(SUM(total_sales), 0) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    
    total = (shift_revenue[0].value or 0) + (cashier_revenue[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry"]
    }

@frappe.whitelist()
def get_month_fuel_sales():
    """This month's fuel sales - from both shift entry types"""
    month_start = get_first_day(today())
    
    # Query Shift Sale Entry
    shift_fuel = frappe.db.sql("""
        SELECT COALESCE(SUM(total_fuel_sales), 0) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_fuel = frappe.db.sql("""
        SELECT COALESCE(SUM(total_fuel_sales), 0) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    
    total = (shift_fuel[0].value or 0) + (cashier_fuel[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry"]
    }

@frappe.whitelist()
def get_month_other_sales():
    """This month's other sales - from both shift entry types"""
    month_start = get_first_day(today())
    
    # Query Shift Sale Entry
    shift_other = frappe.db.sql("""
        SELECT COALESCE(SUM(total_other_sales), 0) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_other = frappe.db.sql("""
        SELECT COALESCE(SUM(total_other_sales), 0) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    
    total = (shift_other[0].value or 0) + (cashier_other[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry"]
    }

# ============================================================================
# CREDIT MANAGEMENT
# ============================================================================

@frappe.whitelist()
def get_credit_outstanding():
    """
    Total credit outstanding - SINGLE SOURCE OF TRUTH.
    Only counts Credit Sale documents (auto-created from shifts).
    """
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0) as value
        FROM `tabCredit Sale`
        WHERE docstatus = 1
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["query-report", "Customer Outstanding Report"]
    }

@frappe.whitelist()
def get_credit_sales_count():
    """Credit sales this month - ONLY from Credit Sale documents"""
    month_start = get_first_day(today())
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabCredit Sale`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Credit Sale"]
    }

@frappe.whitelist()
def get_credit_customers_count():
    """Credit customers with outstanding balance - ONLY from Credit Sale"""
    result = frappe.db.sql("""
        SELECT COUNT(DISTINCT customer) as value
        FROM `tabCredit Sale`
        WHERE docstatus = 1 AND outstanding_amount > 0
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["query-report", "Customer Outstanding Report"]
    }

@frappe.whitelist()
def get_payments_received_today():
    """Payments received today"""
    result = frappe.db.sql("""
        SELECT SUM(paid_amount) as value
        FROM `tabCustomer Payment Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Customer Payment Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_month_payments_received():
    """Payments received this month"""
    month_start = get_first_day(today())
    result = frappe.db.sql("""
        SELECT SUM(paid_amount) as value
        FROM `tabCustomer Payment Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Customer Payment Entry"]
    }

# ============================================================================
# STOCK & INVENTORY
# ============================================================================

@frappe.whitelist()
def get_current_stock():
    """Current stock from latest tank dip readings"""
    result = frappe.db.sql("""
        SELECT SUM(total_stock_as_per_dip) as value
        FROM `tabTank Dip Reading`
        WHERE posting_date = (
            SELECT MAX(posting_date) FROM `tabTank Dip Reading` WHERE docstatus = 1
        ) AND docstatus = 1
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Float",
        "route": ["List", "Tank Dip Reading"]
    }

@frappe.whitelist()
def get_stock_variance_today():
    """Today's stock variance"""
    result = frappe.db.sql("""
        SELECT SUM(variance) as value
        FROM `tabTank Dip Reading`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Float",
        "route": ["List", "Tank Dip Reading", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_month_tanker_receipts():
    """Tanker receipts this month"""
    month_start = get_first_day(today())
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabTanker Receipt`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Tanker Receipt"]
    }

@frappe.whitelist()
def get_month_fuel_received():
    """Fuel received this month (liters)"""
    month_start = get_first_day(today())
    result = frappe.db.sql("""
        SELECT SUM(total_received_qty) as value
        FROM `tabTanker Receipt`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Float",
        "route": ["List", "Tanker Receipt"]
    }

# ============================================================================
# MASTERS & CONFIGURATION
# ============================================================================

@frappe.whitelist()
def get_total_tanks():
    """Total fuel tanks"""
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabFuel Tank Master`
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Fuel Tank Master"]
    }

@frappe.whitelist()
def get_active_tanks():
    """Active fuel tanks"""
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabFuel Tank Master`
        WHERE status = 'Active'
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Fuel Tank Master", {"status": "Active"}]
    }

@frappe.whitelist()
def get_total_nozzles():
    """Total fuel nozzles"""
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabFuel Nozzle Master`
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Fuel Nozzle Master"]
    }

@frappe.whitelist()
def get_active_nozzles():
    """Active fuel nozzles"""
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabFuel Nozzle Master`
        WHERE status = 'Active'
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Fuel Nozzle Master", {"status": "Active"}]
    }

@frappe.whitelist()
def get_total_customers():
    """Total customers"""
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabCustomer`
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Customer"]
    }

@frappe.whitelist()
def get_total_items():
    """Total fuel items"""
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabItem`
        WHERE item_group IN ('Fuel', 'Petrol', 'Diesel', 'CNG')
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Item"]
    }

@frappe.whitelist()
def get_total_fuel_items():
    """Total fuel items - alias for get_total_items"""
    return get_total_items()

# ============================================================================
# HR & STAFF
# ============================================================================

@frappe.whitelist()
def get_total_employees():
    """Total active employees"""
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabEmployee`
        WHERE status = 'Active'
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Employee"]
    }

@frappe.whitelist()
def get_total_advance_given():
    """Total advances given from shift expenses - from both shift entry types"""
    # Query Shift Sale Entry
    shift_advances = frappe.db.sql("""
        SELECT COALESCE(SUM(total_emp_advances), 0) as value
        FROM `tabShift Sale Entry`
        WHERE docstatus = 1
    """, as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_advances = frappe.db.sql("""
        SELECT COALESCE(SUM(total_emp_advances), 0) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE docstatus = 1
    """, as_dict=1)
    
    total = (shift_advances[0].value or 0) + (cashier_advances[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry"]
    }

@frappe.whitelist()
def get_total_cash_shortage():
    """Total cash shortage/variance from cashier entries"""
    result = frappe.db.sql("""
        SELECT SUM(cash_variance) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE docstatus = 1
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Cashier Wise Shift Sale Entry"]
    }

@frappe.whitelist()
def get_today_expenses():
    """Today's total expenses - from both shift entry types"""
    # Query Shift Sale Entry
    shift_expenses = frappe.db.sql("""
        SELECT COALESCE(SUM(total_expenses), 0) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_expenses = frappe.db.sql("""
        SELECT COALESCE(SUM(total_expenses), 0) as value
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    
    total = (shift_expenses[0].value or 0) + (cashier_expenses[0].value or 0)
    
    return {
        "value": total,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_total_expenses():
    """Total expenses - alias for get_today_expenses"""
    return get_today_expenses()

# ============================================================================
# PURCHASE & PROCUREMENT
# ============================================================================

@frappe.whitelist()
def get_month_purchases():
    """Product purchases this month"""
    month_start = get_first_day(today())
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabProduct Purchase Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Product Purchase Entry"]
    }

@frappe.whitelist()
def get_month_purchase_amount():
    """Purchase amount this month"""
    month_start = get_first_day(today())
    result = frappe.db.sql("""
        SELECT SUM(total_amount) as value
        FROM `tabProduct Purchase Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Product Purchase Entry"]
    }

# ============================================================================
# DASHBOARD CHART COMBINED METHODS
# ============================================================================

@frappe.whitelist()
def get_daily_sales_trend(from_date=None, to_date=None):
    """Combined daily sales from both shift entry types for dashboard charts"""
    conditions = ""
    params = {}
    
    if from_date:
        conditions += " AND posting_date >= %(from_date)s"
        params["from_date"] = from_date
    if to_date:
        conditions += " AND posting_date <= %(to_date)s"
        params["to_date"] = to_date
    
    # Query Shift Sale Entry
    shift_data = frappe.db.sql(f"""
        SELECT posting_date, SUM(total_sales) as total_sales
        FROM `tabShift Sale Entry`
        WHERE docstatus = 1 {conditions}
        GROUP BY posting_date
    """, params, as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_data = frappe.db.sql(f"""
        SELECT posting_date, SUM(total_sales) as total_sales
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE docstatus = 1 {conditions}
        GROUP BY posting_date
    """, params, as_dict=1)
    
    # Combine data by date
    combined = {}
    for row in shift_data:
        combined[row.posting_date] = combined.get(row.posting_date, 0) + (row.total_sales or 0)
    for row in cashier_data:
        combined[row.posting_date] = combined.get(row.posting_date, 0) + (row.total_sales or 0)
    
    # Return format for dashboard charts
    result = []
    for date, total in sorted(combined.items()):
        result.append({"date": date, "value": total})
    
    return result

@frappe.whitelist()
def get_daily_fuel_sales_trend(from_date=None, to_date=None):
    """Combined daily fuel sales from both shift entry types"""
    conditions = ""
    params = {}
    
    if from_date:
        conditions += " AND posting_date >= %(from_date)s"
        params["from_date"] = from_date
    if to_date:
        conditions += " AND posting_date <= %(to_date)s"
        params["to_date"] = to_date
    
    # Query Shift Sale Entry
    shift_data = frappe.db.sql(f"""
        SELECT posting_date, SUM(total_fuel_sales) as total_fuel_sales
        FROM `tabShift Sale Entry`
        WHERE docstatus = 1 {conditions}
        GROUP BY posting_date
    """, params, as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_data = frappe.db.sql(f"""
        SELECT posting_date, SUM(total_fuel_sales) as total_fuel_sales
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE docstatus = 1 {conditions}
        GROUP BY posting_date
    """, params, as_dict=1)
    
    # Combine data by date
    combined = {}
    for row in shift_data:
        combined[row.posting_date] = combined.get(row.posting_date, 0) + (row.total_fuel_sales or 0)
    for row in cashier_data:
        combined[row.posting_date] = combined.get(row.posting_date, 0) + (row.total_fuel_sales or 0)
    
    # Return format for dashboard charts
    result = []
    for date, total in sorted(combined.items()):
        result.append({"date": date, "value": total})
    
    return result

@frappe.whitelist()
def get_weekly_revenue_trend(weeks=4):
    """Combined weekly revenue from both shift entry types"""
    # Get last N weeks of data
    start_date = frappe.utils.add_days(frappe.utils.today(), -weeks * 7)
    
    # Query Shift Sale Entry
    shift_data = frappe.db.sql("""
        SELECT YEARWEEK(posting_date) as week, SUM(total_sales) as total_sales
        FROM `tabShift Sale Entry`
        WHERE docstatus = 1 AND posting_date >= %s
        GROUP BY YEARWEEK(posting_date)
    """, start_date, as_dict=1)
    
    # Query Cashier Wise Shift Sale Entry
    cashier_data = frappe.db.sql("""
        SELECT YEARWEEK(posting_date) as week, SUM(total_sales) as total_sales
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE docstatus = 1 AND posting_date >= %s
        GROUP BY YEARWEEK(posting_date)
    """, start_date, as_dict=1)
    
    # Combine data by week
    combined = {}
    for row in shift_data:
        combined[row.week] = combined.get(row.week, 0) + (row.total_sales or 0)
    for row in cashier_data:
        combined[row.week] = combined.get(row.week, 0) + (row.total_sales or 0)
    
    # Return format for dashboard charts
    result = []
    for week, total in sorted(combined.items()):
        result.append({"week": week, "value": total})
    
    return result