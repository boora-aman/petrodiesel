# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate

class CustomerBill(Document):
    def validate(self):
        self.validate_dates()
        self.calculate_totals()
    
    def validate_dates(self):
        """Validate date range"""
        if getdate(self.from_date) > getdate(self.to_date):
            frappe.throw("To Date cannot be before From Date")
    
    def calculate_totals(self):
        """Calculate total credit and payments"""
        total_credit = 0
        total_payments = 0
        
        for row in self.credit_sales:
            total_credit += flt(row.amount)
        
        for row in self.payments:
            total_payments += flt(row.paid_amount)
        
        self.total_credit_amount = total_credit
        self.total_payments = total_payments
        self.outstanding_amount = total_credit - total_payments


@frappe.whitelist()
def fetch_customer_transactions(customer, from_date, to_date):
    """Fetch all credit transactions and payments for customer in date range"""
    
    # 1. Get Shift Credit Sales
    shift_credits = frappe.db.sql("""
        SELECT 
            sse.posting_date,
            'Shift Sale Entry' as reference_type,
            sse.name as reference_name,
            scs.vehicle_number,
            scs.fuel_item,
            scs.quantity_liters as quantity,
            scs.rate_per_liter as rate,
            scs.amount
        FROM `tabShift Credit Sale` scs
        INNER JOIN `tabShift Sale Entry` sse ON sse.name = scs.parent
        WHERE scs.customer = %s
        AND sse.posting_date BETWEEN %s AND %s
        AND sse.docstatus = 1
        ORDER BY sse.posting_date, sse.name
    """, (customer, from_date, to_date), as_dict=1)
    
    # 2. Get Direct Credit Sales
    credit_sales = frappe.db.sql("""
        SELECT 
            cs.posting_date,
            'Credit Sale' as reference_type,
            cs.name as reference_name,
            csi.vehicle_number,
            csi.item_code as fuel_item,
            csi.quantity,
            csi.rate,
            csi.amount
        FROM `tabCredit Sale Item` csi
        INNER JOIN `tabCredit Sale` cs ON cs.name = csi.parent
        WHERE cs.customer = %s
        AND cs.posting_date BETWEEN %s AND %s
        AND cs.docstatus = 1
        ORDER BY cs.posting_date, cs.name
    """, (customer, from_date, to_date), as_dict=1)
    
    # Combine all credit sales
    all_credits = shift_credits + credit_sales
    
    # 3. Get Payments
    payments = frappe.db.sql("""
        SELECT 
            posting_date,
            name as payment_entry,
            payment_mode,
            paid_amount
        FROM `tabCustomer Payment Entry`
        WHERE customer = %s
        AND posting_date BETWEEN %s AND %s
        AND docstatus = 1
        ORDER BY posting_date
    """, (customer, from_date, to_date), as_dict=1)
    
    return {
        'credit_sales': all_credits,
        'payments': payments
    }


@frappe.whitelist()
def get_last_bill_date(customer):
    """Get the to_date of last bill for this customer"""
    last_bill = frappe.db.sql("""
        SELECT to_date
        FROM `tabCustomer Bill`
        WHERE customer = %s
        AND docstatus = 1
        ORDER BY to_date DESC
        LIMIT 1
    """, customer)
    
    return last_bill[0][0] if last_bill else None
