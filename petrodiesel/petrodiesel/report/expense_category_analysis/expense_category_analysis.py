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
        {"label": _("Expense Type"), "fieldname": "expense_type", "fieldtype": "Data", "width": 150},
        {"label": _("Transaction Count"), "fieldname": "transaction_count", "fieldtype": "Int", "width": 130},
        {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 140},
        {"label": _("Avg Amount"), "fieldname": "avg_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Min Amount"), "fieldname": "min_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Max Amount"), "fieldname": "max_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("% of Total"), "fieldname": "percentage", "fieldtype": "Percent", "width": 110}
    ]

def get_data(filters):
    if not filters:
        filters = {}
    
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))
    
    # Query expenses from Shift Sale Entry
    query_sse = """
        SELECT 
            sed.expense_type,
            COUNT(*) as transaction_count,
            SUM(sed.amount) as total_amount,
            AVG(sed.amount) as avg_amount,
            MIN(sed.amount) as min_amount,
            MAX(sed.amount) as max_amount
        FROM `tabShift Expense Detail` sed
        INNER JOIN `tabShift Sale Entry` sse ON sed.parent = sse.name
        WHERE sse.docstatus = 1
        AND sse.posting_date BETWEEN %(from_date)s AND %(to_date)s
        {expense_type_filter}
        {shift_filter_sse}
        GROUP BY sed.expense_type
    """
    
    # Query expenses from Cashier Wise Shift Sale Entry
    query_cwsse = """
        SELECT 
            sed.expense_type,
            COUNT(*) as transaction_count,
            SUM(sed.amount) as total_amount,
            AVG(sed.amount) as avg_amount,
            MIN(sed.amount) as min_amount,
            MAX(sed.amount) as max_amount
        FROM `tabShift Expense Detail` sed
        INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON sed.parent = cwsse.name
        WHERE cwsse.docstatus = 1
        AND cwsse.posting_date BETWEEN %(from_date)s AND %(to_date)s
        {expense_type_filter}
        {shift_filter_cwsse}
        GROUP BY sed.expense_type
    """
    
    # Build filters
    expense_type_filter = "AND sed.expense_type = %(expense_type)s" if filters.get("expense_type") else ""
    shift_filter_sse = "AND sse.shift = %(shift)s" if filters.get("shift") else ""
    shift_filter_cwsse = "AND cwsse.shift = %(shift)s" if filters.get("shift") else ""
    
    query_sse = query_sse.format(expense_type_filter=expense_type_filter, shift_filter_sse=shift_filter_sse)
    query_cwsse = query_cwsse.format(expense_type_filter=expense_type_filter, shift_filter_cwsse=shift_filter_cwsse)
    
    # Combine both queries
    combined_query = f"""
        SELECT 
            expense_type,
            SUM(transaction_count) as transaction_count,
            SUM(total_amount) as total_amount,
            AVG(avg_amount) as avg_amount,
            MIN(min_amount) as min_amount,
            MAX(max_amount) as max_amount
        FROM (
            ({query_sse})
            UNION ALL
            ({query_cwsse})
        ) combined
        GROUP BY expense_type
        ORDER BY total_amount DESC
    """
    
    data = frappe.db.sql(combined_query, filters, as_dict=1)
    
    if not data:
        return []
    
    # Calculate percentage of total
    total_expenses = sum(flt(d.get("total_amount", 0)) for d in data)
    
    for row in data:
        amount = flt(row.get("total_amount", 0))
        row["percentage"] = (amount / total_expenses * 100) if total_expenses > 0 else 0
    
    return data

def get_chart_data(data):
    if not data:
        return None
    
    labels = [d.get("expense_type", "") for d in data]
    values = [flt(d.get("total_amount", 0)) for d in data]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Expense Amount", "values": values}
            ]
        },
        "type": "donut",
        "height": 300,
        "colors": ["#ff5858", "#ffa00a", "#4C78FF", "#743ee2", "#29CD42", "#2ecc71"]
    }

def get_summary(data):
    if not data:
        return []
    
    total_amount = sum(flt(d.get("total_amount", 0)) for d in data)
    total_transactions = sum(flt(d.get("transaction_count", 0)) for d in data)
    expense_categories = len(data)
    
    # Find highest expense category
    highest_category = max(data, key=lambda x: flt(x.get("total_amount", 0))) if data else None
    
    # Calculate average expense per transaction
    avg_per_transaction = total_amount / total_transactions if total_transactions > 0 else 0
    
    return [
        {"value": total_amount, "label": "Total Expenses", "datatype": "Currency", "indicator": "Red"},
        {"value": total_transactions, "label": "Total Transactions", "datatype": "Int", "indicator": "Blue"},
        {"value": expense_categories, "label": "Expense Categories", "datatype": "Int", "indicator": "Orange"},
        {"value": avg_per_transaction, "label": "Avg per Transaction", "datatype": "Currency", "indicator": "Purple"},
        {"value": highest_category.get("expense_type", "N/A") if highest_category else "N/A", "label": "Highest Category", "datatype": "Data", "indicator": "Red"}
    ]
