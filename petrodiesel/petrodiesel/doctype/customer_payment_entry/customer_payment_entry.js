// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Payment Entry', {
    refresh: function(frm) {
        update_indicators(frm);
    },
    
    paid_amount: function(frm) {
        update_indicators(frm);
    }
});

function update_indicators(frm) {
    frm.page.clear_indicator();
    
    // Customer
    if (frm.doc.customer) {
        frm.page.add_indicator(__(frm.doc.customer), 'blue');
    }
    
    // Paid Amount
    if (frm.doc.paid_amount) {
        frm.page.add_indicator(__('Amount: ₹{0}', [format_currency(frm.doc.paid_amount)]), 'green');
    }
    
    // Payment Mode
    if (frm.doc.payment_mode) {
        frm.page.add_indicator(__(frm.doc.payment_mode), 'blue');
    }
}
