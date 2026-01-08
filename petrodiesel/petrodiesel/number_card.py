# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, get_first_day, getdate, add_days, nowdate

# ============================================================================
# DAILY OPERATIONS - TODAY'S METRICS
# ============================================================================

@frappe.whitelist()
def get_today_fuel_sales():
    """Today's fuel sales amount"""
    result = frappe.db.sql("""
        SELECT SUM(total_fuel_sales) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_today_total_collection():
    """Today's total collection"""
    result = frappe.db.sql("""
        SELECT SUM(total_sales) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_today_cash_collection():
    """Today's cash received"""
    result = frappe.db.sql("""
        SELECT SUM(cash_received) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_today_other_sales():
    """Today's other sales (non-fuel)"""
    result = frappe.db.sql("""
        SELECT SUM(total_other_sales) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_today_credit_fuel():
    """Today's credit fuel sales"""
    result = frappe.db.sql("""
        SELECT SUM(total_credit_fuel) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_today_online_sales():
    """Today's online payments"""
    result = frappe.db.sql("""
        SELECT SUM(total_online) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_active_shifts_today():
    """Active shifts today"""
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s
    """, today(), as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_today_cash_variance():
    """Today's cash variance"""
    result = frappe.db.sql("""
        SELECT SUM(cash_variance) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

# ============================================================================
# WEEKLY METRICS
# ============================================================================

@frappe.whitelist()
def get_week_shifts_count():
    """This week's shift count"""
    week_start = add_days(today(), -7)
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, week_start, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Shift Sale Entry"]
    }

@frappe.whitelist()
def get_week_revenue():
    """This week's revenue"""
    week_start = add_days(today(), -7)
    result = frappe.db.sql("""
        SELECT SUM(total_sales) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, week_start, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry"]
    }

# ============================================================================
# MONTHLY METRICS
# ============================================================================

@frappe.whitelist()
def get_month_revenue():
    """This month's revenue"""
    month_start = get_first_day(today())
    result = frappe.db.sql("""
        SELECT SUM(total_sales) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry"]
    }

@frappe.whitelist()
def get_month_fuel_sales():
    """This month's fuel sales"""
    month_start = get_first_day(today())
    result = frappe.db.sql("""
        SELECT SUM(total_fuel_sales) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry"]
    }

@frappe.whitelist()
def get_month_other_sales():
    """This month's other sales"""
    month_start = get_first_day(today())
    result = frappe.db.sql("""
        SELECT SUM(total_other_sales) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date >= %s AND docstatus = 1
    """, month_start, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry"]
    }

# ============================================================================
# CREDIT MANAGEMENT
# ============================================================================

@frappe.whitelist()
def get_credit_outstanding():
    """Total credit outstanding"""
    result = frappe.db.sql("""
        SELECT SUM(outstanding_amount) as value
        FROM `tabCredit Sale`
        WHERE docstatus = 1 AND outstanding_amount > 0
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Credit Sale", {"outstanding_amount": [">", 0]}]
    }

@frappe.whitelist()
def get_credit_sales_count():
    """Credit sales this month"""
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
    """Credit customers with outstanding balance"""
    result = frappe.db.sql("""
        SELECT COUNT(DISTINCT customer) as value
        FROM `tabCredit Sale`
        WHERE docstatus = 1 AND outstanding_amount > 0
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Credit Sale"]
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
    """Total advances given from shift expenses"""
    result = frappe.db.sql("""
        SELECT SUM(total_emp_advances) as value
        FROM `tabShift Sale Entry`
        WHERE docstatus = 1
    """, as_dict=1)
    return {
        "value": result[0].value or 0,
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
    """Today's total expenses"""
    result = frappe.db.sql("""
        SELECT SUM(total_expenses) as value
        FROM `tabShift Sale Entry`
        WHERE posting_date = %s AND docstatus = 1
    """, today(), as_dict=1)
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Shift Sale Entry", {"posting_date": today()}]
    }

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