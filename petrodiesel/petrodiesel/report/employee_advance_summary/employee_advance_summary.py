# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    return columns, data, None, chart

def get_columns():
    return [
        {
            "fieldname": "employee",
            "label": _("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150
        },
        {
            "fieldname": "employee_name",
            "label": _("Employee Name"),
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "total_advances",
            "label": _("Total Advances"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "total_expenses",
            "label": _("Total Expenses"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "total_loans",
            "label": _("Total Loans"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "total_shortage",
            "label": _("Total Cash Shortage"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "total_deductions",
            "label": _("Total to Deduct"),
            "fieldtype": "Currency",
            "width": 140
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql(f"""
        SELECT 
            e.name as employee,
            e.employee_name,
            COALESCE(SUM(CASE WHEN sea.advance_type = 'Advance' THEN sea.amount ELSE 0 END), 0) as total_advances,
            COALESCE(SUM(CASE WHEN sea.advance_type = 'Expense' THEN sea.amount ELSE 0 END), 0) as total_expenses,
            COALESCE(SUM(CASE WHEN sea.advance_type = 'Loan' THEN sea.amount ELSE 0 END), 0) as total_loans,
            COALESCE(SUM(nsr.cash_shortage), 0) as total_shortage,
            (
                COALESCE(SUM(CASE WHEN sea.advance_type = 'Advance' THEN sea.amount ELSE 0 END), 0) +
                COALESCE(SUM(CASE WHEN sea.advance_type = 'Expense' THEN sea.amount ELSE 0 END), 0) +
                COALESCE(SUM(CASE WHEN sea.advance_type = 'Loan' THEN sea.amount ELSE 0 END), 0) +
                COALESCE(SUM(nsr.cash_shortage), 0)
            ) as total_deductions
        FROM 
            `tabEmployee` e
        LEFT JOIN 
            `tabNozzle Shift Reading` nsr ON (nsr.cashier = e.name OR nsr.supervisor = e.name)
            AND nsr.docstatus = 1
            {conditions}
        LEFT JOIN 
            `tabShift Employee Advance` sea ON sea.parent = nsr.name
        WHERE 
            e.status = 'Active'
        GROUP BY 
            e.name, e.employee_name
        HAVING 
            total_deductions > 0
        ORDER BY 
            total_deductions DESC
    """, filters, as_dict=1)
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND nsr.posting_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND nsr.posting_date <= %(to_date)s"
    
    if filters.get("employee"):
        conditions += " AND e.name = %(employee)s"
    
    return conditions

def get_chart_data(data):
    if not data or len(data) == 0:
        return None
    
    # Top 10 employees by total deductions
    top_10 = data[:10]
    
    return {
        "data": {
            "labels": [d.employee_name for d in top_10],
            "datasets": [
                {
                    "name": "Advances",
                    "values": [d.total_advances for d in top_10]
                },
                {
                    "name": "Expenses",
                    "values": [d.total_expenses for d in top_10]
                },
                {
                    "name": "Shortage",
                    "values": [d.total_shortage for d in top_10]
                }
            ]
        },
        "type": "bar",
        "colors": ["#5E64FF", "#FFA00A", "#FF5858"],
        "height": 300,
        "barOptions": {
            "stacked": 1
        }
    }
