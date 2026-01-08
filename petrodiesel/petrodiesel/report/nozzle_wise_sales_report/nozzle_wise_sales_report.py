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
            "label": _("Nozzle"),
            "fieldname": "nozzle",
            "fieldtype": "Link",
            "options": "Fuel Nozzle Master",
            "width": 120
        },
        {
            "label": _("Nozzle Name"),
            "fieldname": "nozzle_name",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Fuel Item"),
            "fieldname": "fuel_item",
            "fieldtype": "Link",
            "options": "Item",
            "width": 120
        },
        {
            "label": _("Cashier"),
            "fieldname": "cashier",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120
        },
        {
            "label": _("Total Qty (L)"),
            "fieldname": "total_qty",
            "fieldtype": "Float",
            "width": 120,
            "precision": 2
        },
        {
            "label": _("Testing Qty (L)"),
            "fieldname": "testing_qty",
            "fieldtype": "Float",
            "width": 110,
            "precision": 2
        },
        {
            "label": _("Actual Sale Qty (L)"),
            "fieldname": "actual_sale_qty",
            "fieldtype": "Float",
            "width": 140,
            "precision": 2
        },
        {
            "label": _("Total Amount"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Avg Rate/L"),
            "fieldname": "avg_rate",
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "label": _("Shift Count"),
            "fieldname": "shift_count",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Last Reading Date"),
            "fieldname": "last_reading_date",
            "fieldtype": "Date",
            "width": 120
        }
    ]

def get_data(filters):
    if not filters:
        filters = {}
    
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))
    
    conditions_sse = get_conditions_sse(filters)
    conditions_cwsse = get_conditions_cwsse(filters)
    
    # Query 1: Shift Sale Entry → Shift Nozzle Reading
    sse_query = f"""
        SELECT 
            snr.nozzle,
            snr.fuel_item,
            snr.cashier,
            SUM(snr.total_sale_qty) as total_qty,
            SUM(snr.testing_qty) as testing_qty,
            SUM(snr.actual_sale_qty) as actual_sale_qty,
            SUM(snr.amount) as total_amount,
            AVG(snr.rate_per_liter) as avg_rate,
            COUNT(DISTINCT sse.name) as shift_count,
            MAX(sse.posting_date) as last_reading_date
        FROM `tabShift Nozzle Reading` snr
        INNER JOIN `tabShift Sale Entry` sse ON snr.parent = sse.name
        WHERE sse.docstatus = 1
        {conditions_sse}
        GROUP BY snr.nozzle, snr.fuel_item, snr.cashier
    """
    
    # Query 2: Cashier Wise Shift Sale Entry → Nozzle Reading Detail
    cwsse_query = f"""
        SELECT 
            nrd.nozzle,
            nrd.fuel_item,
            cwsse.cashier,
            SUM(nrd.total_sale_qty) as total_qty,
            SUM(nrd.testing_qty) as testing_qty,
            SUM(nrd.actual_sale_qty) as actual_sale_qty,
            SUM(nrd.amount) as total_amount,
            AVG(nrd.rate_per_liter) as avg_rate,
            COUNT(DISTINCT cwsse.name) as shift_count,
            MAX(cwsse.posting_date) as last_reading_date
        FROM `tabNozzle Reading Detail` nrd
        INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON nrd.parent = cwsse.name
        WHERE cwsse.docstatus = 1
        {conditions_cwsse}
        GROUP BY nrd.nozzle, nrd.fuel_item, cwsse.cashier
    """
    
    # Combine both queries
    combined_query = f"""
        SELECT 
            nozzle,
            fuel_item,
            cashier,
            SUM(total_qty) as total_qty,
            SUM(testing_qty) as testing_qty,
            SUM(actual_sale_qty) as actual_sale_qty,
            SUM(total_amount) as total_amount,
            AVG(avg_rate) as avg_rate,
            SUM(shift_count) as shift_count,
            MAX(last_reading_date) as last_reading_date
        FROM (
            ({sse_query})
            UNION ALL
            ({cwsse_query})
        ) combined
        GROUP BY nozzle, fuel_item, cashier
        ORDER BY total_amount DESC
    """
    
    data = frappe.db.sql(combined_query, filters, as_dict=1)
    
    if not data:
        return []
    
    # Add nozzle names and cashier names
    for row in data:
        nozzle_doc = frappe.db.get_value("Fuel Nozzle Master", row.get("nozzle"), 
                                         ["nozzle_name", "nozzle_number"], as_dict=1)
        if nozzle_doc:
            row["nozzle_name"] = nozzle_doc.get("nozzle_name") or nozzle_doc.get("nozzle_number") or ""
        else:
            row["nozzle_name"] = row.get("nozzle", "")
    
    return data

def get_conditions_sse(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += f" AND sse.posting_date >= '{filters.get('from_date')}'"
    
    if filters.get("to_date"):
        conditions += f" AND sse.posting_date <= '{filters.get('to_date')}'"
    
    if filters.get("nozzle"):
        conditions += f" AND snr.nozzle = '{filters.get('nozzle')}'"
    
    if filters.get("fuel_item"):
        conditions += f" AND snr.fuel_item = '{filters.get('fuel_item')}'"
    
    if filters.get("cashier"):
        conditions += f" AND snr.cashier = '{filters.get('cashier')}'"
    
    if filters.get("shift"):
        conditions += f" AND sse.shift = '{filters.get('shift')}'"
    
    return conditions

def get_conditions_cwsse(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += f" AND cwsse.posting_date >= '{filters.get('from_date')}'"
    
    if filters.get("to_date"):
        conditions += f" AND cwsse.posting_date <= '{filters.get('to_date')}'"
    
    if filters.get("nozzle"):
        conditions += f" AND nrd.nozzle = '{filters.get('nozzle')}'"
    
    if filters.get("fuel_item"):
        conditions += f" AND nrd.fuel_item = '{filters.get('fuel_item')}'"
    
    if filters.get("cashier"):
        conditions += f" AND cwsse.cashier = '{filters.get('cashier')}'"
    
    if filters.get("shift"):
        conditions += f" AND cwsse.shift = '{filters.get('shift')}'"
    
    return conditions

def get_chart_data(data):
    if not data:
        return None
    
    # Top 10 nozzles by sales
    top_nozzles = data[:10]
    labels = [d.get("nozzle_name", "") or d.get("nozzle", "") for d in top_nozzles]
    values = [d.get("total_amount", 0) for d in top_nozzles]
    
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
        "type": "bar",
        "height": 300,
        "colors": ["#4C78FF"]
    }

def get_summary(data):
    if not data:
        return []
    
    total_qty = sum(d.get("actual_sale_qty", 0) for d in data)
    total_amount = sum(d.get("total_amount", 0) for d in data)
    testing_qty = sum(d.get("testing_qty", 0) for d in data)
    total_nozzles = len(set(d.get("nozzle") for d in data))
    
    return [
        {
            "value": total_qty,
            "label": "Total Sales Qty (L)",
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
            "value": testing_qty,
            "label": "Testing Qty (L)",
            "datatype": "Float",
            "indicator": "Orange"
        },
        {
            "value": total_nozzles,
            "label": "Active Nozzles",
            "datatype": "Int",
            "indicator": "Purple"
        }
    ]
