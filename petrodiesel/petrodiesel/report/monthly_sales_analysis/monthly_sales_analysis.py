# Copyright (c) 2025, AlfaStack and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
import calendar

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    summary = get_summary(data)
    return columns, data, None, chart, summary

def get_columns():
    return [
        {"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 120},
        {"label": _("Year"), "fieldname": "year", "fieldtype": "Data", "width": 80},
        {"label": _("Total Fuel Sales"), "fieldname": "fuel_sales", "fieldtype": "Currency", "width": 140},
        {"label": _("Total Other Sales"), "fieldname": "other_sales", "fieldtype": "Currency", "width": 140},
        {"label": _("Total Credit Fuel"), "fieldname": "credit_fuel", "fieldtype": "Currency", "width": 140},
        {"label": _("Total Online"), "fieldname": "online_payments", "fieldtype": "Currency", "width": 130},
        {"label": _("Cash Received"), "fieldname": "cash_received", "fieldtype": "Currency", "width": 130},
        {"label": _("Total Sales"), "fieldname": "total_sales", "fieldtype": "Currency", "width": 140},
        {"label": _("Total Expenses"), "fieldname": "total_expenses", "fieldtype": "Currency", "width": 130},
        {"label": _("Shift Count"), "fieldname": "shift_count", "fieldtype": "Int", "width": 100},
        {"label": _("Avg Daily Sales"), "fieldname": "avg_daily_sales", "fieldtype": "Currency", "width": 130},
        {"label": _("Growth %"), "fieldname": "growth_percentage", "fieldtype": "Percent", "width": 100}
    ]

def get_data(filters):
    if not filters:
        filters = {}
    
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))
    
    # Build query with direct aggregation
    query = """
        SELECT 
            CONCAT(YEAR(posting_date), '-', LPAD(MONTH(posting_date), 2, '0')) as sort_key,
            MONTHNAME(posting_date) as month,
            YEAR(posting_date) as year,
            SUM(total_fuel_sales) as fuel_sales,
            SUM(total_other_sales) as other_sales,
            SUM(total_credit_fuel) as credit_fuel,
            SUM(total_online) as online_payments,
            SUM(cash_received) as cash_received,
            SUM(total_sales) as total_sales,
            SUM(total_expenses) as total_expenses,
            COUNT(*) as shift_count
        FROM (
            SELECT 
                posting_date,
                total_fuel_sales,
                total_other_sales,
                total_credit_fuel,
                total_online,
                cash_received,
                total_sales,
                total_expenses
            FROM `tabShift Sale Entry`
            WHERE docstatus = 1
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            {shift_filter_sse}
            
            UNION ALL
            
            SELECT 
                posting_date,
                total_fuel_sales,
                total_other_sales,
                total_credit_fuel,
                total_online,
                cash_received,
                total_sales,
                total_expenses
            FROM `tabCashier Wise Shift Sale Entry`
            WHERE docstatus = 1
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            {shift_filter_cwsse}
        ) all_shifts
        GROUP BY YEAR(posting_date), MONTH(posting_date), MONTHNAME(posting_date)
        ORDER BY sort_key DESC
    """
    
    # Add shift filter if needed
    shift_filter_sse = ""
    shift_filter_cwsse = ""
    if filters.get("shift"):
        shift_filter_sse = "AND shift = %(shift)s"
        shift_filter_cwsse = "AND shift = %(shift)s"
    
    query = query.format(shift_filter_sse=shift_filter_sse, shift_filter_cwsse=shift_filter_cwsse)
    
    data = frappe.db.sql(query, filters, as_dict=1)
    
    if not data:
        return []
    
    # Calculate average daily sales and growth percentage
    for i, row in enumerate(data):
        # Get number of days in month
        days_in_month = get_days_in_month(int(row.get("year")), row.get("month"))
        row["avg_daily_sales"] = flt(row.get("total_sales", 0)) / days_in_month if days_in_month > 0 else 0
        
        # Calculate growth compared to previous month
        if i < len(data) - 1:
            prev_sales = flt(data[i + 1].get("total_sales", 0))
            curr_sales = flt(row.get("total_sales", 0))
            if prev_sales > 0:
                row["growth_percentage"] = ((curr_sales - prev_sales) / prev_sales * 100)
            else:
                row["growth_percentage"] = 0
        else:
            row["growth_percentage"] = 0
    
    return data

def get_days_in_month(year, month_name):
    """Get number of days in a given month"""
    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    month_num = month_map.get(month_name, 1)
    return calendar.monthrange(year, month_num)[1]

def get_chart_data(data):
    if not data:
        return None
    
    data_reversed = list(reversed(data))
    labels = [f"{d.get('month', '')} {d.get('year', '')}" for d in data_reversed]
    fuel_values = [flt(d.get("fuel_sales", 0)) for d in data_reversed]
    other_values = [flt(d.get("other_sales", 0)) for d in data_reversed]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Fuel Sales", "values": fuel_values},
                {"name": "Other Sales", "values": other_values}
            ]
        },
        "type": "line",
        "height": 300,
        "colors": ["#4C78FF", "#29CD42"],
        "axisOptions": {"xIsSeries": 1}
    }

def get_summary(data):
    if not data:
        return []
    
    total_fuel = sum(flt(d.get("fuel_sales", 0)) for d in data)
    total_other = sum(flt(d.get("other_sales", 0)) for d in data)
    total_sales = sum(flt(d.get("total_sales", 0)) for d in data)
    total_expenses = sum(flt(d.get("total_expenses", 0)) for d in data)
    total_shifts = sum(flt(d.get("shift_count", 0)) for d in data)
    avg_monthly_sales = total_sales / len(data) if data else 0
    
    return [
        {"value": total_sales, "label": "Total Sales", "datatype": "Currency", "indicator": "Green"},
        {"value": total_fuel, "label": "Total Fuel Sales", "datatype": "Currency", "indicator": "Blue"},
        {"value": total_expenses, "label": "Total Expenses", "datatype": "Currency", "indicator": "Red"},
        {"value": avg_monthly_sales, "label": "Avg Monthly Sales", "datatype": "Currency", "indicator": "Orange"},
        {"value": total_shifts, "label": "Total Shifts", "datatype": "Int", "indicator": "Purple"}
    ]
