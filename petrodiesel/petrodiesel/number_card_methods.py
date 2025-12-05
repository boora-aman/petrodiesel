# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, get_first_day, getdate, add_days

@frappe.whitelist()
def get_today_fuel_sales():
    """Today's fuel sales amount"""
    result = frappe.db.sql("""
        SELECT SUM(total_fuel_sales_amount) as value
        FROM `tabNozzle Shift Reading`
        WHERE posting_date = %s
        AND docstatus = 1
    """, today(), as_dict=1)
    
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Nozzle Shift Reading", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_today_total_collection():
    """Today's total collection"""
    result = frappe.db.sql("""
        SELECT SUM(total_sales_amount) as value
        FROM `tabNozzle Shift Reading`
        WHERE posting_date = %s
        AND docstatus = 1
    """, today(), as_dict=1)
    
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Nozzle Shift Reading", {"posting_date": today()}]
    }

@frappe.whitelist()
def get_current_stock():
    """Current stock in liters"""
    result = frappe.db.sql("""
        SELECT SUM(actual_qty) as value
        FROM `tabBin`
        WHERE actual_qty > 0
    """, as_dict=1)
    
    return {
        "value": result[0].value or 0,
        "fieldtype": "Float",
        "route": ["query-report", "Stock Balance"]
    }

@frappe.whitelist()
def get_week_shifts_count():
    """This week's shift count"""
    week_start = add_days(today(), -7)
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabNozzle Shift Reading`
        WHERE posting_date >= %s
        AND docstatus = 1
    """, week_start, as_dict=1)
    
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Nozzle Shift Reading"]
    }

@frappe.whitelist()
def get_credit_outstanding():
    """Total credit outstanding"""
    result = frappe.db.sql("""
        SELECT SUM(total_amount) as value
        FROM `tabCredit Sale`
        WHERE docstatus = 1
    """, as_dict=1)
    
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Credit Sale"]
    }

@frappe.whitelist()
def get_month_revenue():
    """This month's revenue"""
    month_start = get_first_day(today())
    result = frappe.db.sql("""
        SELECT SUM(total_sales_amount) as value
        FROM `tabNozzle Shift Reading`
        WHERE posting_date >= %s
        AND docstatus = 1
    """, month_start, as_dict=1)
    
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["List", "Nozzle Shift Reading"]
    }

@frappe.whitelist()
def get_credit_sales_count():
    """Credit sales this month"""
    month_start = get_first_day(today())
    result = frappe.db.sql("""
        SELECT COUNT(*) as value
        FROM `tabCredit Sale`
        WHERE posting_date >= %s
        AND docstatus = 1
    """, month_start, as_dict=1)
    
    return {
        "value": result[0].value or 0,
        "fieldtype": "Int",
        "route": ["List", "Credit Sale"]
    }

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
def get_active_nozzles():
    """Active nozzles"""
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
def get_total_cash_shortage():
    """Total cash shortage from all shifts"""
    result = frappe.db.sql("""
        SELECT IFNULL(SUM(cash_shortage), 0) as value
        FROM `tabNozzle Shift Reading`
        WHERE docstatus = 1
    """, as_dict=1)
    
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route_options": {"docstatus": 1},
        "route": ["query-report", "Employee Advance Summary"]
    }

@frappe.whitelist()
def get_total_advance_given():
    """Total advances given to employees"""
    result = frappe.db.sql("""
        SELECT IFNULL(SUM(sea.amount), 0) as value
        FROM `tabShift Employee Advance` sea
        INNER JOIN `tabNozzle Shift Reading` nsr ON nsr.name = sea.parent
        WHERE nsr.docstatus = 1
    """, as_dict=1)
    
    return {
        "value": result[0].value or 0,
        "fieldtype": "Currency",
        "route": ["query-report", "Employee Advance Summary"]
    }
