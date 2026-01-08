# Copyright (c) 2025, AlfaStack and contributors
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
        {"label": _("Cashier"), "fieldname": "cashier", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": _("Cashier Name"), "fieldname": "cashier_name", "fieldtype": "Data", "width": 150},
        {"label": _("Shifts Worked"), "fieldname": "shifts_worked", "fieldtype": "Int", "width": 110},
        {"label": _("Total Sales"), "fieldname": "total_sales", "fieldtype": "Currency", "width": 130},
        {"label": _("Fuel Sales"), "fieldname": "fuel_sales", "fieldtype": "Currency", "width": 130},
        {"label": _("Credit Sales"), "fieldname": "credit_sales", "fieldtype": "Currency", "width": 130},
        {"label": _("Cash Received"), "fieldname": "cash_received", "fieldtype": "Currency", "width": 130},
        {"label": _("Expected Cash"), "fieldname": "expected_cash", "fieldtype": "Currency", "width": 130},
        {"label": _("Cash Variance"), "fieldname": "cash_variance", "fieldtype": "Currency", "width": 120},
        {"label": _("Variance %"), "fieldname": "variance_percentage", "fieldtype": "Percent", "width": 100},
        {"label": _("Accuracy %"), "fieldname": "accuracy_percentage", "fieldtype": "Percent", "width": 100},
        {"label": _("Avg Sales/Shift"), "fieldname": "avg_sales_per_shift", "fieldtype": "Currency", "width": 130}
    ]

def get_data(filters):
    if not filters:
        filters = {}
    
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))
    
    # Query for Cashier Wise Shift Sale Entry
    query = """
        SELECT 
            cashier,
            COUNT(*) as shifts_worked,
            SUM(total_sales) as total_sales,
            SUM(total_fuel_sales) as fuel_sales,
            SUM(total_credit_fuel) as credit_sales,
            SUM(cash_received) as cash_received,
            SUM(expected_cash) as expected_cash,
            SUM(cash_variance) as cash_variance
        FROM `tabCashier Wise Shift Sale Entry`
        WHERE docstatus = 1
        AND posting_date BETWEEN %(from_date)s AND %(to_date)s
        {cashier_filter}
        {shift_filter}
        GROUP BY cashier
        ORDER BY total_sales DESC
    """
    
    # Add filters
    cashier_filter = "AND cashier = %(cashier)s" if filters.get("cashier") else ""
    shift_filter = "AND shift = %(shift)s" if filters.get("shift") else ""
    
    query = query.format(cashier_filter=cashier_filter, shift_filter=shift_filter)
    
    data = frappe.db.sql(query, filters, as_dict=1)
    
    if not data:
        return []
    
    # Calculate derived fields
    for row in data:
        # Get cashier name
        cashier_name = frappe.db.get_value("Employee", row.get("cashier"), "employee_name")
        row["cashier_name"] = cashier_name or row.get("cashier", "")
        
        # Calculate percentages
        expected = flt(row.get("expected_cash", 0))
        variance = flt(row.get("cash_variance", 0))
        
        if expected > 0:
            row["variance_percentage"] = (variance / expected * 100)
            row["accuracy_percentage"] = 100 - abs(variance / expected * 100)
        else:
            row["variance_percentage"] = 0
            row["accuracy_percentage"] = 100
        
        # Average sales per shift
        shifts = flt(row.get("shifts_worked", 0))
        row["avg_sales_per_shift"] = flt(row.get("total_sales", 0)) / shifts if shifts > 0 else 0
    
    return data

def get_chart_data(data):
    if not data:
        return None
    
    # Top 10 cashiers by sales
    top_cashiers = data[:10]
    labels = [d.get("cashier_name", "") or d.get("cashier", "") for d in top_cashiers]
    sales_values = [flt(d.get("total_sales", 0)) for d in top_cashiers]
    accuracy_values = [flt(d.get("accuracy_percentage", 0)) for d in top_cashiers]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Total Sales", "values": sales_values, "chartType": "bar"},
                {"name": "Accuracy %", "values": accuracy_values, "chartType": "line"}
            ]
        },
        "type": "axis-mixed",
        "height": 300,
        "colors": ["#4C78FF", "#29CD42"]
    }

def get_summary(data):
    if not data:
        return []
    
    total_shifts = sum(flt(d.get("shifts_worked", 0)) for d in data)
    total_sales = sum(flt(d.get("total_sales", 0)) for d in data)
    total_variance = sum(flt(d.get("cash_variance", 0)) for d in data)
    avg_accuracy = sum(flt(d.get("accuracy_percentage", 0)) for d in data) / len(data) if data else 0
    
    # Find best performer (highest accuracy with minimum 3 shifts)
    qualified_cashiers = [d for d in data if flt(d.get("shifts_worked", 0)) >= 3]
    best_performer = max(qualified_cashiers, key=lambda x: flt(x.get("accuracy_percentage", 0))) if qualified_cashiers else None
    
    return [
        {"value": total_sales, "label": "Total Sales Handled", "datatype": "Currency", "indicator": "Green"},
        {"value": total_shifts, "label": "Total Shifts", "datatype": "Int", "indicator": "Blue"},
        {"value": abs(total_variance), "label": "Total Cash Variance", "datatype": "Currency", "indicator": "Red" if total_variance < 0 else "Orange"},
        {"value": avg_accuracy, "label": "Avg Accuracy", "datatype": "Percent", "indicator": "Green"},
        {"value": best_performer.get("cashier_name", "N/A") if best_performer else "N/A", "label": "Top Performer", "datatype": "Data", "indicator": "Purple"}
    ]
