// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on('Credit Sale', {
    refresh: function(frm) {
        update_indicators(frm);
        
        if (frm.doc.docstatus === 1) {
            // Add Payment button
            if (frm.doc.outstanding_amount > 0) {
                frm.add_custom_button(__('Add Payment'), function() {
                    frappe.new_doc('Customer Payment Entry', {
                        customer: frm.doc.customer,
                        credit_sale: frm.doc.name,
                        outstanding_amount: frm.doc.outstanding_amount
                    });
                }, __('Actions'));
            }
            
            // View buttons
            if (frm.doc.sales_invoice) {
                frm.add_custom_button(__('View Sales Invoice'), function() {
                    frappe.set_route('Form', 'Sales Invoice', frm.doc.sales_invoice);
                }, __('View'));
            }
            
            // Customer Ledger
            frm.add_custom_button(__('Customer Ledger'), function() {
                show_customer_ledger(frm);
            }, __('View'));
        }
    },
    
    customer: function(frm) {
        if (frm.doc.customer) {
            // Fetch customer outstanding
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.credit_sale.credit_sale.get_customer_outstanding',
                args: { customer: frm.doc.customer },
                callback: function(r) {
                    if (r.message !== undefined) {
                        let msg = r.message > 0 
                            ? `Customer Outstanding: ₹${format_currency(r.message)}` 
                            : 'No outstanding balance';
                        frappe.show_alert({
                            message: __(msg),
                            indicator: r.message > 0 ? 'orange' : 'green'
                        });
                    }
                }
            });
        }
    }
});

frappe.ui.form.on('Credit Sale Item', {
    nozzle: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.nozzle) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Fuel Nozzle Master',
                    filters: { name: row.nozzle },
                    fieldname: ['fuel_item', 'source_tank', 'current_reading']
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'fuel_item', r.message.fuel_item);
                        frappe.model.set_value(cdt, cdn, 'item_code', r.message.fuel_item);
                        
                        setTimeout(function() {
                            frm.script_manager.trigger('fuel_item', cdt, cdn);
                        }, 300);
                    }
                }
            });
        }
    },
    
    fuel_item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.fuel_item && !row.rate_per_liter) {
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.shift_sale_entry.shift_sale_entry.get_latest_fuel_price',
                args: {
                    fuel_item: row.fuel_item,
                    posting_date: frm.doc.posting_date
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'rate_per_liter', r.message);
                    }
                }
            });
        }
    },
    
    quantity_liters: function(frm, cdt, cdn) { calculate_item(frm, cdt, cdn); },
    rate_per_liter: function(frm, cdt, cdn) { calculate_item(frm, cdt, cdn); },
    amount: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.amount && row.rate_per_liter && !row.quantity_liters) {
            frappe.model.set_value(cdt, cdn, 'quantity_liters', row.amount / row.rate_per_liter);
        }
        calculate_totals(frm);
    },
    items_remove: function(frm) { calculate_totals(frm); }
});

function calculate_item(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.quantity_liters && row.rate_per_liter) {
        row.amount = flt(row.quantity_liters) * flt(row.rate_per_liter);
    }
    frm.refresh_field('items');
    calculate_totals(frm);
}

function calculate_totals(frm) {
    let total_qty = 0;
    let total_amount = 0;
    
    $.each(frm.doc.items || [], function(i, row) {
        total_qty += flt(row.quantity_liters);
        total_amount += flt(row.amount);
    });
    
    frm.set_value('total_quantity', total_qty);
    frm.set_value('total_amount', total_amount);
    frm.set_value('outstanding_amount', total_amount - flt(frm.doc.paid_amount));
    
    update_indicators(frm);
}

function update_indicators(frm) {
    frm.page.clear_indicator();
    
    // Customer
    if (frm.doc.customer) {
        frm.page.add_indicator(__(frm.doc.customer), 'blue');
    }
    
    // Total Amount
    if (frm.doc.total_amount) {
        frm.page.add_indicator(__('Total: ₹{0}', [format_currency(frm.doc.total_amount)]), 'green');
    }
    
    // Outstanding
    if (frm.doc.outstanding_amount !== undefined) {
        let color = frm.doc.outstanding_amount > 0 ? 'red' : 'green';
        frm.page.add_indicator(__('Outstanding: ₹{0}', [format_currency(frm.doc.outstanding_amount)]), color);
    }
    
    // Payment Status
    if (frm.doc.payment_status) {
        let color = frm.doc.payment_status === 'Paid' ? 'green' : 
                   (frm.doc.payment_status === 'Partial' ? 'orange' : 'red');
        frm.page.add_indicator(__(frm.doc.payment_status), color);
    }
}

function show_customer_ledger(frm) {
    frappe.call({
        method: 'petrodiesel.petrodiesel.doctype.credit_sale.credit_sale.get_customer_ledger',
        args: { customer: frm.doc.customer },
        callback: function(r) {
            if (r.message) {
                let html = `<h4>Customer: ${frm.doc.customer}</h4>`;
                html += `<p><b>Total Outstanding: ₹${format_currency(r.message.total_outstanding)}</b></p>`;
                
                html += '<h5>Recent Sales</h5>';
                html += '<table class="table table-bordered table-sm">';
                html += '<tr><th>Date</th><th>Invoice</th><th>Total</th><th>Paid</th><th>Outstanding</th><th>Status</th></tr>';
                
                $.each(r.message.sales, function(i, sale) {
                    html += `<tr>
                        <td>${sale.posting_date}</td>
                        <td><a href="/app/credit-sale/${sale.name}">${sale.name}</a></td>
                        <td>₹${format_currency(sale.total_amount)}</td>
                        <td>₹${format_currency(sale.paid_amount || 0)}</td>
                        <td>₹${format_currency(sale.outstanding_amount)}</td>
                        <td><span class="indicator ${sale.payment_status === 'Paid' ? 'green' : 'red'}">${sale.payment_status}</span></td>
                    </tr>`;
                });
                html += '</table>';
                
                html += '<h5>Recent Payments</h5>';
                html += '<table class="table table-bordered table-sm">';
                html += '<tr><th>Date</th><th>Payment</th><th>Amount</th><th>Mode</th><th>Against</th></tr>';
                
                $.each(r.message.payments, function(i, pay) {
                    html += `<tr>
                        <td>${pay.posting_date}</td>
                        <td><a href="/app/customer-payment-entry/${pay.name}">${pay.name}</a></td>
                        <td>₹${format_currency(pay.paid_amount)}</td>
                        <td>${pay.payment_mode}</td>
                        <td>${pay.credit_sale || '-'}</td>
                    </tr>`;
                });
                html += '</table>';
                
                frappe.msgprint({
                    title: __('Customer Ledger'),
                    message: html,
                    wide: true
                });
            }
        }
    });
}
