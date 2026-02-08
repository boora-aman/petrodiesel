# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate
from frappe import _


class CustomerBill(Document):
    def validate(self):
        self.validate_dates()
        self.validate_no_overlapping_bills()
        self.calculate_totals()
    
    def on_submit(self):
        msg = _(f"✓ Bill {self.name} generated successfully for {self.customer}\n\n"
               f"Period: {self.from_date} to {self.to_date}\n"
               f"Total Credit: ₹{self.total_credit_amount:,.2f}\n"
               f"Total Payments: ₹{self.total_payments:,.2f}\n"
               f"Outstanding: ₹{self.outstanding_amount:,.2f}")
        frappe.msgprint(msg, alert=True, indicator='green', title=_("Bill Generated"))
    
    def validate_dates(self):
        """Validate date range"""
        if not self.from_date or not self.to_date:
            frappe.throw(_("From Date and To Date are mandatory"), title=_("Missing Dates"))
        
        if getdate(self.from_date) > getdate(self.to_date):
            frappe.throw(_(f"To Date ({self.to_date}) cannot be before From Date ({self.from_date})"), 
                        title=_("Invalid Date Range"))
        
        if getdate(self.bill_date) < getdate(self.to_date):
            frappe.msgprint(_(f"Bill Date ({self.bill_date}) is before To Date ({self.to_date}). "
                            "Consider using a later bill date for accuracy."), 
                          alert=True, indicator='orange')
    
    def validate_no_overlapping_bills(self):
        """Prevent creating overlapping bills for same customer"""
        if not self.customer or not self.from_date or not self.to_date:
            return
        
        overlapping = frappe.db.sql("""
            SELECT name, from_date, to_date
            FROM `tabCustomer Bill`
            WHERE customer = %s
            AND docstatus = 1
            AND name != %s
            AND (
                (from_date <= %s AND to_date >= %s)
                OR (from_date <= %s AND to_date >= %s)
                OR (from_date >= %s AND to_date <= %s)
            )
        """, (self.customer, self.name or '', self.from_date, self.from_date, 
              self.to_date, self.to_date, self.from_date, self.to_date), as_dict=1)
        
        if overlapping:
            bill_list = ", ".join([f"{b.name} ({b.from_date} to {b.to_date})" for b in overlapping])
            frappe.throw(_(f"Cannot create bill. Overlapping bill(s) already exist for customer {self.customer}:\n{bill_list}\n\n"
                          "Please adjust the date range or cancel the existing bill."), 
                        title=_("Overlapping Bills"))
    
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
    """
    Fetch all credit transactions and payments for customer in date range.
    
    SINGLE SOURCE OF TRUTH: Only fetch from Credit Sale documents.
    Credit Sales are auto-created from:
    - Shift Sale Entry (on submit)
    - Cashier Wise Shift Sale Entry (on submit)
    - Direct Credit Sale entry
    """
    
    if not customer or not from_date or not to_date:
        frappe.throw(_("Customer, From Date and To Date are required"))
    
    # ========================================================================
    # CREDIT SALES - Fetch ONLY from Credit Sale documents
    # ========================================================================
    
    credit_sales = frappe.db.sql("""
        SELECT 
            cs.posting_date,
            cs.name as credit_sale_name,
            COALESCE(cs.reference_type, 'Credit Sale') as reference_type,
            COALESCE(cs.reference_name, cs.name) as reference_name,
            csi.vehicle_number,
            csi.fuel_item,
            csi.quantity_liters as quantity,
            csi.rate_per_liter as rate,
            csi.amount,
            csi.nozzle,
            csi.slip_number
        FROM `tabCredit Sale Item` csi
        INNER JOIN `tabCredit Sale` cs ON cs.name = csi.parent
        WHERE cs.customer = %s
        AND cs.posting_date BETWEEN %s AND %s
        AND cs.docstatus = 1
        ORDER BY cs.posting_date, cs.name
    """, (customer, from_date, to_date), as_dict=1)
    
    # ========================================================================
    # PAYMENTS RECEIVED
    # ========================================================================
    
    payments = frappe.db.sql("""
        SELECT 
            posting_date,
            name as payment_entry,
            payment_mode,
            paid_amount,
            reference_no
        FROM `tabCustomer Payment Entry`
        WHERE customer = %s
        AND posting_date BETWEEN %s AND %s
        AND docstatus = 1
        ORDER BY posting_date
    """, (customer, from_date, to_date), as_dict=1)
    
    # ========================================================================
    # SUMMARY BY SOURCE
    # ========================================================================
    
    # Count by source type
    source_summary = {}
    for cs in credit_sales:
        source_type = cs.get('reference_type') or 'Credit Sale'
        if source_type not in source_summary:
            source_summary[source_type] = {'count': 0, 'amount': 0}
        source_summary[source_type]['count'] += 1
        source_summary[source_type]['amount'] += flt(cs.get('amount', 0))
    
    # Build summary message
    summary_lines = []
    for source, data in source_summary.items():
        summary_lines.append(f"&nbsp;&nbsp;• {source}: {data['count']} (₹{data['amount']:,.2f})")
    
    total_credit = sum(flt(c.get('amount', 0)) for c in credit_sales)
    total_payments = sum(flt(p.get('paid_amount', 0)) for p in payments)
    outstanding = total_credit - total_payments
    
    # Show summary
    frappe.msgprint(
        _(f"<b>✅ Transactions Fetched Successfully!</b><br><br>"
          f"<b>📋 Credit Sales:</b> {len(credit_sales)} transactions<br>"
          f"{'<br>'.join(summary_lines)}<br><br>"
          f"<b>💰 Payments:</b> {len(payments)} transactions<br><br>"
          f"<hr>"
          f"<b>Total Credit:</b> ₹{total_credit:,.2f}<br>"
          f"<b>Total Payments:</b> ₹{total_payments:,.2f}<br>"
          f"<b>Outstanding:</b> <span style='color: {'red' if outstanding > 0 else 'green'}; font-weight: bold;'>₹{outstanding:,.2f}</span>"),
        title=_("Transaction Summary"),
        indicator='orange' if outstanding > 0 else 'green'
    )
    
    return {
        'credit_sales': credit_sales,
        'payments': payments
    }


