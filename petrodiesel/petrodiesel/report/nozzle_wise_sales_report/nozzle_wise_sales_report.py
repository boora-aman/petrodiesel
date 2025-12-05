# Copyright (c) 2025, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "posting_date",
            "label": _("Date"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "shift",
            "label": _("Shift"),
            "fieldtype": "Link",
            "options": "Shift Master",
            "width": 120
        },
        {
            "fieldname": "nozzle",
            "label": _("Nozzle"),
            "fieldtype": "Link",
            "options": "Fuel Nozzle Master",
            "width": 120
        },
        {
            "fieldname": "fuel_item",
            "label": _("Fuel Type"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 120
        },
        {
            "fieldname": "opening_reading",
            "label": _("Opening Reading"),
            "fieldtype": "Float",
            "width": 120,
            "precision": 2
        },
        {
            "fieldname": "closing_reading",
            "label": _("Closing Reading"),
            "fieldtype": "Float",
            "width": 120,
            "precision": 2
        },
        {
            "fieldname": "total_sale_qty",
            "label": _("Total Qty (L)"),
            "fieldtype": "Float",
            "width": 100,
            "precision": 2
        },
        {
            "fieldname": "testing_qty",
            "label": _("Testing (L)"),
            "fieldtype": "Float",
            "width": 100,
            "precision": 2
        },
        {
            "fieldname": "actual_sale_qty",
            "label": _("Actual Sale (L)"),
            "fieldtype": "Float",
            "width": 120,
            "precision": 2
        },
        {
            "fieldname": "rate_per_liter",
            "label": _("Rate/Liter"),
            "fieldtype": "Currency",
            "width": 100,
            "precision": 2
        },
        {
            "fieldname": "amount",
            "label": _("Amount"),
            "fieldtype": "Currency",
            "width": 120,
            "precision": 2
        },
        {
            "fieldname": "cashier",
            "label": _("Cashier"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql(f"""
        SELECT 
            nsr.posting_date,
            nsr.shift,
            nrd.nozzle,
            nrd.fuel_item,
            nrd.opening_reading,
            nrd.closing_reading,
            nrd.total_sale_qty,
            nrd.testing_qty,
            nrd.actual_sale_qty,
            nrd.rate_per_liter,
            nrd.amount,
            nsr.cashier
        FROM 
            `tabNozzle Shift Reading` nsr
        INNER JOIN 
            `tabNozzle Reading Detail` nrd ON nrd.parent = nsr.name
        WHERE 
            nsr.docstatus = 1
            {conditions}
        ORDER BY 
            nsr.posting_date DESC, nsr.shift, nrd.nozzle
    """, filters, as_dict=1)
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND nsr.posting_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND nsr.posting_date <= %(to_date)s"
    
    if filters.get("shift"):
        conditions += " AND nsr.shift = %(shift)s"
    
    if filters.get("nozzle"):
        conditions += " AND nrd.nozzle = %(nozzle)s"
    
    if filters.get("fuel_item"):
        conditions += " AND nrd.fuel_item = %(fuel_item)s"
    
    return conditions
