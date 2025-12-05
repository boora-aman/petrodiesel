# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, date_diff, today

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
            "width": 130
        },
        {
            "fieldname": "outstanding_amount",
            "label": _("Outstanding Amount"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "last_sale_date",
            "label": _("Last Sale Date"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "last_payment_date",
            "label": _("Last Payment Date"),
            "fieldtype": "Date",
            "width": 130
        },
        {
            "fieldname": "days_outstanding",
            "label": _("Days Outstanding"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "fuel_type",
            "label": _("Primary Fuel"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "contact_number",
            "label": _("Contact"),
            "fieldtype": "Data",
            "width": 120
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    # Get credit sales data with outstanding
    data = frappe.db.sql(f"""
        SELECT 
            cs.customer,
            SUM(cs.total_amount) as total_credit_sales,
            0 as total_paid,
            SUM(cs.total_amount) as outstanding_amount,
            MAX(cs.posting_date) as last_sale_date,
            NULL as last_payment_date,
            DATEDIFF(CURDATE(), MAX(cs.posting_date)) as days_outstanding,
            (
                SELECT csi.fuel_item 
                FROM `tabCredit Sale Item` csi 
                WHERE csi.parent = cs.name 
                GROUP BY csi.fuel_item 
                ORDER BY SUM(csi.quantity_liters) DESC 
                LIMIT 1
            ) as fuel_type,
            c.mobile_no as contact_number
        FROM 
            `tabCredit Sale` cs
        LEFT JOIN 
            `tabCustomer` c ON c.name = cs.customer
        WHERE 
            cs.docstatus = 1
            {conditions}
        GROUP BY 
            cs.customer
        HAVING 
            outstanding_amount > 0
        ORDER BY 
            outstanding_amount DESC
    """, filters, as_dict=1)
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("customer"):
        conditions += " AND cs.customer = %(customer)s"
    
    if filters.get("from_date"):
        conditions += " AND cs.posting_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND cs.posting_date <= %(to_date)s"
    
    if filters.get("fuel_type"):
        conditions += """ AND EXISTS (
            SELECT 1 FROM `tabCredit Sale Item` csi 
            WHERE csi.parent = cs.name 
            AND csi.fuel_item = %(fuel_type)s
        )"""
    
    if filters.get("min_outstanding"):
        conditions += " AND cs.total_amount >= %(min_outstanding)s"
    
    return conditions

def get_chart_data(data):
    if not data or len(data) == 0:
        return None
    
    # Top 10 customers by outstanding
    top_10 = data[:10]
    
    return {
        "data": {
            "labels": [d.customer for d in top_10],
            "datasets": [
                {
                    "name": "Outstanding Amount",
                    "values": [d.outstanding_amount for d in top_10]
                }
            ]
        },
        "type": "bar",
        "colors": ["#FF5858"],
        "height": 300,
        "axisOptions": {
            "xIsSeries": 1
        }
    }
