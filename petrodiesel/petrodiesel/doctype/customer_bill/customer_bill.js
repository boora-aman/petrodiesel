// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Bill', {
    refresh: function(frm) {
        update_indicators(frm);
        
        if (frm.doc.docstatus === 0) {
            // Fetch Transactions button
            frm.add_custom_button(__('Fetch Transactions'), function() {
                fetch_transactions(frm);
            });
        }
    },
    
    customer: function(frm) {
        if (frm.doc.customer) {
            // Get last bill date
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.customer_bill.customer_bill.get_last_bill_date',
                args: { customer: frm.doc.customer },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint({
                            title: __('Last Bill'),
                            message: __('Last bill for this customer was till: {0}', [r.message]),
                            indicator: 'blue'
                        });
                        
                        // Suggest next day as from_date
                        let next_date = frappe.datetime.add_days(r.message, 1);
                        if (!frm.doc.from_date) {
                            frm.set_value('from_date', next_date);
                        }
                    } else {
                        frappe.show_alert({
                            message: __('No previous bills found for this customer'),
                            indicator: 'orange'
                        });
                    }
                }
            });
        }
    },
    
    from_date: function(frm) {
        validate_dates(frm);
    },
    
    to_date: function(frm) {
        validate_dates(frm);
    }
});

function fetch_transactions(frm) {
    if (!frm.doc.customer) {
        frappe.msgprint(__('Please select a customer first'));
        return;
    }
    
    if (!frm.doc.from_date || !frm.doc.to_date) {
        frappe.msgprint(__('Please select From Date and To Date'));
        return;
    }
    
    frappe.call({
        method: 'petrodiesel.petrodiesel.doctype.customer_bill.customer_bill.fetch_customer_transactions',
        args: {
            customer: frm.doc.customer,
            from_date: frm.doc.from_date,
            to_date: frm.doc.to_date
        },
        callback: function(r) {
            if (r.message) {
                // Clear existing rows
                frm.clear_table('credit_sales');
                frm.clear_table('payments');
                
                // Add credit sales
                if (r.message.credit_sales && r.message.credit_sales.length > 0) {
                    r.message.credit_sales.forEach(function(credit) {
                        let row = frm.add_child('credit_sales');
                        row.posting_date = credit.posting_date;
                        row.reference_type = credit.reference_type;
                        row.reference_name = credit.reference_name;
                        row.vehicle_number = credit.vehicle_number;
                        row.fuel_item = credit.fuel_item;
                        row.quantity = credit.quantity;
                        row.rate = credit.rate;
                        row.amount = credit.amount;
                    });
                    frm.refresh_field('credit_sales');
                }
                
                // Add payments
                if (r.message.payments && r.message.payments.length > 0) {
                    r.message.payments.forEach(function(payment) {
                        let row = frm.add_child('payments');
                        row.posting_date = payment.posting_date;
                        row.payment_entry = payment.payment_entry;
                        row.payment_mode = payment.payment_mode;
                        row.paid_amount = payment.paid_amount;
                    });
                    frm.refresh_field('payments');
                }
                
                // Calculate totals
                calculate_totals(frm);
                
                frappe.show_alert({
                    message: __('Transactions fetched successfully!'),
                    indicator: 'green'
                });
            }
        }
    });
}

function calculate_totals(frm) {
    let total_credit = 0;
    let total_payments = 0;
    
    $.each(frm.doc.credit_sales || [], function(i, row) {
        total_credit += flt(row.amount);
    });
    
    $.each(frm.doc.payments || [], function(i, row) {
        total_payments += flt(row.paid_amount);
    });
    
    frm.set_value('total_credit_amount', total_credit);
    frm.set_value('total_payments', total_payments);
    frm.set_value('outstanding_amount', total_credit - total_payments);
    
    update_indicators(frm);
}

function validate_dates(frm) {
    if (frm.doc.from_date && frm.doc.to_date) {
        if (frappe.datetime.get_day_diff(frm.doc.to_date, frm.doc.from_date) < 0) {
            frappe.msgprint(__('To Date cannot be before From Date'));
            frm.set_value('to_date', '');
        }
    }
}

function update_indicators(frm) {
    frm.page.clear_indicator();
    
    if (frm.doc.customer) {
        frm.page.add_indicator(__(frm.doc.customer), 'blue');
    }
    
    if (frm.doc.from_date && frm.doc.to_date) {
        frm.page.add_indicator(__('Period: {0} to {1}', [frm.doc.from_date, frm.doc.to_date]), 'gray');
    }
    
    if (frm.doc.total_credit_amount) {
        frm.page.add_indicator(__('Credit: ₹{0}', [format_currency(frm.doc.total_credit_amount)]), 'orange');
    }
    
    if (frm.doc.outstanding_amount !== undefined) {
        let color = frm.doc.outstanding_amount > 0 ? 'red' : 'green';
        frm.page.add_indicator(__('Outstanding: ₹{0}', [format_currency(frm.doc.outstanding_amount)]), color);
    }
}
