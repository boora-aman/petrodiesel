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
        {"label": _("Tank"), "fieldname": "tank", "fieldtype": "Link", "options": "Fuel Tank Master", "width": 130},
        {"label": _("Tank Name"), "fieldname": "tank_name", "fieldtype": "Data", "width": 150},
        {"label": _("Fuel Item"), "fieldname": "fuel_item", "fieldtype": "Link", "options": "Item", "width": 130},
        {"label": _("Opening Stock (L)"), "fieldname": "opening_stock", "fieldtype": "Float", "width": 140, "precision": 2},
        {"label": _("Receipts (L)"), "fieldname": "receipts", "fieldtype": "Float", "width": 120, "precision": 2},
        {"label": _("Consumption (L)"), "fieldname": "consumption", "fieldtype": "Float", "width": 140, "precision": 2},
        {"label": _("Closing Stock (L)"), "fieldname": "closing_stock", "fieldtype": "Float", "width": 140, "precision": 2},
        {"label": _("Physical Stock (L)"), "fieldname": "physical_stock", "fieldtype": "Float", "width": 140, "precision": 2},
        {"label": _("Variance (L)"), "fieldname": "variance", "fieldtype": "Float", "width": 120, "precision": 2},
        {"label": _("Variance %"), "fieldname": "variance_percentage", "fieldtype": "Percent", "width": 110},
        {"label": _("Tank Utilization %"), "fieldname": "utilization", "fieldtype": "Percent", "width": 140}
    ]

def get_data(filters):
    if not filters:
        filters = {}
    
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))
    
    # Get all tanks with correct field names
    tank_filter = "AND name = %(tank)s" if filters.get("tank") else ""
    fuel_filter = "AND fuel_item = %(fuel_item)s" if filters.get("fuel_item") else ""
    
    tanks_query = f"""
        SELECT 
            name as tank,
            tank_name,
            fuel_item,
            capacity_in_liters as total_capacity
        FROM `tabFuel Tank Master`
        WHERE 1=1
        {tank_filter}
        {fuel_filter}
    """
    
    tanks = frappe.db.sql(tanks_query, filters, as_dict=1)
    
    if not tanks:
        return []
    
    data = []
    
    for tank_row in tanks:
        tank = tank_row.get("tank")
        fuel_item = tank_row.get("fuel_item")
        capacity = flt(tank_row.get("total_capacity", 0))
        
        # Get opening stock (before from_date)
        opening = get_opening_stock(tank, fuel_item, filters.get("from_date"))
        
        # Get receipts (Tanker Receipt)
        receipts = get_receipts(tank, fuel_item, filters)
        
        # Get consumption (from Tank Consumption Summary)
        consumption = get_consumption(tank, fuel_item, filters)
        
        # Calculate closing stock
        closing = opening + receipts - consumption
        
        # Get latest physical stock from Tank Dip Reading
        physical = get_physical_stock(tank, fuel_item, filters)
        
        # Calculate variance
        variance = physical - closing if physical is not None else 0
        variance_pct = (variance / closing * 100) if closing > 0 else 0
        
        # Calculate utilization
        utilization = (closing / capacity * 100) if capacity > 0 else 0
        
        data.append({
            "tank": tank,
            "tank_name": tank_row.get("tank_name"),
            "fuel_item": fuel_item,
            "opening_stock": opening,
            "receipts": receipts,
            "consumption": consumption,
            "closing_stock": closing,
            "physical_stock": physical if physical is not None else closing,
            "variance": variance,
            "variance_percentage": variance_pct,
            "utilization": utilization
        })
    
    return data

def get_opening_stock(tank, fuel_item, from_date):
    """Get opening stock before from_date"""
    result = frappe.db.sql("""
        SELECT tdd.calculated_quantity_liters
        FROM `tabTank Dip Detail` tdd
        INNER JOIN `tabTank Dip Reading` tdr ON tdd.parent = tdr.name
        WHERE tdr.docstatus = 1
        AND tdd.tank = %s
        AND tdd.fuel_item = %s
        AND tdr.posting_date < %s
        ORDER BY tdr.posting_date DESC, tdr.posting_time DESC
        LIMIT 1
    """, (tank, fuel_item, from_date), as_dict=1)
    
    return flt(result[0].calculated_quantity_liters) if result else 0

