# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    summary = get_summary(data)
    return columns, data, None, chart, summary

def get_columns():
    return [
        {
            "label": _("Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Tank"),
            "fieldname": "tank",
            "fieldtype": "Link",
            "options": "Fuel Tank Master",
            "width": 120
        },
        {
            "label": _("Tank Name"),
            "fieldname": "tank_name",
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
            "label": _("Shift"),
            "fieldname": "shift",
            "fieldtype": "Link",
            "options": "Shift Master",
            "width": 100
        },
        {
            "label": _("Dip Reading (L)"),
            "fieldname": "dip_stock",
            "fieldtype": "Float",
            "width": 130,
            "precision": 2
        },
        {
            "label": _("System Stock (L)"),
            "fieldname": "system_stock",
            "fieldtype": "Float",
            "width": 130,
            "precision": 2
        },
        {
            "label": _("Variance (L)"),
            "fieldname": "variance",
            "fieldtype": "Float",
            "width": 120,
            "precision": 2
        },
        {
            "label": _("Variance %"),
            "fieldname": "variance_percentage",
            "fieldtype": "Percent",
            "width": 110
        },
        {
            "label": _("Temperature (°C)"),
            "fieldname": "temperature",
            "fieldtype": "Float",
            "width": 120,
            "precision": 1
        },
        {
            "label": _("Density"),
            "fieldname": "density",
            "fieldtype": "Float",
            "width": 100,
            "precision": 3
        },
        {
            "label": _("Recorded By"),
            "fieldname": "recorded_by",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 130
        },
        {
            "label": _("Variance Reason"),
            "fieldname": "reason_for_variance",
            "fieldtype": "Data",
            "width": 150
        }
    ]

def get_data(filters):
    if not filters:
        filters = {}
    
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))
    
    params = {}
    conditions = get_conditions(filters, params)
    
    # Get Tank Dip Reading with details
    query = f"""
        SELECT 
            tdr.posting_date,
            tdr.shift,
            tdr.recorded_by,
            tdr.reason_for_variance,
            tdd.tank,
            tdd.fuel_item,
            tdd.dip_height_mm,
            tdd.calculated_quantity_liters as dip_stock,
            tdd.temperature_celsius as temperature,
            tdd.density,
            tdr.total_stock_as_per_system as system_stock,
            tdr.variance,
            tdr.variance_percentage
        FROM `tabTank Dip Detail` tdd
        INNER JOIN `tabTank Dip Reading` tdr ON tdd.parent = tdr.name
        WHERE tdr.docstatus = 1
        {conditions}
        ORDER BY tdr.posting_date DESC, tdd.tank
    """
    
    data = frappe.db.sql(query, params, as_dict=1)
    
    if not data:
        return []
    
    # Add tank names and calculate variance if not present
    for row in data:
        # Get tank name (simplified - only tank_name field)
        tank_name = frappe.db.get_value("Fuel Tank Master", row.get("tank"), "tank_name")
        row["tank_name"] = tank_name or row.get("tank", "")
        
        # Calculate variance if not in parent
        if row.get("variance") is None:
            dip = flt(row.get("dip_stock", 0))
            system = flt(row.get("system_stock", 0))
            row["variance"] = dip - system
            row["variance_percentage"] = ((dip - system) / system * 100) if system > 0 else 0
    
    return data


def get_conditions(filters, params):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND tdr.posting_date >= %(from_date)s"
        params["from_date"] = filters.get("from_date")
    
    if filters.get("to_date"):
        conditions += " AND tdr.posting_date <= %(to_date)s"
        params["to_date"] = filters.get("to_date")
    
    if filters.get("tank"):
        conditions += " AND tdd.tank = %(tank)s"
        params["tank"] = filters.get("tank")
    
    if filters.get("fuel_item"):
        conditions += " AND tdd.fuel_item = %(fuel_item)s"
        params["fuel_item"] = filters.get("fuel_item")
    
    if filters.get("shift"):
        conditions += " AND tdr.shift = %(shift)s"
        params["shift"] = filters.get("shift")
    
    if filters.get("show_variance_only"):
        conditions += " AND ABS(tdr.variance) > 0"
    
    if filters.get("variance_threshold"):
        threshold = flt(filters.get("variance_threshold"))
        conditions += f" AND ABS(tdr.variance) >= {threshold}"
    
    return conditions

def get_chart_data(data):
    if not data:
        return None
    
    # Group by date and show variance trend
    date_variance = {}
    for row in data:
        date = row.get("posting_date")
        variance = flt(row.get("variance", 0))
        if date not in date_variance:
            date_variance[date] = 0
        date_variance[date] += variance
    
    labels = sorted(date_variance.keys())
    values = [date_variance[date] for date in labels]
    
    return {
        "data": {
            "labels": [str(label) for label in labels],
            "datasets": [
                {
                    "name": "Total Variance (L)",
                    "values": values
                }
            ]
        },
        "type": "line",
        "height": 300,
        "colors": ["#ff5858"],
        "axisOptions": {
            "xIsSeries": 1
        }
    }

def get_summary(data):
    if not data:
        return []
    
    total_dip = sum(flt(d.get("dip_stock", 0)) for d in data)
    total_system = sum(flt(d.get("system_stock", 0)) for d in data)
    total_variance = sum(flt(d.get("variance", 0)) for d in data)
    
    # Count positive and negative variances
    positive_variance = sum(1 for d in data if flt(d.get("variance", 0)) > 0)
    negative_variance = sum(1 for d in data if flt(d.get("variance", 0)) < 0)
    
    # Average variance percentage
    avg_variance_pct = sum(flt(d.get("variance_percentage", 0)) for d in data) / len(data) if data else 0
    
    return [
        {
            "value": total_variance,
            "label": "Total Variance (L)",
            "datatype": "Float",
            "indicator": "Red" if total_variance < 0 else "Orange"
        },
        {
            "value": avg_variance_pct,
            "label": "Avg Variance %",
            "datatype": "Percent",
            "indicator": "Blue"
        },
        {
            "value": positive_variance,
            "label": "Excess Stock Readings",
            "datatype": "Int",
            "indicator": "Green"
        },
        {
            "value": negative_variance,
            "label": "Shortage Readings",
            "datatype": "Int",
            "indicator": "Red"
        },
        {
            "value": len(data),
            "label": "Total Readings",
            "datatype": "Int",
            "indicator": "Purple"
        }
    ]
