# Copyright (c) 2025, AlfaStack and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    summary = get_summary(data)
    return columns, data, None, chart, summary

def get_columns():
    return [
        {
            "label": _("Payment Method"),
            "fieldname": "payment_method",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Transaction Count"),
            "fieldname": "transaction_count",
            "fieldtype": "Int",
            "width": 130
        },
        {
            "label": _("Total Amount"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "label": _("Avg Transaction"),
            "fieldname": "avg_transaction",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Min Amount"),
            "fieldname": "min_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Max Amount"),
            "fieldname": "max_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("% of Total"),
            "fieldname": "percentage",
            "fieldtype": "Percent",
            "width": 110
        }
    ]

def get_data(filters):
    if not filters:
        filters = {}
    
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))
    
    params = {}
    # Date conditions only (no payment_method filter in subqueries)
    date_conditions_sse = ""
    if filters.get("from_date"):
        date_conditions_sse += " AND sse.posting_date >= %(from_date)s"
        params["from_date"] = filters.get("from_date")
    if filters.get("to_date"):
        date_conditions_sse += " AND sse.posting_date <= %(to_date)s"
        params["to_date"] = filters.get("to_date")
    if filters.get("shift"):
        date_conditions_sse += " AND sse.shift = %(shift)s"
        params["shift"] = filters.get("shift")
    
    date_conditions_cwsse = ""
    if filters.get("from_date"):
        date_conditions_cwsse += " AND cwsse.posting_date >= %(from_date)s"
    if filters.get("to_date"):
        date_conditions_cwsse += " AND cwsse.posting_date <= %(to_date)s"
    if filters.get("shift"):
        date_conditions_cwsse += " AND cwsse.shift = %(shift)s"
    
    # Query 1: Shift Sale Entry → Shift Online Payment
    sse_query = f"""
        SELECT 
            sop.payment_method,
            COUNT(*) as transaction_count,
            SUM(sop.amount) as total_amount,
            AVG(sop.amount) as avg_transaction,
            MIN(sop.amount) as min_amount,
            MAX(sop.amount) as max_amount
        FROM `tabShift Online Payment` sop
        INNER JOIN `tabShift Sale Entry` sse ON sop.parent = sse.name
        WHERE sse.docstatus = 1
        {date_conditions_sse}
        GROUP BY sop.payment_method
    """
    
    # Query 2: Cashier Wise Shift Sale Entry → Online Payment Detail
    cwsse_query = f"""
        SELECT 
            opd.payment_method,
            COUNT(*) as transaction_count,
            SUM(opd.amount) as total_amount,
            AVG(opd.amount) as avg_transaction,
            MIN(opd.amount) as min_amount,
            MAX(opd.amount) as max_amount
        FROM `tabOnline Payment Detail` opd
        INNER JOIN `tabCashier Wise Shift Sale Entry` cwsse ON opd.parent = cwsse.name
        WHERE cwsse.docstatus = 1
        {date_conditions_cwsse}
        GROUP BY opd.payment_method
    """
    
    # Query 3: Customer Payment Entry
    cpe_conditions = ""
    if filters.get("from_date"):
        cpe_conditions += " AND cpe.posting_date >= %(from_date)s"
    if filters.get("to_date"):
        cpe_conditions += " AND cpe.posting_date <= %(to_date)s"
    
    cpe_query = f"""
        SELECT 
            cpe.payment_mode as payment_method,
            COUNT(*) as transaction_count,
            SUM(cpe.paid_amount) as total_amount,
            AVG(cpe.paid_amount) as avg_transaction,
            MIN(cpe.paid_amount) as min_amount,
            MAX(cpe.paid_amount) as max_amount
        FROM `tabCustomer Payment Entry` cpe
        WHERE cpe.docstatus = 1
        {cpe_conditions}
        GROUP BY cpe.payment_mode
    """
    
    # Query 4: Cash from Shift Sale Entry
    sse_cash = f"""
        SELECT 
            'Cash' as payment_method,
            COUNT(*) as transaction_count,
            SUM(sse.cash_received) as total_amount,
            AVG(sse.cash_received) as avg_transaction,
            MIN(sse.cash_received) as min_amount,
            MAX(sse.cash_received) as max_amount
        FROM `tabShift Sale Entry` sse
        WHERE sse.docstatus = 1
        AND sse.cash_received > 0
        {date_conditions_sse}
    """
    
    # Query 5: Cash from Cashier Wise Shift Sale Entry
    cwsse_cash = f"""
        SELECT 
            'Cash' as payment_method,
            COUNT(*) as transaction_count,
            SUM(cwsse.cash_received) as total_amount,
            AVG(cwsse.cash_received) as avg_transaction,
            MIN(cwsse.cash_received) as min_amount,
            MAX(cwsse.cash_received) as max_amount
        FROM `tabCashier Wise Shift Sale Entry` cwsse
        WHERE cwsse.docstatus = 1
        AND cwsse.cash_received > 0
        {date_conditions_cwsse}
    """
    
    # Combine all queries and aggregate
    combined_query = f"""
        SELECT 
            payment_method,
            SUM(transaction_count) as transaction_count,
            SUM(total_amount) as total_amount,
            AVG(avg_transaction) as avg_transaction,
            MIN(min_amount) as min_amount,
            MAX(max_amount) as max_amount
        FROM (
            ({sse_query})
            UNION ALL
            ({cwsse_query})
            UNION ALL
            ({cpe_query})
            UNION ALL
            ({sse_cash})
            UNION ALL
            ({cwsse_cash})
        ) combined
        GROUP BY payment_method
        ORDER BY total_amount DESC
    """
    
    data = frappe.db.sql(combined_query, params, as_dict=1)
    
    if not data:
        return []
    
    # Apply payment_method filter at Python level (after aggregation)
    if filters.get("payment_method"):
        data = [d for d in data if d.get("payment_method") == filters.get("payment_method")]
    
    # Calculate percentage
    total_amount = sum(d.get("total_amount", 0) for d in data)
    for row in data:
        row["percentage"] = (row.get("total_amount", 0) / total_amount * 100) if total_amount > 0 else 0
    
    return data

def get_chart_data(data):
    if not data:
        return None
    
    labels = [d.get("payment_method", "") for d in data]
    values = [d.get("total_amount", 0) for d in data]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Amount",
                    "values": values
                }
            ]
        },
        "type": "pie",
        "height": 300,
        "colors": ["#29CD42", "#4C78FF", "#ffa00a", "#743ee2", "#ff5858", "#2ecc71"]
    }

def get_summary(data):
    if not data:
        return []
    
    total_transactions = sum(d.get("transaction_count", 0) for d in data)
    total_amount = sum(d.get("total_amount", 0) for d in data)
    payment_methods = len(data)
    
    # Find most used method
    most_used = max(data, key=lambda x: x.get("transaction_count", 0)) if data else {}
    
    return [
        {
            "value": total_amount,
            "label": "Total Payment Amount",
            "datatype": "Currency",
            "indicator": "Green"
        },
        {
            "value": total_transactions,
            "label": "Total Transactions",
            "datatype": "Int",
            "indicator": "Blue"
        },
        {
            "value": payment_methods,
            "label": "Payment Methods Used",
            "datatype": "Int",
            "indicator": "Orange"
        },
        {
            "value": most_used.get("payment_method", "N/A"),
            "label": "Most Used Method",
            "datatype": "Data",
            "indicator": "Purple"
        }
    ]
