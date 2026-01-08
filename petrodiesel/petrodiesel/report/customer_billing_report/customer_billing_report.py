# Copyright (c) 2025, AlfaStack and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    if not filters:
        filters = {}
    
    if not filters.get("customer"):
        frappe.throw(_("Please select a Customer"))
    
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
            "label": _("Vehicle Number"),
            "fieldname": "vehicle_number",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Driver Name"),
            "fieldname": "driver_name",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Transaction Type"),
            "fieldname": "transaction_type",
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
            "label": _("Qty (L)"),
            "fieldname": "quantity_liters",
            "fieldtype": "Float",
            "width": 100,
            "precision": 2
        },
        {
            "label": _("Rate/L"),
            "fieldname": "rate_per_liter",
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "label": _("Fuel Amount"),
            "fieldname": "fuel_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Cash Given"),
            "fieldname": "cash_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Total Amount"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Slip Number"),
            "fieldname": "slip_number",
            "fieldtype": "Data",
            "width": 110
        },
        {
            "label": _("Shift"),
            "fieldname": "shift",
            "fieldtype": "Link",
            "options": "Shift Master",
            "width": 100
        },
        {
            "label": _("Cashier"),
            "fieldname": "cashier",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 130
        }
    ]

def get_data(filters):
    customer = filters.get("customer")
    
    date_conditions_sse = ""
    if filters.get("from_date"):
        date_conditions_sse += f" AND sse.posting_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"):
        date_conditions_sse += f" AND sse.posting_date <= '{filters.get('to_date')}'"
    if filters.get("vehicle_number"):
        date_conditions_sse += f" AND scs.vehicle_number = '{filters.get('vehicle_number')}'"
    
    date_conditions_cwsse = ""
    if filters.get("from_date"):
        date_conditions_cwsse += f" AND cwsse.posting_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"):
        date_conditions_cwsse += f" AND cwsse.posting_date <= '{filters.get('to_date')}'"
    if filters.get("vehicle_number"):
        date_conditions_cwsse += f" AND csi.vehicle_number = '{filters.get('vehicle_number')}'"
    
    # Query 1: Shift Sale Entry → Shift Credit Sale (Fuel)
    fuel_sse_query = f"""
        SELECT 
            sse.posting_date,
            sse.shift,
            scs.cashier,
            COALESCE(scs.vehicle_number, 'WALK-IN') as vehicle_number,
            scs.driver_name,
            'Credit Fuel Sale' as transaction_type,
            scs.fuel_item,
            scs.quantity_liters,
            scs.rate_per_liter,
            scs.amount as fuel_amount,
            0 as cash_amount,
            scs.amount as total_amount,
            scs.slip_number
        FROM `tabShift Credit Sale` scs
        INNER JOIN `tabShift Sale Entry` sse ON scs.parent = sse.name
        WHERE sse.docstatus = 1
        AND scs.customer = '{customer}'
        {date_conditions_sse}
    """
    
    # Query 2: Shift Sale Entry → Shift Driver Cash
    cash_sse_query = f"""
        SELECT 
            sse.posting_date,
            sse.shift,
            sdc.cashier,
            COALESCE(sdc.vehicle_number, 'WALK-IN') as vehicle_number,
            sdc.driver_name,
            'Driver Cash Advance' as transaction_type,
            NULL as fuel_item,
            0 as quantity_liters,
            0 as rate_per_liter,
            0 as fuel_amount,
            sdc.cash_amount,
            sdc.cash_amount as total_amount,
            sdc.slip_number
        FROM `tabShift Driver Cash` sdc
        INNER JOIN `tabShift Sale Entry` sse ON sdc.parent = sse.name
        WHERE sse.docstatus = 1
        AND sdc.customer = '{customer}'
        {date_conditions_sse}
    """
    
    # Query 3: Cashier Wise Shift Sale Entry → Credit Sale Item (Fuel)
    fuel_cwsse_query = f"""
        SELECT 
            cwsse.posting_date,
            cwsse.shift,
            cwsse.cashier,
            COALESCE(csi.vehicle_number, 'WALK-IN') as vehicle_number,
            csi.driver_name,
            'Credit Fuel Sale' as transaction_type,
            csi.fuel_item,
            csi.quantity_liters,
            csi.rate_per_liter,
            csi.amount as fuel_amount,
            0 as cash_amount,
            csi.amount as total_amount,
            csi.slip_number
        FROM `tabCredit Sale Item` csi
        INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON csi.parent = cwsse.name
        WHERE cwsse.docstatus = 1
        AND csi.customer_name = '{customer}'
        {date_conditions_cwsse}
    """
    
    # Query 4: Cashier Wise Shift Sale Entry → Driver Cash Advance
    cash_cwsse_query = f"""
        SELECT 
            cwsse.posting_date,
            cwsse.shift,
            cwsse.cashier,
            COALESCE(dca.vehicle_number, 'WALK-IN') as vehicle_number,
            dca.driver_name,
            'Driver Cash Advance' as transaction_type,
            NULL as fuel_item,
            0 as quantity_liters,
            0 as rate_per_liter,
            0 as fuel_amount,
            dca.cash_amount,
            dca.cash_amount as total_amount,
            NULL as slip_number
        FROM `tabDriver Cash Advance` dca
        INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON dca.parent = cwsse.name
        WHERE cwsse.docstatus = 1
        AND dca.customer = '{customer}'
        {date_conditions_cwsse}
    """
    
    # Query 5: Credit Sale (standalone)
    cs_conditions = ""
    if filters.get("from_date"):
        cs_conditions += f" AND cs.posting_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"):
        cs_conditions += f" AND cs.posting_date <= '{filters.get('to_date')}'"
    
    fuel_cs_query = f"""
        SELECT 
            cs.posting_date,
            cs.shift,
            NULL as cashier,
            'WALK-IN' as vehicle_number,
            '' as driver_name,
            'Credit Fuel Sale' as transaction_type,
            csi.fuel_item,
            csi.quantity_liters,
            csi.rate_per_liter,
            csi.amount as fuel_amount,
            0 as cash_amount,
            csi.amount as total_amount,
            NULL as slip_number
        FROM `tabCredit Sale Item` csi
        INNER JOIN `tabCredit Sale` cs ON csi.parent = cs.name
        WHERE cs.docstatus = 1
        AND cs.customer = '{customer}'
        {cs_conditions}
    """
    
    # Combine all queries
    combined_query = f"""
        SELECT * FROM (
            ({fuel_sse_query})
            UNION ALL
            ({cash_sse_query})
            UNION ALL
            ({fuel_cwsse_query})
            UNION ALL
            ({cash_cwsse_query})
            UNION ALL
            ({fuel_cs_query})
        ) combined
        ORDER BY posting_date DESC, vehicle_number, transaction_type
    """
    
    data = frappe.db.sql(combined_query, as_dict=1)
    
    return data

