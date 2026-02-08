# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, date_diff, today

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    return columns, data, None, chart

def get_columns():
    return [
        {
            "fieldname": "customer",
            "label": _("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200
        },
        {
            "fieldname": "total_credit_sales",
            "label": _("Total Credit Sales"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "total_paid",
            "label": _("Total Paid"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "outstanding_amount",
            "label": _("Outstanding Amount"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "days_overdue",
            "label": _("Days Overdue"),
            "fieldtype": "Int",
            "width": 100
        }
    ]

def get_data(filters):
    """
    SINGLE SOURCE OF TRUTH: Only query Credit Sale documents.
    Credit Sales are auto-created from Shift entries.
    """
    customers = get_customers_with_credit(filters)
    data = []
    
    for customer in customers:
        if filters.get("customer") and customer != filters.get("customer"):
            continue
        
        params = {"customer": customer}
        date_condition = ""
        
        if filters.get("from_date"):
            date_condition += " AND cs.posting_date >= %(from_date)s"
            params["from_date"] = filters.get("from_date")
        
        if filters.get("to_date"):
            date_condition += " AND cs.posting_date <= %(to_date)s"
            params["to_date"] = filters.get("to_date")
        
        # Fuel type filter
        fuel_condition = ""
        if filters.get("fuel_type"):
            fuel_condition = " AND csi.item_code = %(fuel_type)s"
            params["fuel_type"] = filters.get("fuel_type")
        
        # Get credit sales from Credit Sale documents ONLY
        if filters.get("fuel_type"):
            credit_query = """
                SELECT 
                    COALESCE(SUM(csi.amount), 0) as total_credit,
                    COALESCE(SUM(cs.paid_amount), 0) as total_paid
                FROM `tabCredit Sale` cs
                INNER JOIN `tabCredit Sale Item` csi ON csi.parent = cs.name
                WHERE cs.customer = %(customer)s
                AND cs.docstatus = 1
                {date_condition}
                {fuel_condition}
            """.format(date_condition=date_condition, fuel_condition=fuel_condition)
        else:
            credit_query = """
                SELECT 
                    COALESCE(SUM(total_amount), 0) as total_credit,
                    COALESCE(SUM(paid_amount), 0) as total_paid
                FROM `tabCredit Sale` cs
                WHERE cs.customer = %(customer)s
                AND cs.docstatus = 1
                {date_condition}
            """.format(date_condition=date_condition)
        
        result = frappe.db.sql(credit_query, params, as_dict=1)
        
        if not result:
            continue
        
        total_credit = flt(result[0].get('total_credit', 0))
        total_paid = flt(result[0].get('total_paid', 0))
        outstanding = total_credit - total_paid
        
        # Apply minimum outstanding filter
        if filters.get("min_outstanding"):
            if outstanding < flt(filters.get("min_outstanding")):
                continue
        
        # Only show customers with outstanding
        if outstanding > 0.01:
            # Get days overdue from oldest unpaid Credit Sale
            oldest_date = frappe.db.sql("""
                SELECT MIN(posting_date)
                FROM `tabCredit Sale`
                WHERE customer = %(customer)s 
                AND docstatus = 1 
                AND outstanding_amount > 0
            """, params)
            
            days_overdue = 0
            if oldest_date and oldest_date[0][0]:
                days_overdue = date_diff(today(), oldest_date[0][0])
            
            data.append({
                "customer": customer,
                "total_credit_sales": total_credit,
                "total_paid": total_paid,
                "outstanding_amount": outstanding,
                "days_overdue": days_overdue
            })
    
    # Sort by outstanding amount (highest first)
    data.sort(key=lambda x: x["outstanding_amount"], reverse=True)
    
    return data

def get_customers_with_credit(filters):
    """Get all customers who have credit transactions - ONLY from Credit Sale"""
    
    conditions = ""
    params = {}
    
    if filters.get("from_date"):
        conditions += " AND posting_date >= %(from_date)s"
        params["from_date"] = filters.get("from_date")
    
    if filters.get("to_date"):
        conditions += " AND posting_date <= %(to_date)s"
        params["to_date"] = filters.get("to_date")
    
    if filters.get("customer"):
        conditions += " AND customer = %(customer)s"
        params["customer"] = filters.get("customer")
    
    # Get customers from Credit Sale documents only
    customers = frappe.db.sql("""
        SELECT DISTINCT customer
        FROM `tabCredit Sale`
        WHERE docstatus = 1
        {conditions}
    """.format(conditions=conditions), params, as_list=1)
    
    return [c[0] for c in customers]

def get_chart_data(data):
    """Generate chart for top 10 customers by outstanding"""
    
    if not data:
        return None
    
    # Get top 10
    top_10 = data[:10]
    
    return {
        "data": {
            "labels": [d["customer"] for d in top_10],
            "datasets": [
                {
                    "name": "Outstanding Amount",
                    "values": [d["outstanding_amount"] for d in top_10]
                }
            ]
        },
        "type": "bar",
        "colors": ["#fc4f51"]
    }
