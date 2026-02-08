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
        {"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Shift"), "fieldname": "shift", "fieldtype": "Link", "options": "Shift Master", "width": 100},
        {"label": _("Cashier"), "fieldname": "cashier", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": _("Expected Cash"), "fieldname": "expected_cash", "fieldtype": "Currency", "width": 130},
        {"label": _("Cash Received"), "fieldname": "cash_received", "fieldtype": "Currency", "width": 130},
        {"label": _("Cash Variance"), "fieldname": "cash_variance", "fieldtype": "Currency", "width": 120},
        {"label": _("Variance %"), "fieldname": "variance_percentage", "fieldtype": "Percent", "width": 100},
        {"label": _("Total Sales"), "fieldname": "total_sales", "fieldtype": "Currency", "width": 130},
        {"label": _("Cash Sales"), "fieldname": "cash_sales", "fieldtype": "Currency", "width": 120},
        {"label": _("Credit Sales"), "fieldname": "credit_sales", "fieldtype": "Currency", "width": 120},
        {"label": _("Online Sales"), "fieldname": "online_sales", "fieldtype": "Currency", "width": 120},
        {"label": _("Expenses"), "fieldname": "total_expenses", "fieldtype": "Currency", "width": 110},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100}
    ]

def get_data(filters):
    if not filters:
        filters = {}
    
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))
    
    # Query from Cashier Wise Shift Sale Entry
    query_cwsse = """
        SELECT 
            cwsse.posting_date,
            cwsse.shift,
            cwsse.cashier,
            cwsse.expected_cash,
            cwsse.cash_received,
            cwsse.cash_variance,
            cwsse.total_sales,
            (cwsse.total_sales - cwsse.total_credit_fuel - cwsse.total_online) as cash_sales,
            cwsse.total_credit_fuel as credit_sales,
            cwsse.total_online as online_sales,
            cwsse.total_expenses,
            'Cashier Wise' as entry_type
        FROM `tabCashier Wise Shift Sale Entry` cwsse
        WHERE cwsse.docstatus = 1
        AND cwsse.posting_date BETWEEN %(from_date)s AND %(to_date)s
        {shift_filter}
        {cashier_filter}
    """
    
    # Query from Shift Sale Entry (consolidated)
    query_sse = """
        SELECT 
            sse.posting_date,
            sse.shift,
            '' as cashier,
            sse.expected_cash,
            sse.cash_received,
            sse.cash_variance,
            sse.total_sales,
            (sse.total_sales - sse.total_credit_fuel - sse.total_online) as cash_sales,
            sse.total_credit_fuel as credit_sales,
            sse.total_online as online_sales,
            sse.total_expenses,
            'Consolidated' as entry_type
        FROM `tabShift Sale Entry` sse
        WHERE sse.docstatus = 1
        AND sse.posting_date BETWEEN %(from_date)s AND %(to_date)s
        {shift_filter}
    """
    
    # Build filters
    shift_filter = "AND shift = %(shift)s" if filters.get("shift") else ""
    cashier_filter = "AND cashier = %(cashier)s" if filters.get("cashier") else ""
    
    query_cwsse = query_cwsse.format(shift_filter=shift_filter, cashier_filter=cashier_filter)
    query_sse = query_sse.format(shift_filter=shift_filter)
    
    # Combine both queries
    combined_query = f"""
        SELECT * FROM (
            ({query_cwsse})
            UNION ALL
            ({query_sse})
        ) combined
        ORDER BY posting_date DESC, shift, cashier
    """
    
    params = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
    }
    if filters.get("shift"):
        params["shift"] = filters.get("shift")
    if filters.get("cashier"):
        params["cashier"] = filters.get("cashier")

    data = frappe.db.sql(combined_query, params, as_dict=1)
    
    if not data:
        return []
    
    # Calculate variance percentage and status
    for row in data:
        expected = flt(row.get("expected_cash", 0))
        variance = flt(row.get("cash_variance", 0))
        
        if expected > 0:
            row["variance_percentage"] = (variance / expected * 100)
        else:
            row["variance_percentage"] = 0
        
        # Determine status
        abs_variance = abs(variance)
        if abs_variance == 0:
            row["status"] = "Perfect ✓"
        elif abs_variance <= 10:
            row["status"] = "Good"
        elif abs_variance <= 50:
            row["status"] = "Acceptable"
        else:
            row["status"] = "Review Required"
    
    return data


def get_chart_data(data):
    if not data:
        return None
    
    # Show variance trend by date
    date_variance = {}
    for row in data:
        date = str(row.get("posting_date"))
        if date not in date_variance:
            date_variance[date] = 0
        date_variance[date] += flt(row.get("cash_variance", 0))
    
    labels = sorted(date_variance.keys())
    values = [date_variance[date] for date in labels]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [{"name": "Cash Variance", "values": values}]
        },
        "type": "line",
        "height": 300,
        "colors": ["#ff5858"],
        "axisOptions": {"xIsSeries": 1}
    }

def get_summary(data):
    if not data:
        return []
    
    total_expected = sum(flt(d.get("expected_cash", 0)) for d in data)
    total_received = sum(flt(d.get("cash_received", 0)) for d in data)
    total_variance = sum(flt(d.get("cash_variance", 0)) for d in data)
    
    # Count reconciliation status
    perfect = sum(1 for d in data if d.get("status") == "Perfect ✓")
    review_needed = sum(1 for d in data if d.get("status") == "Review Required")
    
    # Overall accuracy
    overall_accuracy = 100 - (abs(total_variance) / total_expected * 100) if total_expected > 0 else 100
    
    return [
        {"value": total_expected, "label": "Total Expected Cash", "datatype": "Currency", "indicator": "Blue"},
        {"value": total_received, "label": "Total Cash Received", "datatype": "Currency", "indicator": "Green"},
        {"value": abs(total_variance), "label": "Total Variance", "datatype": "Currency", "indicator": "Red" if total_variance < 0 else "Orange"},
        {"value": overall_accuracy, "label": "Overall Accuracy", "datatype": "Percent", "indicator": "Green"},
        {"value": perfect, "label": "Perfect Reconciliations", "datatype": "Int", "indicator": "Green"},
        {"value": review_needed, "label": "Need Review", "datatype": "Int", "indicator": "Red"}
    ]
