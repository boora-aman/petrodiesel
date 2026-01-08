# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate

class CreditSale(Document):
    def validate(self):
        self.calculate_totals()
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
            row.amount = flt(row.quantity) * flt(row.rate)
            total_qty += flt(row.quantity)
            total_amount += flt(row.amount)
        
        self.total_quantity = total_qty
        self.total_amount = total_amount
        
        # Calculate outstanding
        self.outstanding_amount = flt(self.total_amount) - flt(self.paid_amount)
    
    def update_outstanding(self):
        """Update outstanding based on payments"""
        if not self.name:
            return
        
        # Get total paid from Customer Payment Entry
        total_paid = frappe.db.sql("""
            SELECT SUM(paid_amount)
            FROM `tabCustomer Payment Entry`
            WHERE credit_sale = %s
            AND docstatus = 1
        """, self.name)
        
        self.paid_amount = flt(total_paid[0][0]) if total_paid and total_paid[0][0] else 0
        self.outstanding_amount = flt(self.total_amount) - flt(self.paid_amount)
        
        # Update payment status
        if self.outstanding_amount <= 0:
            self.payment_status = 'Paid'
        elif self.paid_amount > 0:
            self.payment_status = 'Partial'
        else:
            self.payment_status = 'Unpaid'
    
    def update_customer_balance(self):
        """Update customer outstanding balance"""
        if not self.customer:
            return
        
        outstanding = get_customer_outstanding(self.customer)
        
        # Update in Customer master if field exists
        if frappe.db.exists('Customer', self.customer):
            frappe.db.set_value('Customer', self.customer, 'credit_balance', outstanding, update_modified=False)
    
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
                'item_code': row.item_code,
                'item_name': row.item_name,
                'qty': row.quantity,
                'rate': row.rate,
                'amount': row.amount,
                'uom': row.uom or 'Nos'
            })
        
        si = frappe.get_doc({
            'doctype': 'Sales Invoice',
            'customer': self.customer,
            'posting_date': self.posting_date,
            'company': frappe.defaults.get_user_default('Company'),
            'reference_doctype': 'Credit Sale',
            'reference_name': self.name,
            'items': items
        })
        
        try:
            si.insert(ignore_permissions=True)
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
                    si.cancel()
                self.db_set('sales_invoice', None)
            except Exception as e:
                frappe.log_error(f'Failed to cancel Sales Invoice: {str(e)}')


@frappe.whitelist()
def get_customer_outstanding(customer):
    """Get total outstanding for customer"""
    if not customer:
        return 0
    
    outstanding = frappe.db.sql("""
        SELECT SUM(outstanding_amount)
        FROM `tabCredit Sale`
        WHERE customer = %s
        AND docstatus = 1
    """, customer)
    
    return flt(outstanding[0][0]) if outstanding and outstanding[0][0] else 0


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
            name, posting_date, paid_amount, payment_mode, credit_sale
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
