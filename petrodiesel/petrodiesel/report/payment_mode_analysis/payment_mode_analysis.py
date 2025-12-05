# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    return columns, data, None, chart

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
            "fieldname": "cash_received",
            "label": _("Cash"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "paytm",
            "label": _("Paytm"),
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "fieldname": "phonepe",
            "label": _("PhonePe"),
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "fieldname": "googlepay",
            "label": _("Google Pay"),
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "fieldname": "card",
            "label": _("Card"),
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "fieldname": "other",
            "label": _("Other"),
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "fieldname": "total_online",
            "label": _("Total Online"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "credit_sales",
            "label": _("Credit"),
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "fieldname": "total_collection",
            "label": _("Total Collection"),
            "fieldtype": "Currency",
            "width": 140
        }
    ]

def get_data(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND nsr.posting_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND nsr.posting_date <= %(to_date)s"
    
    if filters.get("shift"):
        conditions += " AND nsr.shift = %(shift)s"
    
    # Get data with proper field names
    data = frappe.db.sql(f"""
        SELECT 
            nsr.posting_date,
            nsr.shift,
            nsr.cash_received,
            SUM(CASE WHEN opd.payment_method = 'Paytm' THEN opd.amount ELSE 0 END) as paytm,
            SUM(CASE WHEN opd.payment_method = 'PhonePe' THEN opd.amount ELSE 0 END) as phonepe,
            SUM(CASE WHEN opd.payment_method = 'Google Pay' THEN opd.amount ELSE 0 END) as googlepay,
            SUM(CASE WHEN opd.payment_method = 'Card' THEN opd.amount ELSE 0 END) as card,
            SUM(CASE WHEN opd.payment_method NOT IN ('Paytm', 'PhonePe', 'Google Pay', 'Card') 
                AND opd.payment_method IS NOT NULL THEN opd.amount ELSE 0 END) as other,
            nsr.total_online_collection as total_online,
            nsr.credit_sales_amount as credit_sales,
            (nsr.cash_received + nsr.total_online_collection) as total_collection
        FROM 
            `tabNozzle Shift Reading` nsr
        LEFT JOIN 
            `tabOnline Payment Detail` opd ON opd.parent = nsr.name
        WHERE 
            nsr.docstatus = 1
            {conditions}
        GROUP BY 
            nsr.name, nsr.posting_date, nsr.shift
        ORDER BY 
            nsr.posting_date DESC, nsr.shift
    """, filters, as_dict=1)
    
    return data

def get_chart_data(data):
    if not data:
        return None
    
    # Aggregate totals across all rows
    totals = {
        "Cash": sum(row.cash_received or 0 for row in data),
        "Paytm": sum(row.paytm or 0 for row in data),
        "PhonePe": sum(row.phonepe or 0 for row in data),
        "Google Pay": sum(row.googlepay or 0 for row in data),
        "Card": sum(row.card or 0 for row in data),
        "Other": sum(row.other or 0 for row in data),
        "Credit": sum(row.credit_sales or 0 for row in data)
    }
    
    # Filter out zero values
    totals = {k: v for k, v in totals.items() if v > 0}
    
    return {
        "data": {
            "labels": list(totals.keys()),
            "datasets": [
                {
                    "name": "Amount",
                    "values": list(totals.values())
                }
            ]
        },
        "type": "donut",
        "colors": ["#29CD42", "#5E64FF", "#F683AE", "#FFA00A", "#FF5858", "#A78BFA", "#8B5CF6"],
        "height": 300
    }
