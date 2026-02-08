# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    return columns, data, None, chart

def get_columns(filters):
    return [
        {
            "label": _("Employee"),
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120
        },
        {
            "label": _("Employee Name"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Advance"),
            "fieldname": "advance_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Expense"),
            "fieldname": "expense_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Loan"),
            "fieldname": "loan_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Total Amount"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Transaction Count"),
            "fieldname": "transaction_count",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Last Transaction"),
            "fieldname": "last_transaction_date",
            "fieldtype": "Date",
            "width": 120
        }
    ]

def get_data(filters):
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))
    
    # Query both Shift Sale Entry and Cashier Wise Shift Sale Entry
    params = {}
    conditions = get_conditions(filters, params)
    
    # Get data from Shift Sale Entry → Shift Employee Advance
    sse_query = f"""
        SELECT 
            sea.employee,
            sea.employee_name,
            SUM(CASE WHEN sea.advance_type = 'Advance' THEN sea.amount ELSE 0 END) as advance_amount,
            SUM(CASE WHEN sea.advance_type = 'Expense' THEN sea.amount ELSE 0 END) as expense_amount,
            SUM(CASE WHEN sea.advance_type = 'Loan' THEN sea.amount ELSE 0 END) as loan_amount,
            SUM(sea.amount) as total_amount,
            COUNT(*) as transaction_count,
            MAX(sse.posting_date) as last_transaction_date
        FROM `tabShift Employee Advance` sea
        INNER JOIN `tabShift Sale Entry` sse ON sea.parent = sse.name
        WHERE sse.docstatus = 1
        {conditions}
        GROUP BY sea.employee, sea.employee_name
    """
    
    # Get data from Cashier Wise Shift Sale Entry → Shift Employee Advance
    cwsse_query = f"""
        SELECT 
            sea.employee,
            sea.employee_name,
            SUM(CASE WHEN sea.advance_type = 'Advance' THEN sea.amount ELSE 0 END) as advance_amount,
            SUM(CASE WHEN sea.advance_type = 'Expense' THEN sea.amount ELSE 0 END) as expense_amount,
            SUM(CASE WHEN sea.advance_type = 'Loan' THEN sea.amount ELSE 0 END) as loan_amount,
            SUM(sea.amount) as total_amount,
            COUNT(*) as transaction_count,
            MAX(cwsse.posting_date) as last_transaction_date
        FROM `tabShift Employee Advance` sea
        INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON sea.parent = cwsse.name
        WHERE cwsse.docstatus = 1
        {conditions.replace('sse.', 'cwsse.')}
        GROUP BY sea.employee, sea.employee_name
    """
    
    # Combine results from both
    combined_query = f"""
        SELECT 
            employee,
            employee_name,
            SUM(advance_amount) as advance_amount,
            SUM(expense_amount) as expense_amount,
            SUM(loan_amount) as loan_amount,
            SUM(total_amount) as total_amount,
            SUM(transaction_count) as transaction_count,
            MAX(last_transaction_date) as last_transaction_date
        FROM (
            ({sse_query})
            UNION ALL
            ({cwsse_query})
        ) combined
        GROUP BY employee, employee_name
        ORDER BY total_amount DESC
    """
    
    data = frappe.db.sql(combined_query, params, as_dict=1)
    
    return data

def get_conditions(filters, params):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND sse.posting_date >= %(from_date)s"
        params["from_date"] = filters.get("from_date")
    
    if filters.get("to_date"):
        conditions += " AND sse.posting_date <= %(to_date)s"
        params["to_date"] = filters.get("to_date")
    
    if filters.get("employee"):
        conditions += " AND sea.employee = %(employee)s"
        params["employee"] = filters.get("employee")
    
    if filters.get("advance_type"):
        conditions += " AND sea.advance_type = %(advance_type)s"
        params["advance_type"] = filters.get("advance_type")
    
    return conditions

def get_chart_data(data, filters):
    if not data:
        return None
    
    labels = [d.employee_name for d in data[:10]]  # Top 10 employees
    advance_values = [d.advance_amount for d in data[:10]]
    expense_values = [d.expense_amount for d in data[:10]]
    loan_values = [d.loan_amount for d in data[:10]]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Advance",
                    "values": advance_values
                },
                {
                    "name": "Expense",
                    "values": expense_values
                },
                {
                    "name": "Loan",
                    "values": loan_values
                }
            ]
        },
        "type": "bar",
        "colors": ["#29CD42", "#ffa00a", "#4C78FF"]
    }
