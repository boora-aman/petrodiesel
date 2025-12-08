// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Payment Entry', {
    refresh: function(frm) {
        // Show outstanding info prominently
        if (frm.doc.outstanding_amount && frm.doc.outstanding_amount > 0) {
            frm.dashboard.add_indicator(__('Outstanding: {0}', 
                [format_currency(frm.doc.outstanding_amount, frm.doc.currency)]), 
                'orange');
        }
    },
    
    customer: function(frm) {
        if (frm.doc.customer) {
            // Fetch customer's outstanding details
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.customer_payment_entry.customer_payment_entry.get_customer_outstanding_details',
                args: {
                    customer: frm.doc.customer
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('total_credit_sales', r.message.total_credit_sales);
                        frm.set_value('total_paid_before', r.message.total_paid_before);
                        frm.set_value('outstanding_amount', r.message.outstanding_amount);
                        
                        // Calculate after payment
                        calculate_outstanding_after_payment(frm);
                    }
                }
            });
        }
    },
    
    amount_received: function(frm) {
        calculate_outstanding_after_payment(frm);
    }
});

function calculate_outstanding_after_payment(frm) {
    if (frm.doc.outstanding_amount && frm.doc.amount_received) {
        let outstanding_after = (frm.doc.outstanding_amount || 0) - (frm.doc.amount_received || 0);
        frm.set_value('outstanding_after_payment', outstanding_after);
        
        // Warning if overpayment
        if (outstanding_after < 0) {
            frappe.msgprint({
                title: __('Overpayment'),
                message: __('Amount received is more than outstanding. Excess: {0}', 
                    [format_currency(Math.abs(outstanding_after), frm.doc.currency)]),
                indicator: 'orange'
            });
        }
    }
}
