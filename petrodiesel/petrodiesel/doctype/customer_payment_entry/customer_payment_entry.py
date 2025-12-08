# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class CustomerPaymentEntry(Document):
    def validate(self):
        """Validate before saving"""
        self.calculate_outstanding_after_payment()
    
    def calculate_outstanding_after_payment(self):
        """Calculate outstanding after this payment"""
        if self.outstanding_amount and self.amount_received:
            self.outstanding_after_payment = (self.outstanding_amount or 0) - (self.amount_received or 0)
    
    def on_submit(self):
        """Update customer outstanding when submitted"""
        if self.customer and self.amount_received:
            # Get customer's current outstanding from Credit Sales
            current_outstanding = get_customer_outstanding(self.customer)
            
            # Payment reduces outstanding
            # We'll update each unpaid credit sale
            self.allocate_payment_to_credit_sales()
    
    def on_cancel(self):
        """Reverse payment allocation on cancel"""
        if self.customer and self.amount_received:
            self.reverse_payment_allocation()
    
    def allocate_payment_to_credit_sales(self):
        """Allocate payment to oldest credit sales first (FIFO)"""
        remaining_amount = self.amount_received
        
        # Get unpaid credit sales for this customer (oldest first)
        credit_sales = frappe.get_all(
            "Credit Sale",
            filters={
                "customer": self.customer,
                "docstatus": 1,
                "outstanding_amount": [">", 0]
            },
            fields=["name", "outstanding_amount"],
            order_by="posting_date asc"
        )
        
        for sale in credit_sales:
            if remaining_amount <= 0:
                break
            
            # How much to allocate to this credit sale
            allocated = min(remaining_amount, sale.outstanding_amount)
            
            # Update credit sale's outstanding
            new_outstanding = sale.outstanding_amount - allocated
            frappe.db.set_value("Credit Sale", sale.name, "outstanding_amount", new_outstanding)
            
            remaining_amount -= allocated
            
            # Create a link/comment
            frappe.get_doc({
                "doctype": "Comment",
                "comment_type": "Info",
                "reference_doctype": "Credit Sale",
                "reference_name": sale.name,
                "content": f"Payment of ₹{allocated:,.2f} received via {self.name}"
            }).insert(ignore_permissions=True)
        
        frappe.db.commit()
    
    def reverse_payment_allocation(self):
        """Reverse payment allocation (used on cancel)"""
        remaining_amount = self.amount_received
        
        # Get paid credit sales for this customer (newest first for reversal)
        credit_sales = frappe.get_all(
            "Credit Sale",
            filters={
                "customer": self.customer,
                "docstatus": 1
            },
            fields=["name", "outstanding_amount", "total_amount"],
            order_by="posting_date desc"
        )
        
        for sale in credit_sales:
            if remaining_amount <= 0:
                break
            
            # How much can we reverse from this sale
            paid_amount = sale.total_amount - sale.outstanding_amount
            reverse_amount = min(remaining_amount, paid_amount)
            
            if reverse_amount > 0:
                # Update credit sale's outstanding
                new_outstanding = sale.outstanding_amount + reverse_amount
                frappe.db.set_value("Credit Sale", sale.name, "outstanding_amount", new_outstanding)
                
                remaining_amount -= reverse_amount
        
        frappe.db.commit()


# Whitelisted methods

@frappe.whitelist()
def get_customer_outstanding_details(customer):
    """Get customer's total credit sales, paid amount, and outstanding"""
    if not customer:
        return {}
    
    # Total credit sales for this customer
    total_credit = frappe.db.sql("""
        SELECT 
            IFNULL(SUM(total_amount), 0) as total_sales,
            IFNULL(SUM(outstanding_amount), 0) as outstanding
        FROM `tabCredit Sale`
        WHERE customer = %s AND docstatus = 1
    """, customer, as_dict=1)[0]
    
    total_sales = total_credit.get("total_sales", 0)
    outstanding = total_credit.get("outstanding", 0)
    total_paid = total_sales - outstanding
    
    return {
        "total_credit_sales": total_sales,
        "total_paid_before": total_paid,
        "outstanding_amount": outstanding
    }


def get_customer_outstanding(customer):
    """Get customer's total outstanding amount"""
    if not customer:
        return 0
    
    outstanding = frappe.db.sql("""
        SELECT IFNULL(SUM(outstanding_amount), 0) as outstanding
        FROM `tabCredit Sale`
        WHERE customer = %s AND docstatus = 1
    """, customer)[0][0]
    
    return outstanding or 0