@frappe.whitelist()
def get_last_bill_date(customer):
    """Get the to_date of last bill for this customer"""
    if not customer:
        return None
    
    last_bill = frappe.db.sql("""
        SELECT to_date, name, outstanding_amount, bill_date
        FROM `tabCustomer Bill`
        WHERE customer = %s
        AND docstatus = 1
        ORDER BY to_date DESC
        LIMIT 1
    """, customer, as_dict=1)
    
    return last_bill[0] if last_bill else None


@frappe.whitelist()
def get_customer_outstanding_summary(customer):
    """Get detailed outstanding summary for customer"""
    if not customer:
        return {}
    
    # Get total outstanding from all sources
    from petrodiesel.utils import get_customer_total_outstanding
    
    total_outstanding = get_customer_total_outstanding(customer)
    
    # Get last bill details
    last_bill = get_last_bill_date(customer)
    
    # Get unbilled Credit Sale count
    unbilled_from = last_bill.get('to_date') if last_bill else None
    
    if unbilled_from:
        unbilled_credits = frappe.db.count('Credit Sale', {
            'customer': customer,
            'docstatus': 1,
            'posting_date': ['>', unbilled_from]
        })
        
        # Get unbilled amount
        unbilled_amount = frappe.db.sql("""
            SELECT COALESCE(SUM(total_amount), 0) as amount
            FROM `tabCredit Sale`
            WHERE customer = %s
            AND docstatus = 1
            AND posting_date > %s
        """, (customer, unbilled_from))[0][0]
    else:
        unbilled_credits = frappe.db.count('Credit Sale', {
            'customer': customer,
            'docstatus': 1
        })
        unbilled_amount = total_outstanding
    
    return {
        'total_outstanding': total_outstanding,
        'last_bill': last_bill,
        'unbilled_transactions': unbilled_credits,
        'unbilled_amount': unbilled_amount
    }
