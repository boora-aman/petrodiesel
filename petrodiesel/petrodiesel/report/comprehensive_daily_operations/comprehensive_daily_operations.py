# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    summary = get_summary(data)
    return columns, data, None, None, summary

def get_columns():
    return [
        {"label": _("Category"), "fieldname": "category", "fieldtype": "Data", "width": 200},
        {"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 250},
        {"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Float", "width": 120, "precision": 2},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 150},
        {"label": _("Count"), "fieldname": "count", "fieldtype": "Int", "width": 100}
    ]

def get_data(filters):
    if not filters:
        filters = {}
    
    date = filters.get("date") or frappe.utils.today()
    
    data = []
    
    # ========== FUEL SALES ==========
    fuel_sales = get_fuel_sales(date)
    if fuel_sales:
        data.append({"category": "FUEL SALES", "description": "", "quantity": 0, "amount": 0, "count": 0, "is_group": 1})
        data.extend(fuel_sales)
    
    # ========== CREDIT SALES ==========
    credit_sales = get_credit_sales(date)
    if credit_sales:
        data.append({"category": "CREDIT SALES", "description": "", "quantity": 0, "amount": 0, "count": 0, "is_group": 1})
        data.extend(credit_sales)
    
    # ========== OTHER SALES ==========
    other_sales = get_other_sales(date)
    if other_sales:
        data.append({"category": "OTHER SALES", "description": "", "quantity": 0, "amount": 0, "count": 0, "is_group": 1})
        data.extend(other_sales)
    
    # ========== ONLINE PAYMENTS ==========
    online_payments = get_online_payments(date)
    if online_payments:
        data.append({"category": "ONLINE PAYMENTS", "description": "", "quantity": 0, "amount": 0, "count": 0, "is_group": 1})
        data.extend(online_payments)
    
    # ========== DRIVER CASH ==========
    driver_cash = get_driver_cash(date)
    if driver_cash:
        data.append({"category": "DRIVER CASH ADVANCES", "description": "", "quantity": 0, "amount": 0, "count": 0, "is_group": 1})
        data.extend(driver_cash)
    
    # ========== EXPENSES ==========
    expenses = get_expenses(date)
    if expenses:
        data.append({"category": "EXPENSES", "description": "", "quantity": 0, "amount": 0, "count": 0, "is_group": 1})
        data.extend(expenses)
    
    # ========== EMPLOYEE ADVANCES ==========
    emp_advances = get_employee_advances(date)
    if emp_advances:
        data.append({"category": "EMPLOYEE ADVANCES", "description": "", "quantity": 0, "amount": 0, "count": 0, "is_group": 1})
        data.extend(emp_advances)
    
    # ========== CUSTOMER PAYMENTS ==========
    payments = get_customer_payments(date)
    if payments:
        data.append({"category": "CUSTOMER PAYMENTS", "description": "", "quantity": 0, "amount": 0, "count": 0, "is_group": 1})
        data.extend(payments)
    
    # ========== CASH RECONCILIATION ==========
    cash_recon = get_cash_reconciliation(date)
    if cash_recon:
        data.append({"category": "CASH RECONCILIATION", "description": "", "quantity": 0, "amount": 0, "count": 0, "is_group": 1})
        data.extend(cash_recon)
    
    # ========== TESTING ==========
    testing = get_testing(date)
    if testing:
        data.append({"category": "TESTING", "description": "", "quantity": 0, "amount": 0, "count": 0, "is_group": 1})
        data.extend(testing)
    
    # ========== NOZZLE SUMMARY ==========
    nozzles = get_nozzle_summary(date)
    if nozzles:
        data.append({"category": "NOZZLE SUMMARY", "description": "", "quantity": 0, "amount": 0, "count": 0, "is_group": 1})
        data.extend(nozzles)
    
    return data

def get_fuel_sales(date):
    result = frappe.db.sql("""
        SELECT 
            'Fuel Sales' as category,
            fuel_item as description,
            SUM(actual_sale_qty) as quantity,
            SUM(amount) as amount,
            COUNT(*) as count
        FROM (
            SELECT fuel_item, actual_sale_qty, amount
            FROM `tabShift Nozzle Reading` snr
            INNER JOIN `tabShift Sale Entry` sse ON snr.parent = sse.name
            WHERE sse.posting_date = %s AND sse.docstatus = 1
            UNION ALL
            SELECT fuel_item, actual_sale_qty, amount
            FROM `tabNozzle Reading Detail` nrd
            INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON nrd.parent = cwsse.name
            WHERE cwsse.posting_date = %s AND cwsse.docstatus = 1
        ) combined
        GROUP BY fuel_item
        ORDER BY amount DESC
    """, (date, date), as_dict=1)
    return result

