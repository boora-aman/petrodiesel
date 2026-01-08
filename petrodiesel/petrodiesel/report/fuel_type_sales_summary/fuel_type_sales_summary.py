# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    summary = get_summary(data)
    return columns, data, None, chart, summary

def get_columns():
    return [
        {
            "label": _("Fuel Item"),
            "fieldname": "fuel_item",
            "fieldtype": "Link",
            "options": "Item",
            "width": 150
        },
        {
            "label": _("Fuel Name"),
            "fieldname": "fuel_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Total Qty (L)"),
            "fieldname": "total_qty",
            "fieldtype": "Float",
            "width": 120,
            "precision": 2
        },
        {
            "label": _("Total Amount"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Avg Rate/L"),
            "fieldname": "avg_rate",
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "label": _("Min Rate/L"),
            "fieldname": "min_rate",
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "label": _("Max Rate/L"),
            "fieldname": "max_rate",
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "label": _("Transactions"),
            "fieldname": "transaction_count",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("% of Total"),
            "fieldname": "sales_percentage",
            "fieldtype": "Percent",
            "width": 110
        }
    ]

def get_data(filters):
    if not filters:
        filters = {}
    
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))
    
    conditions_sse = get_conditions_sse(filters)
    conditions_cwsse = get_conditions_cwsse(filters)
    
    # Query 1: Shift Sale Entry → Fuel Type Sales Summary
    sse_query = f"""
        SELECT 
            ftss.fuel_item,
            SUM(ftss.total_qty) as total_qty,
            SUM(ftss.total_amount) as total_amount,
            AVG(ftss.rate) as avg_rate,
            MIN(ftss.rate) as min_rate,
            MAX(ftss.rate) as max_rate,
            COUNT(*) as transaction_count
        FROM `tabFuel Type Sales Summary` ftss
        INNER JOIN `tabShift Sale Entry` sse ON ftss.parent = sse.name
        WHERE sse.docstatus = 1
        {conditions_sse}
        GROUP BY ftss.fuel_item
    """
    
    # Query 2: Cashier Wise Shift Sale Entry → Nozzle Reading Detail
    cwsse_query = f"""
        SELECT 
            nrd.fuel_item,
            SUM(nrd.actual_sale_qty) as total_qty,
            SUM(nrd.amount) as total_amount,
            AVG(nrd.rate_per_liter) as avg_rate,
            MIN(nrd.rate_per_liter) as min_rate,
            MAX(nrd.rate_per_liter) as max_rate,
            COUNT(*) as transaction_count
        FROM `tabNozzle Reading Detail` nrd
        INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON nrd.parent = cwsse.name
        WHERE cwsse.docstatus = 1
        {conditions_cwsse}
        GROUP BY nrd.fuel_item
    """
    
    # Combine both queries
    combined_query = f"""
        SELECT 
            fuel_item,
            SUM(total_qty) as total_qty,
            SUM(total_amount) as total_amount,
            AVG(avg_rate) as avg_rate,
            MIN(min_rate) as min_rate,
            MAX(max_rate) as max_rate,
            SUM(transaction_count) as transaction_count
        FROM (
            ({sse_query})
            UNION ALL
            ({cwsse_query})
        ) combined
        GROUP BY fuel_item
        ORDER BY total_amount DESC
    """
    
    data = frappe.db.sql(combined_query, filters, as_dict=1)
    
    if not data:
        return []
    
    # Calculate total for percentage
    total_sales = sum(d.get("total_amount", 0) for d in data)
    
    # Add fuel names and percentage
    for row in data:
        row["fuel_name"] = frappe.db.get_value("Item", row.get("fuel_item"), "item_name") or row.get("fuel_item", "")
        row["sales_percentage"] = (row.get("total_amount", 0) / total_sales * 100) if total_sales > 0 else 0
    
    return data

def get_conditions_sse(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += f" AND sse.posting_date >= '{filters.get('from_date')}'"
    
    if filters.get("to_date"):
        conditions += f" AND sse.posting_date <= '{filters.get('to_date')}'"
    
    if filters.get("fuel_item"):
        conditions += f" AND ftss.fuel_item = '{filters.get('fuel_item')}'"
    
    if filters.get("shift"):
        conditions += f" AND sse.shift = '{filters.get('shift')}'"
    
    return conditions

def get_conditions_cwsse(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += f" AND cwsse.posting_date >= '{filters.get('from_date')}'"
    
    if filters.get("to_date"):
        conditions += f" AND cwsse.posting_date <= '{filters.get('to_date')}'"
    
    if filters.get("fuel_item"):
        conditions += f" AND nrd.fuel_item = '{filters.get('fuel_item')}'"
    
    if filters.get("shift"):
        conditions += f" AND cwsse.shift = '{filters.get('shift')}'"
    
    return conditions

def get_chart_data(data):
    if not data:
        return None
    
    labels = [d.get("fuel_name", "") or d.get("fuel_item", "") for d in data]
    values = [d.get("total_amount", 0) for d in data]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Sales Amount",
                    "values": values
                }
            ]
        },
        "type": "donut",
        "height": 300,
        "colors": ["#29CD42", "#4C78FF", "#ffa00a", "#743ee2", "#ff5858"]
    }

def get_summary(data):
    if not data:
        return []
    
    total_qty = sum(d.get("total_qty", 0) for d in data)
    total_amount = sum(d.get("total_amount", 0) for d in data)
    total_transactions = sum(d.get("transaction_count", 0) for d in data)
    
    return [
        {
            "value": total_qty,
            "label": "Total Quantity (L)",
            "datatype": "Float",
            "indicator": "Blue"
        },
        {
            "value": total_amount,
            "label": "Total Sales Amount",
            "datatype": "Currency",
            "indicator": "Green"
        },
        {
            "value": total_transactions,
            "label": "Total Transactions",
            "datatype": "Int",
            "indicator": "Orange"
        },
        {
            "value": len(data),
            "label": "Fuel Types",
            "datatype": "Int",
            "indicator": "Purple"
        }
    ]
