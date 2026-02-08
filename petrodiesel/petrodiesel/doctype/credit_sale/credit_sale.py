# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate
from petrodiesel.utils import get_customer_total_outstanding


class CreditSale(Document):
    def validate(self):
        self.calculate_totals()
        if self.docstatus == 0:
            self.update_outstanding()
    
    def on_submit(self):
        self.update_customer_balance()
        if self.invoice_created:
            self.create_sales_invoice()
    
    def on_cancel(self):
        self.reverse_customer_balance()
        self.cancel_sales_invoice()
    
    def calculate_totals(self):
        """Calculate total quantity and amount from items"""
        total_qty = 0
        total_amount = 0
        
        for row in self.items:
            row.amount = flt(row.quantity_liters) * flt(row.rate_per_liter)
            total_qty += flt(row.quantity_liters)
            total_amount += flt(row.amount)
        
        self.total_quantity = total_qty
        self.total_amount = total_amount
        
        # Initial outstanding equals total amount
        if not self.outstanding_amount:
            self.outstanding_amount = flt(self.total_amount)
    
    def update_outstanding(self):
        """
        Update outstanding based on payments.
        Called from:
        1. validate() for draft documents
        2. recalculate_outstanding() after payment submission
        """
        if not self.name:
            return
        
        # Get total paid from Customer Payment Entry
        total_paid = frappe.db.sql("""
            SELECT COALESCE(SUM(paid_amount), 0)
            FROM `tabCustomer Payment Entry`
            WHERE credit_sale = %s
            AND docstatus = 1
        """, self.name)
        
        self.paid_amount = flt(total_paid[0][0]) if total_paid else 0
        self.outstanding_amount = flt(self.total_amount) - flt(self.paid_amount)
        
        # Update payment status
        if self.outstanding_amount <= 0:
            self.payment_status = 'Paid'
        elif self.paid_amount > 0:
            self.payment_status = 'Partial'
        else:
            self.payment_status = 'Unpaid'
    
    def recalculate_outstanding(self):
        """
        Public method to recalculate outstanding after payment.
        Called from Customer Payment Entry on submit/cancel.
        """
        self.update_outstanding()
        self.db_set('paid_amount', self.paid_amount)
        self.db_set('outstanding_amount', self.outstanding_amount)
        self.db_set('payment_status', self.payment_status)
    
    def update_customer_balance(self):
        """Update customer outstanding balance"""
        if not self.customer:
            return
        
        # Calculate total outstanding for this customer
        outstanding = get_customer_total_outstanding(self.customer)
        
        # Update in Customer master if custom field exists
        try:
            if frappe.db.exists('Customer', self.customer):
                frappe.db.set_value('Customer', self.customer, {
                    'custom_credit_balance': outstanding,
                    'custom_last_credit_date': self.posting_date
                }, update_modified=False)
                
                frappe.msgprint(_(f"Customer {self.customer} outstanding balance updated to {outstanding}"), alert=True)
        except Exception as e:
            frappe.log_error(f"Failed to update customer balance: {str(e)}")
    
    def reverse_customer_balance(self):
        """Reverse customer balance on cancel"""
        self.update_customer_balance()
    
    def create_sales_invoice(self):
        """Create Sales Invoice for accounting"""
        if self.sales_invoice:
            return
        
        items = []
        for row in self.items:
            items.append({
                'item_code': row.fuel_item,
                'qty': row.quantity_liters,
                'rate': row.rate_per_liter,
                'amount': row.amount,
                'uom': 'Litre'
            })
        
        si = frappe.get_doc({
            'doctype': 'Sales Invoice',
            'customer': self.customer,
            'posting_date': self.posting_date,
            'company': frappe.defaults.get_user_default('Company'),
            'items': items
        })
        
        try:
            si.flags.ignore_permissions = True
            si.insert()
            si.submit()
            
            self.db_set('sales_invoice', si.name)
            frappe.msgprint(f'Sales Invoice {si.name} created', alert=True)
        except Exception as e:
            frappe.log_error(f'Failed to create Sales Invoice: {str(e)}')
    
    def cancel_sales_invoice(self):
        """Cancel Sales Invoice"""
        if self.sales_invoice:
            try:
                si = frappe.get_doc('Sales Invoice', self.sales_invoice)
                if si.docstatus == 1:
                    si.flags.ignore_permissions = True
                    si.cancel()
                self.db_set('sales_invoice', None)
            except Exception as e:
                frappe.log_error(f'Failed to cancel Sales Invoice: {str(e)}')


@frappe.whitelist()
def get_customer_outstanding(customer):
    """Get total outstanding for customer"""
    return get_customer_total_outstanding(customer)


@frappe.whitelist()
def get_customer_ledger(customer):
    """Get customer credit ledger (sales + payments)"""
    if not customer:
        return {}
    
    sales = frappe.db.sql("""
        SELECT 
            name, posting_date, total_amount, paid_amount, 
            outstanding_amount, payment_status
        FROM `tabCredit Sale`
        WHERE customer = %s
        AND docstatus = 1
        ORDER BY posting_date DESC
        LIMIT 50
    """, customer, as_dict=1)
    
    payments = frappe.db.sql("""
        SELECT 
            name, posting_date, paid_amount, payment_mode
        FROM `tabCustomer Payment Entry`
        WHERE customer = %s
        AND docstatus = 1
        ORDER BY posting_date DESC
        LIMIT 50
    """, customer, as_dict=1)
    
    return {
        'sales': sales,
        'payments': payments,
        'total_outstanding': get_customer_outstanding(customer)
    }