def get_credit_sales(date):
    result = frappe.db.sql("""
        SELECT 
            'Credit Sale' as category,
            CONCAT(customer, ' - ', fuel_item) as description,
            SUM(quantity_liters) as quantity,
            SUM(amount) as amount,
            COUNT(*) as count
        FROM `tabCredit Sale Item` csi
        INNER JOIN `tabCredit Sale` cs ON csi.parent = cs.name
        WHERE cs.posting_date = %s AND cs.docstatus = 1
        GROUP BY cs.customer, csi.fuel_item
        ORDER BY amount DESC
    """, date, as_dict=1)
    return result

def get_other_sales(date):
    result = frappe.db.sql("""
        SELECT 
            'Other Items' as category,
            item_code as description,
            SUM(quantity) as quantity,
            SUM(amount) as amount,
            COUNT(*) as count
        FROM (
            SELECT item_code, quantity, amount
            FROM `tabShift Other Sales` sos
            INNER JOIN `tabShift Sale Entry` sse ON sos.parent = sse.name
            WHERE sse.posting_date = %s AND sse.docstatus = 1
            UNION ALL
            SELECT item_code, quantity, amount
            FROM `tabOther Product Sales Detail` opsd
            INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON opsd.parent = cwsse.name
            WHERE cwsse.posting_date = %s AND cwsse.docstatus = 1
        ) combined
        GROUP BY item_code
        ORDER BY amount DESC
    """, (date, date), as_dict=1)
    return result

def get_online_payments(date):
    result = frappe.db.sql("""
        SELECT 
            'Online Payment' as category,
            payment_method as description,
            0 as quantity,
            SUM(amount) as amount,
            COUNT(*) as count
        FROM (
            SELECT payment_method, amount
            FROM `tabShift Online Payment` sop
            INNER JOIN `tabShift Sale Entry` sse ON sop.parent = sse.name
            WHERE sse.posting_date = %s AND sse.docstatus = 1
            UNION ALL
            SELECT payment_method, amount
            FROM `tabOnline Payment Detail` opd
            INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON opd.parent = cwsse.name
            WHERE cwsse.posting_date = %s AND cwsse.docstatus = 1
        ) combined
        GROUP BY payment_method
        ORDER BY amount DESC
    """, (date, date), as_dict=1)
    return result

def get_driver_cash(date):
    result = frappe.db.sql("""
        SELECT 
            'Driver Cash' as category,
            driver_name as description,
            0 as quantity,
            SUM(cash_amount) as amount,
            COUNT(*) as count
        FROM (
            SELECT driver_name, cash_amount
            FROM `tabShift Driver Cash` sdc
            INNER JOIN `tabShift Sale Entry` sse ON sdc.parent = sse.name
            WHERE sse.posting_date = %s AND sse.docstatus = 1
            UNION ALL
            SELECT driver_name, cash_amount
            FROM `tabDriver Cash Advance` dca
            INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON dca.parent = cwsse.name
            WHERE cwsse.posting_date = %s AND cwsse.docstatus = 1
        ) combined
        GROUP BY driver_name
        ORDER BY amount DESC
    """, (date, date), as_dict=1)
    return result

def get_expenses(date):
    result = frappe.db.sql("""
        SELECT 
            'Expense' as category,
            expense_type as description,
            0 as quantity,
            SUM(amount) as amount,
            COUNT(*) as count
        FROM (
            SELECT expense_type, amount
            FROM `tabShift Expense Detail` sed
            INNER JOIN `tabShift Sale Entry` sse ON sed.parent = sse.name
            WHERE sse.posting_date = %s AND sse.docstatus = 1
            UNION ALL
            SELECT expense_type, amount
            FROM `tabShift Expense Detail` sed
            INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON sed.parent = cwsse.name
            WHERE cwsse.posting_date = %s AND cwsse.docstatus = 1
        ) combined
        GROUP BY expense_type
        ORDER BY amount DESC
    """, (date, date), as_dict=1)
    return result

def get_employee_advances(date):
    result = frappe.db.sql("""
        SELECT 
            'Employee Advance' as category,
            employee_name as description,
            0 as quantity,
            SUM(amount) as amount,
            COUNT(*) as count
        FROM (
            SELECT employee_name, amount
            FROM `tabShift Employee Advance` sea
            INNER JOIN `tabShift Sale Entry` sse ON sea.parent = sse.name
            WHERE sse.posting_date = %s AND sse.docstatus = 1
            UNION ALL
            SELECT employee_name, amount
            FROM `tabShift Employee Advance` sea
            INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON sea.parent = cwsse.name
            WHERE cwsse.posting_date = %s AND cwsse.docstatus = 1
        ) combined
        GROUP BY employee_name
        ORDER BY amount DESC
    """, (date, date), as_dict=1)
    return result

