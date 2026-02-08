# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def create_customer_custom_fields():
    """Create custom fields for Customer doctype"""
    custom_fields = {
        'Customer': [
            {
                'fieldname': 'credit_balance',
                'label': 'Credit Balance',
                'fieldtype': 'Currency',
                'insert_after': 'credit_limits',
                'read_only': 1,
                'description': 'Total credit sales amount for this customer'
            },
            {
                'fieldname': 'current_outstanding',
                'label': 'Current Outstanding',
                'fieldtype': 'Currency',
                'insert_after': 'credit_balance',
                'read_only': 1,
                'description': 'Current outstanding amount from Credit Sales'
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)

def update_customer_outstanding_balance(doc, method=None):
    """Update customer outstanding and credit balance fields"""
    from petrodiesel.petrodiesel.utils import get_customer_total_outstanding
    
    # Get customer from doc
    customer = doc.customer if hasattr(doc, 'customer') else None
    if not customer:
        return
    
    # Get total outstanding from Credit Sale documents
    outstanding = get_customer_total_outstanding(customer)
    
    # Get total credit sales amount
    total_credit = frappe.db.sql("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM `tabCredit Sale`
        WHERE customer = %s AND docstatus = 1
    """, customer)[0][0] or 0
    
    # Update customer fields
    frappe.db.set_value('Customer', customer, {
        'current_outstanding': outstanding,
        'credit_balance': total_credit
    }, update_modified=False)
