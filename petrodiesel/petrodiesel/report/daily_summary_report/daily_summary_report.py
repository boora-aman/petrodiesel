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
            "fieldname": "shift_count",
            "label": _("Shifts"),
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "total_fuel_sales",
            "label": _("Fuel Sales (₹)"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "fuel_liters",
            "label": _("Fuel (Liters)"),
            "fieldtype": "Float",
            "width": 120
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
            "fieldname": "payments_received",
            "label": _("Payments Received (₹)"),
            "fieldtype": "Currency",
            "width": 150
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
            "fieldname": "cash_variance",
            "label": _("Cash Variance (₹)"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "net_cash",
            "label": _("Net Cash (₹)"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "credit_outstanding",
            "label": _("Credit Outstanding (₹)"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "tank_variance",
            "label": _("Tank Variance (Liters)"),
            "fieldtype": "Float",
            "width": 140
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
    
    # Get all dates with shifts from both sources
    shift_dates = frappe.db.sql("""
        SELECT DISTINCT posting_date
        FROM `tabShift Sale Entry`
        WHERE docstatus = 1
        {conditions}
    """.format(conditions=conditions), params, as_dict=1)
    
    cashier_dates = frappe.db.sql("""
        SELECT DISTINCT posting_date
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE docstatus = 1
        {conditions}
    """.format(conditions=conditions), params, as_dict=1)
    
    # Combine and get unique dates
    all_dates = set()
    for d in shift_dates:
        all_dates.add(d.posting_date)
    for d in cashier_dates:
        all_dates.add(d.posting_date)
    
    dates = [{"posting_date": d} for d in sorted(all_dates)]
    
    data = []
    
    for date_row in dates:
        date = date_row["posting_date"]
        
        # Get comprehensive daily data for this date
        daily_data = get_comprehensive_daily_data(date)
        
        if daily_data:
            data.append(daily_data)
    
    return data

def get_comprehensive_daily_data(date):
    """Get comprehensive daily data using the same logic as comprehensive daily operations"""
    
    # Get shifts from Shift Sale Entry
    shift_entries = frappe.db.sql("""
        SELECT 
            total_fuel_sales,
            total_other_sales,
            total_sales,
            cash_received,
            total_credit_fuel,
            total_online,
            total_driver_cash,
            total_expenses,
            cash_variance
        FROM `tabShift Sale Entry`
        WHERE posting_date = %(date)s
        AND docstatus = 1
    """, {"date": date}, as_dict=1)
    
    # Get shifts from Cashier Wise Shift Sale Entry
    cashier_entries = frappe.db.sql("""
        SELECT 
            total_fuel_sales,
            total_other_sales,
            total_sales,
            cash_received,
            total_credit_fuel,
            total_online,
            total_driver_cash,
            total_expenses,
            cash_variance
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE posting_date = %(date)s
        AND docstatus = 1
    """, {"date": date}, as_dict=1)
    
    # Combine both lists
    shifts = shift_entries + cashier_entries
    
    # Get fuel liters from nozzle readings (both shift doctypes)
    shift_fuel_liters = frappe.db.sql("""
        SELECT COALESCE(SUM(nr.actual_sale_qty), 0) as liters
        FROM `tabShift Nozzle Reading` nr
        INNER JOIN `tabShift Sale Entry` sse ON nr.parent = sse.name
        WHERE sse.posting_date = %(date)s
        AND sse.docstatus = 1
    """, {"date": date}, as_dict=1)

    cashier_fuel_liters = frappe.db.sql("""
        SELECT COALESCE(SUM(nrd.actual_sale_qty), 0) as liters
        FROM `tabNozzle Reading Detail` nrd
        INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON nrd.parent = cwsse.name
        WHERE cwsse.posting_date = %(date)s
        AND cwsse.docstatus = 1
    """, {"date": date}, as_dict=1)

    fuel_liters = (shift_fuel_liters[0].liters if shift_fuel_liters else 0) + (cashier_fuel_liters[0].liters if cashier_fuel_liters else 0)

    # Payments received on this date
    payments_data = frappe.db.sql("""
        SELECT COALESCE(SUM(paid_amount), 0) as payments_received
        FROM `tabCustomer Payment Entry`
        WHERE posting_date = %(date)s
        AND docstatus = 1
    """, {"date": date}, as_dict=1)
    
    # Get credit outstanding for this date
    credit_data = frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0) as credit_outstanding
        FROM `tabCredit Sale`
        WHERE posting_date = %(date)s AND docstatus = 1
    """, {"date": date}, as_dict=1)
    
    # Get tank variance for this date
    tank_data = frappe.db.sql("""
        SELECT COALESCE(SUM(variance), 0) as tank_variance
        FROM `tabTank Dip Reading`
        WHERE posting_date = %(date)s AND docstatus = 1
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
    cash_variance = 0
    
    for shift in shifts:
        total_fuel_sales += flt(shift.total_fuel_sales)
        other_product_sales += flt(shift.total_other_sales)
        total_sales += flt(shift.total_sales)
        cash_received += flt(shift.cash_received)
        credit_sales += flt(shift.total_credit_fuel)
        digital_payment += flt(shift.total_online)
        driver_cash += flt(shift.total_driver_cash)
        expenses += flt(shift.total_expenses)
        cash_variance += flt(shift.cash_variance)
    
    net_cash = cash_received - expenses
    payments_received = payments_data[0].payments_received if payments_data else 0
    credit_outstanding = credit_data[0].credit_outstanding if credit_data else 0
    tank_variance = tank_data[0].tank_variance if tank_data else 0
    
    return {
        "posting_date": date,
        "shift_count": len(shifts),
        "total_fuel_sales": total_fuel_sales,
        "fuel_liters": fuel_liters,
        "other_product_sales": other_product_sales,
        "total_sales": total_sales,
        "cash_received": cash_received,
        "credit_sales": credit_sales,
        "digital_payment": digital_payment,
        "payments_received": payments_received,
        "driver_cash": driver_cash,
        "expenses": expenses,
        "cash_variance": cash_variance,
        "net_cash": net_cash,
        "credit_outstanding": credit_outstanding,
        "tank_variance": tank_variance
    }

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
                    "values": [flt(d["total_sales"]) for d in data]
                },
                {
                    "name": "Fuel Sales",
                    "values": [flt(d["total_fuel_sales"]) for d in data]
                },
                {
                    "name": "Cash Received",
                    "values": [flt(d["cash_received"]) for d in data]
                },
                {
                    "name": "Credit Sales",
                    "values": [flt(d["credit_sales"]) for d in data]
                }
            ]
        },
        "type": "line",
        "colors": ["#29CD42", "#FF5858", "#FFA00A", "#8B5CF6"]
    }
