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
            "fieldname": "tank",
            "label": _("Tank"),
            "fieldtype": "Link",
            "options": "Fuel Tank Master",
            "width": 150
        },
        {
            "fieldname": "fuel_item",
            "label": _("Fuel Type"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 120
        },
        {
            "fieldname": "dip_reading",
            "label": _("Dip Reading (mm)"),
            "fieldtype": "Float",
            "width": 130,
            "precision": 2
        },
        {
            "fieldname": "physical_stock",
            "label": _("Physical Stock (L)"),
            "fieldtype": "Float",
            "width": 140,
            "precision": 2
        },
        {
            "fieldname": "system_stock",
            "label": _("System Stock (L)"),
            "fieldtype": "Float",
            "width": 130,
            "precision": 2
        },
        {
            "fieldname": "variance",
            "label": _("Variance (L)"),
            "fieldtype": "Float",
            "width": 110,
            "precision": 2
        },
        {
            "fieldname": "variance_percentage",
            "label": _("Variance %"),
            "fieldtype": "Percent",
            "width": 110,
            "precision": 2
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 100
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql(f"""
        SELECT 
            tdr.posting_date,
            tdd.tank,
            tdd.fuel_item,
            tdd.dip_height_mm as dip_reading,
            tdd.calculated_quantity_liters as physical_stock,
            (
                SELECT IFNULL(SUM(actual_qty), 0)
                FROM `tabBin` b
                INNER JOIN `tabFuel Tank Master` ftm ON ftm.warehouse = b.warehouse
                WHERE ftm.name = tdd.tank
                AND b.item_code = tdd.fuel_item
            ) as system_stock,
            (tdd.calculated_quantity_liters - (
                SELECT IFNULL(SUM(actual_qty), 0)
                FROM `tabBin` b
                INNER JOIN `tabFuel Tank Master` ftm ON ftm.warehouse = b.warehouse
                WHERE ftm.name = tdd.tank
                AND b.item_code = tdd.fuel_item
            )) as variance,
            CASE 
                WHEN (
                    SELECT IFNULL(SUM(actual_qty), 0)
                    FROM `tabBin` b
                    INNER JOIN `tabFuel Tank Master` ftm ON ftm.warehouse = b.warehouse
                    WHERE ftm.name = tdd.tank
                    AND b.item_code = tdd.fuel_item
                ) > 0 THEN
                    ((tdd.calculated_quantity_liters - (
                        SELECT IFNULL(SUM(actual_qty), 0)
                        FROM `tabBin` b
                        INNER JOIN `tabFuel Tank Master` ftm ON ftm.warehouse = b.warehouse
                        WHERE ftm.name = tdd.tank
                        AND b.item_code = tdd.fuel_item
                    )) / (
                        SELECT IFNULL(SUM(actual_qty), 0)
                        FROM `tabBin` b
                        INNER JOIN `tabFuel Tank Master` ftm ON ftm.warehouse = b.warehouse
                        WHERE ftm.name = tdd.tank
                        AND b.item_code = tdd.fuel_item
                    ) * 100)
                ELSE 0
            END as variance_percentage,
            CASE 
                WHEN ABS((tdd.calculated_quantity_liters - (
                    SELECT IFNULL(SUM(actual_qty), 0)
                    FROM `tabBin` b
                    INNER JOIN `tabFuel Tank Master` ftm ON ftm.warehouse = b.warehouse
                    WHERE ftm.name = tdd.tank
                    AND b.item_code = tdd.fuel_item
                )) / NULLIF((
                    SELECT IFNULL(SUM(actual_qty), 0)
                    FROM `tabBin` b
                    INNER JOIN `tabFuel Tank Master` ftm ON ftm.warehouse = b.warehouse
                    WHERE ftm.name = tdd.tank
                    AND b.item_code = tdd.fuel_item
                ), 0) * 100) > 2 THEN 'High Variance'
                WHEN ABS((tdd.calculated_quantity_liters - (
                    SELECT IFNULL(SUM(actual_qty), 0)
                    FROM `tabBin` b
                    INNER JOIN `tabFuel Tank Master` ftm ON ftm.warehouse = b.warehouse
                    WHERE ftm.name = tdd.tank
                    AND b.item_code = tdd.fuel_item
                )) / NULLIF((
                    SELECT IFNULL(SUM(actual_qty), 0)
                    FROM `tabBin` b
                    INNER JOIN `tabFuel Tank Master` ftm ON ftm.warehouse = b.warehouse
                    WHERE ftm.name = tdd.tank
                    AND b.item_code = tdd.fuel_item
                ), 0) * 100) > 1 THEN 'Medium Variance'
                ELSE 'Normal'
            END as status
        FROM 
            `tabTank Dip Reading` tdr
        INNER JOIN 
            `tabTank Dip Detail` tdd ON tdd.parent = tdr.name
        WHERE 
            tdr.docstatus = 1
            {conditions}
        ORDER BY 
            tdr.posting_date DESC, variance_percentage DESC
    """, filters, as_dict=1)
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND tdr.posting_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND tdr.posting_date <= %(to_date)s"
    
    if filters.get("tank"):
        conditions += " AND tdd.tank = %(tank)s"
    
    if filters.get("fuel_item"):
        conditions += " AND tdd.fuel_item = %(fuel_item)s"
    
    return conditions

def get_chart_data(data):
    if not data:
        return None
    
    # Group by fuel type
    fuel_variance = {}
    for row in data:
        fuel = row.fuel_item
        if fuel not in fuel_variance:
            fuel_variance[fuel] = []
        fuel_variance[fuel].append(abs(row.variance or 0))
    
    # Average variance per fuel
    avg_variance = {k: sum(v)/len(v) if len(v) > 0 else 0 for k, v in fuel_variance.items()}
    
    return {
        "data": {
            "labels": list(avg_variance.keys()),
            "datasets": [
                {
                    "name": "Avg Variance (L)",
                    "values": list(avg_variance.values())
                }
            ]
        },
        "type": "bar",
        "colors": ["#FFA00A"],
        "height": 250
    }
