# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

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
            "fieldname": "total_fuel_sales",
            "label": _("Fuel Sales (₹)"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "other_product_sales",
            "label": _("Other Products (₹)"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "total_sales",
            "label": _("Total Sales (₹)"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "cash_received",
            "label": _("Cash Received (₹)"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "credit_sales",
            "label": _("Credit (₹)"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "digital_payment",
            "label": _("Online/Digital (₹)"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "driver_cash",
            "label": _("Driver Cash (₹)"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "expenses",
            "label": _("Expenses (₹)"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "net_cash",
            "label": _("Net Cash (₹)"),
            "fieldtype": "Currency",
            "width": 150
        }
    ]

def get_data(filters):
    conditions = ""
    params = {}
    
    if filters.get("from_date"):
        conditions += " AND posting_date >= %(from_date)s"
        params["from_date"] = filters.get("from_date")
    
    if filters.get("to_date"):
        conditions += " AND posting_date <= %(to_date)s"
        params["to_date"] = filters.get("to_date")
    
    # Get all dates with shifts
    dates = frappe.db.sql("""
        SELECT DISTINCT posting_date
        FROM `tabShift Sale Entry`
        WHERE docstatus = 1
        {conditions}
        ORDER BY posting_date
    """.format(conditions=conditions), params, as_dict=1)
    
    data = []
    
    for date_row in dates:
        date = date_row.posting_date
        
        # Get all shifts for this date
        shifts = frappe.db.sql("""
            SELECT 
                name,
                total_fuel_sales,
                total_other_sales,
                total_sales,
                cash_received,
                total_credit_fuel,
                total_online,
                total_driver_cash,
                total_expenses
            FROM `tabShift Sale Entry`
            WHERE posting_date = %(date)s
            AND docstatus = 1
        """, {"date": date}, as_dict=1)
        
        # Aggregate all shifts for this date
        total_fuel_sales = 0
        other_product_sales = 0
        total_sales = 0
        cash_received = 0
        credit_sales = 0
        digital_payment = 0
        driver_cash = 0
        expenses = 0
        
        for shift in shifts:
            total_fuel_sales += flt(shift.total_fuel_sales)
            other_product_sales += flt(shift.total_other_sales)
            total_sales += flt(shift.total_sales)
            cash_received += flt(shift.cash_received)
            credit_sales += flt(shift.total_credit_fuel)
            digital_payment += flt(shift.total_online)
            driver_cash += flt(shift.total_driver_cash)
            expenses += flt(shift.total_expenses)
        
        net_cash = cash_received - expenses
        
        data.append({
            "posting_date": date,
            "total_fuel_sales": total_fuel_sales,
            "other_product_sales": other_product_sales,
            "total_sales": total_sales,
            "cash_received": cash_received,
            "credit_sales": credit_sales,
            "digital_payment": digital_payment,
            "driver_cash": driver_cash,
            "expenses": expenses,
            "net_cash": net_cash
        })
    
    return data

def get_chart_data(data):
    """Generate chart showing sales trend"""
    
    if not data:
        return None
    
    return {
        "data": {
            "labels": [d["posting_date"].strftime("%d-%b") if hasattr(d["posting_date"], "strftime") else str(d["posting_date"]) for d in data],
            "datasets": [
                {
                    "name": "Total Sales",
                    "values": [d["total_sales"] for d in data]
                },
                {
                    "name": "Cash Received",
                    "values": [d["cash_received"] for d in data]
                },
                {
                    "name": "Credit Sales",
                    "values": [d["credit_sales"] for d in data]
                }
            ]
        },
        "type": "line",
        "colors": ["#7cd6fd", "#5e64ff", "#fc4f51"]
    }