def get_receipts(tank, fuel_item, filters):
    """Get total receipts from Tanker Receipt - using calculated_received_qty field"""
    result = frappe.db.sql("""
        SELECT SUM(tri.calculated_received_qty) as total_receipts
        FROM `tabTanker Receipt Item` tri
        INNER JOIN `tabTanker Receipt` tr ON tri.parent = tr.name
        WHERE tr.docstatus = 1
        AND tri.tank = %(tank)s
        AND tri.fuel_item = %(fuel_item)s
        AND tr.posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, {"tank": tank, "fuel_item": fuel_item, "from_date": filters.get("from_date"), "to_date": filters.get("to_date")}, as_dict=1)
    
    # Convert KL to Liters (calculated_received_qty is in KL)
    total_kl = flt(result[0].total_receipts) if result and result[0].total_receipts else 0
    return total_kl * 1000  # Convert KL to Liters

def get_consumption(tank, fuel_item, filters):
    """Get total consumption from Tank Consumption Summary"""
    result = frappe.db.sql("""
        SELECT SUM(tcs.total_consumption) as total_consumption
        FROM `tabTank Consumption Summary` tcs
        INNER JOIN `tabShift Sale Entry` sse ON tcs.parent = sse.name
        WHERE sse.docstatus = 1
        AND tcs.tank = %(tank)s
        AND tcs.fuel_item = %(fuel_item)s
        AND sse.posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, {"tank": tank, "fuel_item": fuel_item, "from_date": filters.get("from_date"), "to_date": filters.get("to_date")}, as_dict=1)
    
    consumption = flt(result[0].total_consumption) if result and result[0].total_consumption else 0
    
    return consumption

def get_physical_stock(tank, fuel_item, filters):
    """Get latest physical stock from Tank Dip Reading within period"""
    result = frappe.db.sql("""
        SELECT tdd.calculated_quantity_liters
        FROM `tabTank Dip Detail` tdd
        INNER JOIN `tabTank Dip Reading` tdr ON tdd.parent = tdr.name
        WHERE tdr.docstatus = 1
        AND tdd.tank = %s
        AND tdd.fuel_item = %s
        AND tdr.posting_date BETWEEN %s AND %s
        ORDER BY tdr.posting_date DESC, tdr.posting_time DESC
        LIMIT 1
    """, (tank, fuel_item, filters.get("from_date"), filters.get("to_date")), as_dict=1)
    
    return flt(result[0].calculated_quantity_liters) if result else None

def get_chart_data(data, filters):
    if not data:
        return None
    
    # If single tank, show stock movement trend
    if filters.get("tank") and len(data) == 1:
        row = data[0]
        labels = ["Opening", "Receipts", "Consumption", "Closing", "Physical"]
        values = [
            flt(row.get("opening_stock", 0)),
            flt(row.get("receipts", 0)),
            -flt(row.get("consumption", 0)),
            flt(row.get("closing_stock", 0)),
            flt(row.get("physical_stock", 0))
        ]
        
        return {
            "data": {"labels": labels, "datasets": [{"name": "Stock (L)", "values": values}]},
            "type": "bar",
            "height": 300,
            "colors": ["#4C78FF"]
        }
    
    # Otherwise show utilization comparison
    labels = [d.get("tank_name", "") or d.get("tank", "") for d in data]
    utilization_values = [flt(d.get("utilization", 0)) for d in data]
    
    return {
        "data": {"labels": labels, "datasets": [{"name": "Utilization %", "values": utilization_values}]},
        "type": "bar",
        "height": 300,
        "colors": ["#29CD42"]
    }

def get_summary(data):
    if not data:
        return []
    
    total_receipts = sum(flt(d.get("receipts", 0)) for d in data)
    total_consumption = sum(flt(d.get("consumption", 0)) for d in data)
    total_variance = sum(flt(d.get("variance", 0)) for d in data)
    avg_utilization = sum(flt(d.get("utilization", 0)) for d in data) / len(data) if data else 0
    
    return [
        {"value": total_receipts, "label": "Total Receipts (L)", "datatype": "Float", "indicator": "Green"},
        {"value": total_consumption, "label": "Total Consumption (L)", "datatype": "Float", "indicator": "Blue"},
        {"value": abs(total_variance), "label": "Total Variance (L)", "datatype": "Float", "indicator": "Red" if total_variance < 0 else "Orange"},
        {"value": avg_utilization, "label": "Avg Utilization %", "datatype": "Percent", "indicator": "Purple"},
        {"value": len(data), "label": "Active Tanks", "datatype": "Int", "indicator": "Blue"}
    ]