def get_customer_payments(date):
    result = frappe.db.sql("""
        SELECT 
            'Payment Received' as category,
            CONCAT(customer, ' - ', payment_mode) as description,
            0 as quantity,
            paid_amount as amount,
            1 as count
        FROM `tabCustomer Payment Entry`
        WHERE posting_date = %s AND docstatus = 1
        ORDER BY paid_amount DESC
    """, date, as_dict=1)
    return result

def get_cash_reconciliation(date):
    result = frappe.db.sql("""
        SELECT 
            'Cash Reconciliation' as category,
            name as description,
            0 as quantity,
            cash_variance as amount,
            1 as count
        FROM (
            SELECT name, cash_variance FROM `tabShift Sale Entry`
            WHERE posting_date = %s AND docstatus = 1
            UNION ALL
            SELECT name, cash_variance FROM `tabCashier Wise Shift Sale Entry`
            WHERE posting_date = %s AND docstatus = 1
        ) combined
        WHERE ABS(cash_variance) > 0
        ORDER BY ABS(cash_variance) DESC
    """, (date, date), as_dict=1)
    return result

def get_testing(date):
    result = frappe.db.sql("""
        SELECT 
            'Testing' as category,
            fuel_item as description,
            SUM(testing_qty) as quantity,
            0 as amount,
            COUNT(*) as count
        FROM (
            SELECT fuel_item, testing_qty
            FROM `tabShift Nozzle Reading` snr
            INNER JOIN `tabShift Sale Entry` sse ON snr.parent = sse.name
            WHERE sse.posting_date = %s AND sse.docstatus = 1 AND testing_qty > 0
            UNION ALL
            SELECT fuel_item, testing_qty
            FROM `tabNozzle Reading Detail` nrd
            INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON nrd.parent = cwsse.name
            WHERE cwsse.posting_date = %s AND cwsse.docstatus = 1 AND testing_qty > 0
        ) combined
        GROUP BY fuel_item
        ORDER BY quantity DESC
    """, (date, date), as_dict=1)
    return result

def get_nozzle_summary(date):
    result = frappe.db.sql("""
        SELECT 
            'Nozzle' as category,
            nozzle as description,
            SUM(actual_sale_qty) as quantity,
            SUM(amount) as amount,
            COUNT(*) as count
        FROM (
            SELECT nozzle, actual_sale_qty, amount
            FROM `tabShift Nozzle Reading` snr
            INNER JOIN `tabShift Sale Entry` sse ON snr.parent = sse.name
            WHERE sse.posting_date = %s AND sse.docstatus = 1
            UNION ALL
            SELECT nozzle, actual_sale_qty, amount
            FROM `tabNozzle Reading Detail` nrd
            INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON nrd.parent = cwsse.name
            WHERE cwsse.posting_date = %s AND cwsse.docstatus = 1
        ) combined
        GROUP BY nozzle
        ORDER BY amount DESC
    """, (date, date), as_dict=1)
    return result

def get_summary(data):
    if not data:
        return []
    
    total_fuel = sum(flt(d.get("amount", 0)) for d in data if d.get("category") == "Fuel Sales")
    total_credit = sum(flt(d.get("amount", 0)) for d in data if d.get("category") == "Credit Sale")
    total_other = sum(flt(d.get("amount", 0)) for d in data if d.get("category") == "Other Items")
    total_online = sum(flt(d.get("amount", 0)) for d in data if d.get("category") == "Online Payment")
    total_expenses = sum(flt(d.get("amount", 0)) for d in data if d.get("category") == "Expense")
    total_payments = sum(flt(d.get("amount", 0)) for d in data if d.get("category") == "Payment Received")
    
    return [
        {"value": total_fuel, "label": "Total Fuel Sales", "datatype": "Currency", "indicator": "Green"},
        {"value": total_credit, "label": "Total Credit Sales", "datatype": "Currency", "indicator": "Orange"},
        {"value": total_other, "label": "Total Other Sales", "datatype": "Currency", "indicator": "Blue"},
        {"value": total_online, "label": "Total Online Payments", "datatype": "Currency", "indicator": "Purple"},
        {"value": total_expenses, "label": "Total Expenses", "datatype": "Currency", "indicator": "Red"},
        {"value": total_payments, "label": "Payments Received", "datatype": "Currency", "indicator": "Green"}
    ]
