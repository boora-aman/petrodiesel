# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate
from frappe import _
from petrodiesel.utils import get_customer_total_outstanding as resolve_customer_total_outstanding


class CustomerPaymentEntry(Document):
    def validate(self):
        if not self.paid_amount or flt(self.paid_amount) <= 0:
            frappe.throw(_("Paid Amount must be greater than 0"))
        
        # Validate against outstanding
        outstanding = resolve_customer_total_outstanding(self.customer)
        
        # If paying against specific credit sale, validate against that
        if self.credit_sale:
            cs_outstanding = frappe.db.get_value("Credit Sale", self.credit_sale, "outstanding_amount")
            if flt(self.paid_amount) > flt(cs_outstanding):
                frappe.throw(_(f"Payment amount ₹{self.paid_amount} exceeds Credit Sale outstanding ₹{cs_outstanding}"))
        else:
            # General payment - validate against total outstanding
            if flt(self.paid_amount) > outstanding:
                frappe.throw(_(f"Payment amount ₹{self.paid_amount} exceeds total outstanding ₹{outstanding}"))
        
        # Fetch and display current outstanding
        self.outstanding_amount = outstanding
    
    def on_submit(self):
        self.update_credit_sale_outstanding()
        self.update_customer_balance()
        frappe.msgprint(f'Payment of ₹{self.paid_amount} recorded for {self.customer}', 
                       alert=True, indicator='green')
    
    def on_cancel(self):
        self.update_credit_sale_outstanding()
        self.update_customer_balance()
    
    def update_credit_sale_outstanding(self):
        """Update linked credit sale outstanding"""
        if self.credit_sale:
            try:
                cs_doc = frappe.get_doc("Credit Sale", self.credit_sale)
                cs_doc.recalculate_outstanding()
                frappe.msgprint(_(f"Credit Sale {self.credit_sale} outstanding updated"), alert=True)
            except Exception as e:
                frappe.log_error(f"Failed to update Credit Sale: {str(e)}")
    
    def update_customer_balance(self):
        """Update customer outstanding balance"""
        outstanding = resolve_customer_total_outstanding(self.customer)
        
        # Update Customer custom fields
        try:
            if frappe.db.exists('Customer', self.customer):
                frappe.db.set_value('Customer', self.customer, {
                    'custom_credit_balance': outstanding,
                    'custom_last_payment_date': self.posting_date
                }, update_modified=False)
        except Exception as e:
            frappe.log_error(f'Could not update customer credit_balance: {str(e)}')


@frappe.whitelist()
def get_customer_outstanding(customer):
    """Get customer outstanding - alias for compatibility"""
    if not customer:
        return 0.0
    return resolve_customer_total_outstanding(customer)


@frappe.whitelist()
def get_customer_total_outstanding(customer):
    """Get total outstanding for customer across all credit entries"""
    return resolve_customer_total_outstanding(customer)


@frappe.whitelist()
def get_customer_credit_summary(customer):
    """
    Get detailed credit summary for customer.
    
    SINGLE SOURCE OF TRUTH: Only fetch Credit Sale documents.
    These are auto-created from Shift entries, so no need to query shift tables.
    """
    if not customer:
        return {}
    
    # Credit Sale entries (includes all sources)
    credit_sales = frappe.db.sql("""
        SELECT 
            cs.name, 
            cs.posting_date, 
            cs.total_amount, 
            cs.paid_amount,
            cs.outstanding_amount,
            cs.payment_status,
            cs.reference_type,
            cs.reference_name,
            cs.vehicle_number
        FROM `tabCredit Sale` cs
        WHERE cs.customer = %s
        AND cs.docstatus = 1
        ORDER BY cs.posting_date DESC, cs.creation DESC
        LIMIT 100
    """, customer, as_dict=1)
    
    # Payment entries
    payments = frappe.db.sql("""
        SELECT 
            name, 
            posting_date, 
            paid_amount, 
            payment_mode, 
            credit_sale,
            COALESCE(reference_no, '-') as reference_no
        FROM `tabCustomer Payment Entry`
        WHERE customer = %s
        AND docstatus = 1
        ORDER BY posting_date DESC
        LIMIT 100
    """, customer, as_dict=1)
    
    return {
        'credit_sales': credit_sales,
        'payments': payments,
        'total_outstanding': resolve_customer_total_outstanding(customer)
    }
