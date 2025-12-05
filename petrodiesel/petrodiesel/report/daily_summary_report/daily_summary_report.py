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
            "width": 120
        },
        {
            "fieldname": "total_fuel_sales_qty",
            "label": _("Total Fuel Qty (L)"),
            "fieldtype": "Float",
            "width": 150,
            "precision": 2
        },
        {
            "fieldname": "total_fuel_sales_amount",
            "label": _("Fuel Sales (₹)"),
            "fieldtype": "Currency",
            "width": 150,
            "precision": 2
        },
        {
            "fieldname": "lubricant_sales",
            "label": _("Lubricant Sales (₹)"),
            "fieldtype": "Currency",
            "width": 150,
            "precision": 2
        },
        {
            "fieldname": "accessories_sales",
            "label": _("Accessories (₹)"),
            "fieldtype": "Currency",
            "width": 150,
            "precision": 2
        },
        {
            "fieldname": "total_sales",
            "label": _("Total Sales (₹)"),
            "fieldtype": "Currency",
            "width": 150,
            "precision": 2
        },
        {
            "fieldname": "cash_collection",
            "label": _("Cash (₹)"),
            "fieldtype": "Currency",
            "width": 120,
            "precision": 2
        },
        {
            "fieldname": "online_collection",
            "label": _("Online (₹)"),
            "fieldtype": "Currency",
            "width": 120,
            "precision": 2
        },
        {
            "fieldname": "credit_sales",
            "label": _("Credit (₹)"),
            "fieldtype": "Currency",
            "width": 120,
            "precision": 2
        },
        {
            "fieldname": "variance",
            "label": _("Shortage/Excess (₹)"),
            "fieldtype": "Currency",
            "width": 150,
            "precision": 2
        }
    ]

def get_data(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND posting_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND posting_date <= %(to_date)s"
    
    data = frappe.db.sql(f"""
        SELECT 
            posting_date,
            SUM(total_fuel_sales_qty) as total_fuel_sales_qty,
            SUM(total_fuel_sales_amount) as total_fuel_sales_amount,
            SUM(lubricant_sales_amount) as lubricant_sales,
            SUM(accessories_sales_amount) as accessories_sales,
            SUM(total_sales_amount) as total_sales,
            SUM(cash_received) as cash_collection,
            SUM(total_online_collection) as online_collection,
            SUM(credit_sales_amount) as credit_sales,
            SUM(cash_shortage) - SUM(cash_excess) as variance
        FROM 
            `tabNozzle Shift Reading`
        WHERE 
            docstatus = 1
            {conditions}
        GROUP BY 
            posting_date
        ORDER BY 
            posting_date DESC
    """, filters, as_dict=1)
    
    return data

def get_chart_data(data):
    if not data:
        return None
    
    labels = [row.posting_date.strftime('%Y-%m-%d') for row in data]
    labels.reverse()
    
    sales_data = [row.total_sales for row in data]
    sales_data.reverse()
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Total Sales",
                    "values": sales_data
                }
            ]
        },
        "type": "line",
        "colors": ["#32a852"],
        "height": 250
    }
