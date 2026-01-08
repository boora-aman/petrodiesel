# Copyright (c) 2025, AlfaStack and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    summary = get_summary(data)
    return columns, data, None, chart, summary

def get_columns():
    return [
        {"label": _("Date"), "fieldname": "effective_date", "fieldtype": "Date", "width": 110},
        {"label": _("Time"), "fieldname": "effective_time", "fieldtype": "Time", "width": 100},
        {"label": _("Fuel Item"), "fieldname": "fuel_item", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("Fuel Name"), "fieldname": "fuel_name", "fieldtype": "Data", "width": 150},
        {"label": _("Old Price"), "fieldname": "old_price", "fieldtype": "Currency", "width": 120},
        {"label": _("New Price"), "fieldname": "new_price", "fieldtype": "Currency", "width": 120},
        {"label": _("Change Amount"), "fieldname": "change_amount", "fieldtype": "Currency", "width": 130},
        {"label": _("Change %"), "fieldname": "change_percentage", "fieldtype": "Percent", "width": 100},
        {"label": _("Notification Source"), "fieldname": "notification_source", "fieldtype": "Data", "width": 150},
        {"label": _("Approved By"), "fieldname": "approved_by", "fieldtype": "Link", "options": "Employee", "width": 140}
    ]

def get_data(filters):
    if not filters:
        filters = {}
    
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))
    
    # Query Fuel Price Update with items
    query = """
        SELECT 
            fpu.effective_date,
            fpu.effective_time,
            fpu.notification_source,
            fpu.approved_by,
            fpui.fuel_item,
            fpui.old_price,
            fpui.new_price,
            fpui.change_amount,
            fpui.change_percentage
        FROM `tabFuel Price Update Item` fpui
        INNER JOIN `tabFuel Price Update` fpu ON fpui.parent = fpu.name
        WHERE fpu.docstatus = 1
        AND fpu.effective_date BETWEEN %(from_date)s AND %(to_date)s
        {fuel_item_filter}
        {source_filter}
        ORDER BY fpu.effective_date DESC, fpu.effective_time DESC, fpui.fuel_item
    """
    
    # Build filters
    fuel_item_filter = "AND fpui.fuel_item = %(fuel_item)s" if filters.get("fuel_item") else ""
    source_filter = "AND fpu.notification_source = %(notification_source)s" if filters.get("notification_source") else ""
    
    query = query.format(fuel_item_filter=fuel_item_filter, source_filter=source_filter)
    
    data = frappe.db.sql(query, filters, as_dict=1)
    
    if not data:
        return []
    
    # Add fuel names
    for row in data:
        fuel_name = frappe.db.get_value("Item", row.get("fuel_item"), "item_name")
        row["fuel_name"] = fuel_name or row.get("fuel_item", "")
    
    return data

def get_chart_data(data, filters):
    if not data:
        return None
    
    # Group by fuel item for trend chart
    fuel_items = {}
    for row in data:
        fuel_item = row.get("fuel_item")
        if fuel_item not in fuel_items:
            fuel_items[fuel_item] = []
        fuel_items[fuel_item].append({
            "date": row.get("effective_date"),
            "price": flt(row.get("new_price", 0))
        })
    
    # If specific fuel item selected, show price trend
    if filters.get("fuel_item"):
        selected_fuel = filters.get("fuel_item")
        if selected_fuel in fuel_items:
            # Sort by date
            trend_data = sorted(fuel_items[selected_fuel], key=lambda x: x["date"])
            labels = [str(d["date"]) for d in trend_data]
            values = [d["price"] for d in trend_data]
            
            return {
                "data": {
                    "labels": labels,
                    "datasets": [
                        {"name": "Price", "values": values}
                    ]
                },
                "type": "line",
                "height": 300,
                "colors": ["#4C78FF"],
                "axisOptions": {"xIsSeries": 1}
            }
    
    # Otherwise show price change breakdown
    increases = sum(1 for d in data if flt(d.get("change_amount", 0)) > 0)
    decreases = sum(1 for d in data if flt(d.get("change_amount", 0)) < 0)
    no_change = sum(1 for d in data if flt(d.get("change_amount", 0)) == 0)
    
    return {
        "data": {
            "labels": ["Price Increased", "Price Decreased", "No Change"],
            "datasets": [
                {"name": "Count", "values": [increases, decreases, no_change]}
            ]
        },
        "type": "donut",
        "height": 300,
        "colors": ["#ff5858", "#29CD42", "#ffa00a"]
    }

def get_summary(data):
    if not data:
        return []
    
    total_updates = len(data)
    
    # Count increases and decreases
    increases = sum(1 for d in data if flt(d.get("change_amount", 0)) > 0)
    decreases = sum(1 for d in data if flt(d.get("change_amount", 0)) < 0)
    
    # Average change
    avg_change = sum(flt(d.get("change_amount", 0)) for d in data) / total_updates if total_updates > 0 else 0
    
    # Biggest increase and decrease
    biggest_increase = max((flt(d.get("change_amount", 0)) for d in data), default=0)
    biggest_decrease = min((flt(d.get("change_amount", 0)) for d in data), default=0)
    
    # Latest price for each fuel
    fuel_latest = {}
    for row in data:
        fuel = row.get("fuel_item")
        if fuel not in fuel_latest:
            fuel_latest[fuel] = row.get("new_price", 0)
    
    return [
        {"value": total_updates, "label": "Total Price Updates", "datatype": "Int", "indicator": "Blue"},
        {"value": increases, "label": "Price Increases", "datatype": "Int", "indicator": "Red"},
        {"value": decreases, "label": "Price Decreases", "datatype": "Int", "indicator": "Green"},
        {"value": avg_change, "label": "Avg Change", "datatype": "Currency", "indicator": "Orange"},
        {"value": biggest_increase, "label": "Biggest Increase", "datatype": "Currency", "indicator": "Red"}
    ]
