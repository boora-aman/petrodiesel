// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Payment Entry', {
    refresh: function(frm) {
        update_indicators(frm);
        
        if (frm.doc.docstatus === 0 && frm.doc.customer) {
            frm.add_custom_button(__('View Outstanding'), function() {
                show_customer_outstanding(frm);
            }, __('View'));
            
            frm.add_custom_button(__('View Credit Summary'), function() {
                show_credit_summary(frm);
            }, __('View'));
        }
    },
    
    customer: function(frm) {
        if (frm.doc.customer) {
            fetch_customer_outstanding(frm);
        }
    },
    
    credit_sale: function(frm) {
        if (frm.doc.credit_sale) {
            frappe.db.get_value('Credit Sale', frm.doc.credit_sale, 'outstanding_amount')
                .then(r => {
                    if (r.message && r.message.outstanding_amount) {
                        frm.set_value('outstanding_amount', r.message.outstanding_amount);
                        if (!frm.doc.paid_amount) {
                            frm.set_value('paid_amount', r.message.outstanding_amount);
                        }
                    }
                });
        }
    },
    
    paid_amount: function(frm) {
        update_indicators(frm);
    }
});

function fetch_customer_outstanding(frm) {
    frappe.call({
        method: 'petrodiesel.petrodiesel.doctype.customer_payment_entry.customer_payment_entry.get_customer_outstanding',
        args: { customer: frm.doc.customer },
        callback: function(r) {
            if (r.message !== undefined) {
                frm.set_value('outstanding_amount', r.message);
                frappe.show_alert({
                    message: __('Customer Outstanding: ₹{0}', [format_currency(r.message)]),
                    indicator: r.message > 0 ? 'orange' : 'green'
                });
            }
        }
    });
}

function show_customer_outstanding(frm) {
    frappe.call({
        method: 'petrodiesel.petrodiesel.doctype.customer_payment_entry.customer_payment_entry.get_customer_outstanding',
        args: { customer: frm.doc.customer },
        callback: function(r) {
            if (r.message !== undefined) {
                frappe.msgprint({
                    title: __('Customer Outstanding'),
                    message: __('Total Outstanding Amount: <b>₹{0}</b>', [format_currency(r.message)]),
                    indicator: 'blue'
                });
            }
        }
    });
}

function show_credit_summary(frm) {
    frappe.call({
        method: 'petrodiesel.petrodiesel.doctype.customer_payment_entry.customer_payment_entry.get_customer_credit_summary',
        args: { customer: frm.doc.customer },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let html = '<table class="table table-bordered table-sm">';
                html += '<tr><th>Date</th><th>Credit Sale</th><th>Total</th><th>Paid</th><th>Outstanding</th><th>Status</th><th></th></tr>';
                
                $.each(r.message, function(i, row) {
                    html += `<tr>
                        <td>${row.posting_date}</td>
                        <td><a href="/app/credit-sale/${row.name}">${row.name}</a></td>
                        <td>₹${format_currency(row.total_amount)}</td>
                        <td>₹${format_currency(row.paid_amount || 0)}</td>
                        <td>₹${format_currency(row.outstanding_amount)}</td>
                        <td><span class="indicator ${row.payment_status === 'Paid' ? 'green' : 'red'}">${row.payment_status}</span></td>
                        <td><button class="btn btn-xs btn-primary" onclick="set_credit_sale('${row.name}', ${row.outstanding_amount})">Pay</button></td>
                    </tr>`;
                });
                html += '</table>';
                
                frappe.msgprint({
                    title: __('Credit Sales Summary'),
                    message: html,
                    wide: true
                });
            } else {
                frappe.msgprint(__('No outstanding credit sales found'));
            }
        }
    });
}

window.set_credit_sale = function(credit_sale, outstanding) {
    cur_frm.set_value('credit_sale', credit_sale);
    cur_frm.set_value('paid_amount', outstanding);
    frappe.show_alert({
        message: __('Credit Sale selected'),
        indicator: 'green'
    });
};

function update_indicators(frm) {
    frm.page.clear_indicator();
    
    if (frm.doc.customer) {
        frm.page.add_indicator(__(frm.doc.customer), 'blue');
    }
    
    if (frm.doc.paid_amount) {
        frm.page.add_indicator(__('Amount: ₹{0}', [format_currency(frm.doc.paid_amount)]), 'green');
    }
    
    if (frm.doc.payment_mode) {
        frm.page.add_indicator(__(frm.doc.payment_mode), 'blue');
    }
    
    if (frm.doc.outstanding_amount !== undefined) {
        frm.page.add_indicator(__('Outstanding: ₹{0}', [format_currency(frm.doc.outstanding_amount)]), 'orange');
    }
}
