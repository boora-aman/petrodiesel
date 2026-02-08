// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Bill', {
    refresh: function(frm) {
        update_indicators(frm);
        
        if (frm.doc.docstatus === 0) {
            // Fetch Transactions button
            frm.add_custom_button(__('Fetch Transactions'), function() {
                fetch_transactions(frm);
            }, __('Actions'));
            
            // Get Customer Summary button
            if (frm.doc.customer) {
                frm.add_custom_button(__('Customer Summary'), function() {
                    show_customer_summary(frm);
                }, __('View'));
            }
            
            // Clear Tables button
            if (frm.doc.credit_sales?.length > 0 || frm.doc.payments?.length > 0) {
                frm.add_custom_button(__('Clear Tables'), function() {
                    frappe.confirm(
                        __('Are you sure you want to clear all transactions?'),
                        function() {
                            frm.clear_table('credit_sales');
                            frm.clear_table('payments');
                            frm.refresh_fields();
                            calculate_totals(frm);
                        }
                    );
                }, __('Actions'));
            }
        }
        
        // Add print button for submitted bills
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Print Bill'), function() {
                frappe.ui.form.qz_print(frm.doc.doctype, frm.doc.name);
            }, __('Print'));
        }
    },
    
    customer: function(frm) {
        if (frm.doc.customer) {
            // Get last bill date and show summary
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.customer_bill.customer_bill.get_last_bill_date',
                args: { customer: frm.doc.customer },
                callback: function(r) {
                    if (r.message) {
                        let last_bill = r.message;
                        
                        frappe.msgprint({
                            title: __('Last Bill Information'),
                            message: __('Last Bill: {0}<br>Bill Date: {1}<br>Outstanding: ₹{2}', 
                                [last_bill.name, last_bill.to_date, format_currency(last_bill.outstanding_amount)]),
                            indicator: 'blue'
                        });
                        
                        // Suggest next day as from_date
                        if (!frm.doc.from_date) {
                            let next_date = frappe.datetime.add_days(last_bill.to_date, 1);
                            frm.set_value('from_date', next_date);
                        }
                    } else {
                        frappe.show_alert({
                            message: __('No previous bills found for this customer'),
                            indicator: 'orange'
                        });
                        
                        // Suggest 30 days ago as from_date
                        if (!frm.doc.from_date) {
                            frm.set_value('from_date', frappe.datetime.add_days(frappe.datetime.get_today(), -30));
                        }
                    }
                }
            });
            
            // Show customer outstanding summary
            show_customer_summary(frm);
        }
    },
    
    from_date: function(frm) {
        validate_dates(frm);
    },
    
    to_date: function(frm) {
        validate_dates(frm);
    }
});


// Child table triggers
frappe.ui.form.on('Customer Bill Credit Item', {
    amount: function(frm) {
        calculate_totals(frm);
    },
    credit_sales_remove: function(frm) {
        calculate_totals(frm);
    }
});

frappe.ui.form.on('Customer Bill Payment', {
    paid_amount: function(frm) {
        calculate_totals(frm);
    },
    payments_remove: function(frm) {
        calculate_totals(frm);
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
    
    frappe.show_alert({
        message: __('Fetching transactions...'),
        indicator: 'blue'
    });
    
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
                        row.reference_no = payment.reference_no;
                    });
                    frm.refresh_field('payments');
                }
                
                // Calculate totals
                calculate_totals(frm);
                
                frappe.show_alert({
                    message: __('Transactions loaded successfully!'),
                    indicator: 'green'
                });
            }
        },
        error: function(r) {
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to fetch transactions. Please check console for details.'),
                indicator: 'red'
            });
        }
    });
}


function show_customer_summary(frm) {
    if (!frm.doc.customer) return;
    
    frappe.call({
        method: 'petrodiesel.petrodiesel.doctype.customer_bill.customer_bill.get_customer_outstanding_summary',
        args: { customer: frm.doc.customer },
        callback: function(r) {
            if (r.message) {
                let data = r.message;
                let html = `
                    <div class="row">
                        <div class="col-md-4">
                            <div class="alert alert-info" style="margin: 0;">
                                <h5>Total Outstanding</h5>
                                <h3>₹${format_currency(data.total_outstanding)}</h3>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="alert alert-warning" style="margin: 0;">
                                <h5>Unbilled Transactions</h5>
                                <h3>${data.unbilled_transactions || 0}</h3>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="alert alert-success" style="margin: 0;">
                                <h5>Last Bill Date</h5>
                                <h3>${data.last_bill ? data.last_bill.to_date : 'N/A'}</h3>
                            </div>
                        </div>
                    </div>
                `;
                
                frappe.msgprint({
                    title: __('Customer Summary: {0}', [frm.doc.customer]),
                    message: html,
                    indicator: 'blue',
                    primary_action: {
                        label: __('Create Bill'),
                        action: function() {
                            fetch_transactions(frm);
                        }
                    }
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
        let days = frappe.datetime.get_day_diff(frm.doc.to_date, frm.doc.from_date) + 1;
        frm.page.add_indicator(__('Period: {0} days', [days]), 'gray');
    }
    
    if (frm.doc.total_credit_amount) {
        frm.page.add_indicator(__('Credit: ₹{0}', [format_currency(frm.doc.total_credit_amount)]), 'orange');
    }
    
    if (frm.doc.outstanding_amount !== undefined && frm.doc.outstanding_amount !== null) {
        let color = frm.doc.outstanding_amount > 0 ? 'red' : 'green';
        let label = frm.doc.outstanding_amount > 0 ? 'Outstanding' : 'Overpaid';
        frm.page.add_indicator(__('{0}: ₹{1}', [label, format_currency(Math.abs(frm.doc.outstanding_amount))]), color);
    }
}