def get_chart_data(data):
    if not data:
        return None
    
    # Vehicle-wise breakdown
    vehicle_totals = {}
    for row in data:
        vehicle = row.get("vehicle_number", "WALK-IN")
        if vehicle not in vehicle_totals:
            vehicle_totals[vehicle] = 0
        vehicle_totals[vehicle] += flt(row.get("total_amount", 0))
    
    labels = list(vehicle_totals.keys())
    values = list(vehicle_totals.values())
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Total Amount",
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
    
    total_fuel_amount = sum(flt(d.get("fuel_amount", 0)) for d in data)
    total_cash_given = sum(flt(d.get("cash_amount", 0)) for d in data)
    total_amount = sum(flt(d.get("total_amount", 0)) for d in data)
    total_qty = sum(flt(d.get("quantity_liters", 0)) for d in data)
    unique_vehicles = len(set(d.get("vehicle_number") for d in data))
    
    return [
        {
            "value": total_amount,
            "label": "Total Outstanding",
            "datatype": "Currency",
            "indicator": "Red"
        },
        {
            "value": total_fuel_amount,
            "label": "Fuel Credit",
            "datatype": "Currency",
            "indicator": "Blue"
        },
        {
            "value": total_cash_given,
            "label": "Cash Given to Drivers",
            "datatype": "Currency",
            "indicator": "Orange"
        },
        {
            "value": total_qty,
            "label": "Total Fuel (L)",
            "datatype": "Float",
            "indicator": "Green"
        },
        {
            "value": unique_vehicles,
            "label": "Unique Vehicles",
            "datatype": "Int",
            "indicator": "Purple"
        }
    ]
