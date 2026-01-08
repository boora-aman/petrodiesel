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
        {"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Time"), "fieldname": "posting_time", "fieldtype": "Time", "width": 90},
        {"label": _("Payment Entry"), "fieldname": "payment_entry", "fieldtype": "Link", "options": "Customer Payment Entry", "width": 150},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
        {"label": _("Payment Mode"), "fieldname": "payment_mode", "fieldtype": "Data", "width": 120},
        {"label": _("Paid Amount"), "fieldname": "paid_amount", "fieldtype": "Currency", "width": 130},
        {"label": _("Outstanding Amount"), "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 140},
        {"label": _("Reference No"), "fieldname": "reference_no", "fieldtype": "Data", "width": 150},
        {"label": _("Reference Date"), "fieldname": "reference_date", "fieldtype": "Date", "width": 120},
        {"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Small Text", "width": 200}
    ]

def get_data(filters):
    if not filters:
        filters = {}
    
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))
    
    # Build query for Customer Payment Entry
    query = """
        SELECT 
            cpe.posting_date,
            cpe.posting_time,
            cpe.name as payment_entry,
            cpe.customer,
            cpe.customer_name,
            cpe.payment_mode,
            cpe.paid_amount,
            cpe.outstanding_amount,
            cpe.reference_no,
            cpe.reference_date,
            cpe.remarks
        FROM `tabCustomer Payment Entry` cpe
        WHERE cpe.docstatus = 1
        AND cpe.posting_date BETWEEN %(from_date)s AND %(to_date)s
        {customer_filter}
        {payment_mode_filter}
        ORDER BY cpe.posting_date DESC, cpe.posting_time DESC
    """
    
    # Build filters
    customer_filter = "AND cpe.customer = %(customer)s" if filters.get("customer") else ""
    payment_mode_filter = "AND cpe.payment_mode = %(payment_mode)s" if filters.get("payment_mode") else ""
    
    query = query.format(
        customer_filter=customer_filter,
        payment_mode_filter=payment_mode_filter
    )
    
    data = frappe.db.sql(query, filters, as_dict=1)
    
    return data

def get_chart_data(data, filters):
    if not data:
        return None
    
    # If specific customer, show payment trend over time
    if filters.get("customer"):
        # Group by date
        date_payments = {}
        for row in data:
            date = str(row.get("posting_date"))
            if date not in date_payments:
                date_payments[date] = 0
            date_payments[date] += flt(row.get("paid_amount", 0))
        
        labels = sorted(date_payments.keys())
        values = [date_payments[date] for date in labels]
        
        return {
            "data": {
                "labels": labels,
                "datasets": [{"name": "Payments Received", "values": values}]
            },
            "type": "line",
            "height": 300,
            "colors": ["#29CD42"],
            "axisOptions": {"xIsSeries": 1}
        }
    
    # Otherwise show payment mode breakdown
    mode_totals = {}
    for row in data:
        mode = row.get("payment_mode") or "Cash"
        if mode not in mode_totals:
            mode_totals[mode] = 0
        mode_totals[mode] += flt(row.get("paid_amount", 0))
    
    labels = list(mode_totals.keys())
    values = list(mode_totals.values())
    
    return {
        "data": {
            "labels": labels,
            "datasets": [{"name": "Amount", "values": values}]
        },
        "type": "donut",
        "height": 300,
        "colors": ["#29CD42", "#4C78FF", "#ffa00a", "#743ee2", "#ff5858"]
    }

def get_summary(data):
    if not data:
        return []
    
    total_payments = sum(flt(d.get("paid_amount", 0)) for d in data)
    total_transactions = len(data)
    
    # Average payment
    avg_payment = total_payments / total_transactions if total_transactions > 0 else 0
    
    # Unique customers
    unique_customers = len(set(d.get("customer") for d in data if d.get("customer")))
    
    # Total outstanding (sum from all records)
    total_outstanding = sum(flt(d.get("outstanding_amount", 0)) for d in data)
    
    # Count by payment mode
    mode_counts = {}
    for d in data:
        mode = d.get("payment_mode") or "Cash"
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
    most_used_mode = max(mode_counts, key=mode_counts.get) if mode_counts else "N/A"
    
    return [
        {"value": total_payments, "label": "Total Payments Received", "datatype": "Currency", "indicator": "Green"},
        {"value": total_transactions, "label": "Total Transactions", "datatype": "Int", "indicator": "Blue"},
        {"value": avg_payment, "label": "Avg Payment Amount", "datatype": "Currency", "indicator": "Orange"},
        {"value": unique_customers, "label": "Unique Customers", "datatype": "Int", "indicator": "Purple"},
        {"value": most_used_mode, "label": "Most Used Mode", "datatype": "Data", "indicator": "Blue"}
    ]
