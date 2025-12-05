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
    columns = [
        {
            "fieldname": "fuel_item",
            "label": _("Fuel Type"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 150
        },
        {
            "fieldname": "total_quantity",
            "label": _("Total Quantity (L)"),
            "fieldtype": "Float",
            "width": 130,
            "precision": 2
        },
        {
            "fieldname": "testing_quantity",
            "label": _("Testing (L)"),
            "fieldtype": "Float",
            "width": 100,
            "precision": 2
        },
        {
            "fieldname": "actual_sale_qty",
            "label": _("Actual Sale (L)"),
            "fieldtype": "Float",
            "width": 130,
            "precision": 2
        },
        {
            "fieldname": "avg_rate",
            "label": _("Avg Rate/L"),
            "fieldtype": "Currency",
            "width": 110,
            "precision": 2
        },
        {
            "fieldname": "total_amount",
            "label": _("Total Amount"),
            "fieldtype": "Currency",
            "width": 140,
            "precision": 2
        },
        {
            "fieldname": "percentage",
            "label": _("% Contribution"),
            "fieldtype": "Percent",
            "width": 120,
            "precision": 2
        }
    ]
    
    # Add date column if grouping by date
    if filters.get("group_by") == "Date":
        columns.insert(0, {
            "fieldname": "posting_date",
            "label": _("Date"),
            "fieldtype": "Date",
            "width": 100
        })
    
    return columns

def get_data(filters):
    conditions = get_conditions(filters)
    
    # Determine grouping
    group_by = ""
    if filters.get("group_by") == "Date":
        group_by = "nsr.posting_date, nrd.fuel_item"
    else:
        group_by = "nrd.fuel_item"
    
    # Build query
    data = frappe.db.sql(f"""
        SELECT 
            {f'nsr.posting_date,' if filters.get("group_by") == "Date" else ''}
            nrd.fuel_item,
            SUM(nrd.total_sale_qty) as total_quantity,
            SUM(nrd.testing_qty) as testing_quantity,
            SUM(nrd.actual_sale_qty) as actual_sale_qty,
            AVG(nrd.rate_per_liter) as avg_rate,
            SUM(nrd.amount) as total_amount
        FROM 
            `tabNozzle Shift Reading` nsr
        INNER JOIN 
            `tabNozzle Reading Detail` nrd ON nrd.parent = nsr.name
        WHERE 
            nsr.docstatus = 1
            {conditions}
        GROUP BY 
            {group_by}
        ORDER BY 
            {f'nsr.posting_date DESC,' if filters.get("group_by") == "Date" else ''} 
            total_amount DESC
    """, filters, as_dict=1)
    
    # Calculate percentage contribution
    total_amount = sum(row.total_amount for row in data)
    for row in data:
        row.percentage = (row.total_amount / total_amount * 100) if total_amount else 0
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND nsr.posting_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND nsr.posting_date <= %(to_date)s"
    
    if filters.get("fuel_item"):
        conditions += " AND nrd.fuel_item = %(fuel_item)s"
    
    if filters.get("shift"):
        conditions += " AND nsr.shift = %(shift)s"
    
    return conditions

def get_chart_data(data, filters):
    if not data:
        return None
    
    # Group data for chart
    chart_data = {}
    for row in data:
        fuel = row.fuel_item
        if fuel not in chart_data:
            chart_data[fuel] = 0
        chart_data[fuel] += row.total_amount
    
    return {
        "data": {
            "labels": list(chart_data.keys()),
            "datasets": [
                {
                    "name": "Sales Amount",
                    "values": list(chart_data.values())
                }
            ]
        },
        "type": "donut" if filters.get("group_by") != "Date" else "bar",
        "colors": ["#29CD42", "#5E64FF", "#F683AE"],
        "height": 300
    }
