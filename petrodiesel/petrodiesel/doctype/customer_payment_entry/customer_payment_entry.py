# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate

class CustomerPaymentEntry(Document):
    def validate(self):
        if not self.paid_amount or self.paid_amount <= 0:
            frappe.throw("Paid Amount must be greater than 0")
    
    def on_submit(self):
        self.update_customer_balance()
        frappe.msgprint(f'Payment of ₹{self.paid_amount} recorded for {self.customer}', alert=True, indicator='green')
    
    def on_cancel(self):
        self.update_customer_balance()
    
    def update_customer_balance(self):
        """Update customer outstanding balance"""
        outstanding = get_customer_total_outstanding(self.customer)
        
        # Try to update Customer's credit_balance field if it exists
        try:
            if frappe.db.exists('Customer', self.customer):
                if frappe.db.has_column('Customer', 'credit_balance'):
                    frappe.db.set_value('Customer', self.customer, 'credit_balance', outstanding, update_modified=False)
        except Exception as e:
            frappe.log_error(f'Could not update customer credit_balance: {str(e)}')


@frappe.whitelist()
def get_customer_total_outstanding(customer):
    """Get total outstanding for customer across all credit entries"""
    if not customer:
        return 0
    
    # Get total credit sales from Credit Sale doctype
    credit_sales = frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0)
        FROM `tabCredit Sale`
        WHERE customer = %s
        AND docstatus = 1
    """, customer)
    
    credit_sale_outstanding = flt(credit_sales[0][0]) if credit_sales else 0
    
    # Get total credit from Shift Credit Sale (aggregated from shifts)
    shift_credits = frappe.db.sql("""
        SELECT COALESCE(SUM(scs.amount), 0)
        FROM `tabShift Credit Sale` scs
        INNER JOIN `tabShift Sale Entry` sse ON sse.name = scs.parent
        WHERE scs.customer = %s
        AND sse.docstatus = 1
    """, customer)
    
    shift_credit_total = flt(shift_credits[0][0]) if shift_credits else 0
    
    # Get total payments
    total_payments = frappe.db.sql("""
        SELECT COALESCE(SUM(paid_amount), 0)
        FROM `tabCustomer Payment Entry`
        WHERE customer = %s
        AND docstatus = 1
    """, customer)
    
    payments = flt(total_payments[0][0]) if total_payments else 0
    
    # Calculate outstanding: (Credit Sales + Shift Credits) - Payments
    total_outstanding = (credit_sale_outstanding + shift_credit_total) - payments
    
    return total_outstanding


@frappe.whitelist()
def get_customer_credit_summary(customer):
    """Get detailed credit summary for customer"""
    if not customer:
        return {}
    
    # Credit Sale entries
    credit_sales = frappe.db.sql("""
        SELECT 
            name, posting_date, total_amount, 
            COALESCE(outstanding_amount, total_amount) as outstanding_amount,
            COALESCE(payment_status, 'Unpaid') as payment_status
        FROM `tabCredit Sale`
        WHERE customer = %s
        AND docstatus = 1
        ORDER BY posting_date DESC
        LIMIT 50
    """, customer, as_dict=1)
    
    # Shift credit entries - USE CORRECT FIELD NAMES
    shift_credits = frappe.db.sql("""
        SELECT 
            scs.parent as shift_entry,
            sse.posting_date,
            scs.vehicle_number,
            scs.fuel_item,
            scs.quantity_liters as quantity,
            scs.rate_per_liter as rate,
            scs.amount
        FROM `tabShift Credit Sale` scs
        INNER JOIN `tabShift Sale Entry` sse ON sse.name = scs.parent
        WHERE scs.customer = %s
        AND sse.docstatus = 1
        ORDER BY sse.posting_date DESC
        LIMIT 50
    """, customer, as_dict=1)
    
    # Payment entries
    payments = frappe.db.sql("""
        SELECT 
            name, posting_date, paid_amount, payment_mode, 
            COALESCE(reference_no, '-') as reference_no
        FROM `tabCustomer Payment Entry`
        WHERE customer = %s
        AND docstatus = 1
        ORDER BY posting_date DESC
        LIMIT 50
    """, customer, as_dict=1)
    
    return {
        'credit_sales': credit_sales,
        'shift_credits': shift_credits,
        'payments': payments,
        'total_outstanding': get_customer_total_outstanding(customer)
    }
