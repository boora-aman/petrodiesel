# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document
from frappe import _

class CreditSale(Document):
    def validate(self):
        """Validate before saving"""
        self.calculate_totals()
        self.validate_credit_limit()
    
    def calculate_totals(self):
        """Calculate totals"""
        total_qty = 0
        total_amount = 0
        
        for row in self.items:
            if row.quantity_liters and row.rate_per_liter:
                row.amount = row.quantity_liters * row.rate_per_liter
            
            total_qty += row.quantity_liters or 0
            total_amount += row.amount or 0
        
        self.total_quantity = total_qty
        self.total_amount = total_amount
    
    def validate_credit_limit(self):
        """Check if customer exceeds credit limit - SIMPLIFIED VERSION"""
        if not self.customer:
            return
        
        # Get credit limit from customer
        customer_doc = frappe.get_doc("Customer", self.customer)
        
        # Try to get credit limit from credit_limits child table
        credit_limit = 0
        if hasattr(customer_doc, 'credit_limits') and customer_doc.credit_limits:
            for cl in customer_doc.credit_limits:
                if cl.credit_limit:
                    credit_limit = cl.credit_limit
                    break
        
        # Store it in the document for reference
        self.credit_limit = credit_limit
        
        # Get outstanding using standard frappe method
        try:
            from erpnext.accounts.utils import get_balance_on
            outstanding = get_balance_on(party_type="Customer", party=self.customer)
        except:
            # If ERPNext method not available, skip validation
            outstanding = 0
        
        # Simple validation - just warn if exceeding limit
        if credit_limit > 0:
            new_outstanding = abs(outstanding) + (self.total_amount or 0)
            
            if new_outstanding > credit_limit:
                frappe.msgprint(
                    _("Warning: Credit limit of ₹{0} will be exceeded. Current outstanding: ₹{1}, New sale: ₹{2}").format(
                        frappe.format_value(credit_limit, {'fieldtype': 'Currency'}),
                        frappe.format_value(abs(outstanding), {'fieldtype': 'Currency'}),
                        frappe.format_value(self.total_amount, {'fieldtype': 'Currency'})
                    ),
                    indicator='orange',
                    alert=True
                )
                # Don't throw error, just warn
    
    def on_submit(self):
        """Actions on submit"""
        # TODO: Create Sales Invoice
        pass
