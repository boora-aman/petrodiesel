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
            "fieldname": "total_shift_credits",
            "label": _("Shift Credit Sales"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "total_direct_credits",
            "label": _("Direct Credit Sales"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "total_credit_sales",
            "label": _("Total Credit"),
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
            "label": _("Outstanding"),
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
    customers = get_customers_with_credit(filters)
    data = []
    
    for customer in customers:
        # Skip if specific customer filter doesn't match
        if filters.get("customer") and customer != filters.get("customer"):
            continue
        
        # Build conditions and params
        params = {"customer": customer}
        
        # Date conditions
        date_condition_shift = ""
        date_condition_credit = ""
        date_condition_payment = ""
        
        if filters.get("from_date"):
            date_condition_shift += " AND sse.posting_date >= %(from_date)s"
            date_condition_credit += " AND posting_date >= %(from_date)s"
            date_condition_payment += " AND posting_date >= %(from_date)s"
            params["from_date"] = filters.get("from_date")
        
        if filters.get("to_date"):
            date_condition_shift += " AND sse.posting_date <= %(to_date)s"
            date_condition_credit += " AND posting_date <= %(to_date)s"
            date_condition_payment += " AND posting_date <= %(to_date)s"
            params["to_date"] = filters.get("to_date")
        
        # Fuel type condition
        fuel_condition_shift = ""
        fuel_condition_credit = ""
        
        if filters.get("fuel_type"):
            fuel_condition_shift = " AND scs.fuel_item = %(fuel_type)s"
            fuel_condition_credit = " AND csi.item_code = %(fuel_type)s"
            params["fuel_type"] = filters.get("fuel_type")
        
        # Get shift credit sales
        shift_credits = frappe.db.sql("""
            SELECT COALESCE(SUM(scs.amount), 0) as total
            FROM `tabShift Credit Sale` scs
            INNER JOIN `tabShift Sale Entry` sse ON sse.name = scs.parent
            WHERE scs.customer = %(customer)s
            AND sse.docstatus = 1
            {date_condition}
            {fuel_condition}
        """.format(
            date_condition=date_condition_shift,
            fuel_condition=fuel_condition_shift
        ), params)
        
        shift_credit_total = flt(shift_credits[0][0]) if shift_credits else 0
        
        # Get direct credit sales
        if filters.get("fuel_type"):
            # Need to join with items if filtering by fuel
            direct_credits = frappe.db.sql("""
                SELECT COALESCE(SUM(csi.amount), 0) as total
                FROM `tabCredit Sale Item` csi
                INNER JOIN `tabCredit Sale` cs ON cs.name = csi.parent
                WHERE cs.customer = %(customer)s
                AND cs.docstatus = 1
                {date_condition}
                {fuel_condition}
            """.format(
                date_condition=date_condition_credit,
                fuel_condition=fuel_condition_credit
            ), params)
        else:
            direct_credits = frappe.db.sql("""
                SELECT COALESCE(SUM(outstanding_amount), 0) as total
                FROM `tabCredit Sale`
                WHERE customer = %(customer)s
                AND docstatus = 1
                {date_condition}
            """.format(date_condition=date_condition_credit), params)
        
        direct_credit_total = flt(direct_credits[0][0]) if direct_credits else 0
        
        # Get total payments
        payments = frappe.db.sql("""
            SELECT COALESCE(SUM(paid_amount), 0) as total
            FROM `tabCustomer Payment Entry`
            WHERE customer = %(customer)s
            AND docstatus = 1
            {date_condition}
        """.format(date_condition=date_condition_payment), params)
        
        total_paid = flt(payments[0][0]) if payments else 0
        
        # Calculate outstanding
        total_credit = shift_credit_total + direct_credit_total
        outstanding = total_credit - total_paid
        
        # Apply minimum outstanding filter
        if filters.get("min_outstanding"):
            if outstanding < flt(filters.get("min_outstanding")):
                continue
        
        # Only show customers with outstanding
        if outstanding > 0.01:
            # Get days overdue (from oldest unpaid transaction)
            oldest_date = frappe.db.sql("""
                SELECT MIN(posting_date)
                FROM (
                    SELECT sse.posting_date
                    FROM `tabShift Credit Sale` scs
                    INNER JOIN `tabShift Sale Entry` sse ON sse.name = scs.parent
                    WHERE scs.customer = %(customer)s AND sse.docstatus = 1
                    UNION ALL
                    SELECT posting_date
                    FROM `tabCredit Sale`
                    WHERE customer = %(customer)s AND docstatus = 1 AND outstanding_amount > 0
                ) as combined
            """, params)
            
            days_overdue = 0
            if oldest_date and oldest_date[0][0]:
                days_overdue = date_diff(today(), oldest_date[0][0])
            
            data.append({
                "customer": customer,
                "total_shift_credits": shift_credit_total,
                "total_direct_credits": direct_credit_total,
                "total_credit_sales": total_credit,
                "total_paid": total_paid,
                "outstanding_amount": outstanding,
                "days_overdue": days_overdue
            })
    
    # Sort by outstanding amount (highest first)
    data.sort(key=lambda x: x["outstanding_amount"], reverse=True)
    
    return data

def get_customers_with_credit(filters):
    """Get all customers who have credit transactions"""
    
    conditions_shift = ""
    conditions_credit = ""
    params = {}
    
    # Add date filters
    if filters.get("from_date"):
        conditions_shift += " AND sse.posting_date >= %(from_date)s"
        conditions_credit += " AND posting_date >= %(from_date)s"
        params["from_date"] = filters.get("from_date")
    
    if filters.get("to_date"):
        conditions_shift += " AND sse.posting_date <= %(to_date)s"
        conditions_credit += " AND posting_date <= %(to_date)s"
        params["to_date"] = filters.get("to_date")
    
    # Add customer filter
    if filters.get("customer"):
        conditions_shift += " AND scs.customer = %(customer)s"
        conditions_credit += " AND customer = %(customer)s"
        params["customer"] = filters.get("customer")
    
    # Customers from Shift Credit Sales
    shift_customers = frappe.db.sql("""
        SELECT DISTINCT scs.customer
        FROM `tabShift Credit Sale` scs
        INNER JOIN `tabShift Sale Entry` sse ON sse.name = scs.parent
        WHERE sse.docstatus = 1
        {conditions}
    """.format(conditions=conditions_shift), params, as_list=1)
    
    # Customers from Credit Sale
    direct_customers = frappe.db.sql("""
        SELECT DISTINCT customer
        FROM `tabCredit Sale`
        WHERE docstatus = 1
        {conditions}
    """.format(conditions=conditions_credit), params, as_list=1)
    
    # Combine and deduplicate
    all_customers = set([c[0] for c in shift_customers] + [c[0] for c in direct_customers])
    
    return list(all_customers)

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
