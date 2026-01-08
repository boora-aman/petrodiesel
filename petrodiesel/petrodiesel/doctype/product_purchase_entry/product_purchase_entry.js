// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on('Product Purchase Entry', {
    refresh: function(frm) {
        update_indicators(frm);
        
        if (frm.doc.docstatus === 1) {
            if (frm.doc.stock_entry) {
                frm.add_custom_button(__('View Stock Entry'), function() {
                    frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry);
                }, __('View'));
            }
            
            if (frm.doc.purchase_invoice) {
                frm.add_custom_button(__('View Purchase Invoice'), function() {
                    frappe.set_route('Form', 'Purchase Invoice', frm.doc.purchase_invoice);
                }, __('View'));
            }
        }
    },
    
    posting_date: function(frm) {
        if (!frm.doc.posting_time) {
            frm.set_value('posting_time', frappe.datetime.now_time());
        }
    }
});

frappe.ui.form.on('Product Purchase Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            // Fetch item details
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.product_purchase_entry.product_purchase_entry.get_item_details',
                args: { item_code: row.item_code },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'uom', r.message.uom);
                        if (r.message.last_rate && !row.rate) {
                            frappe.model.set_value(cdt, cdn, 'rate', r.message.last_rate);
                        }
                    }
                }
            });
        }
    },
    
    quantity: function(frm, cdt, cdn) { calculate_item(frm, cdt, cdn); },
    rate: function(frm, cdt, cdn) { calculate_item(frm, cdt, cdn); },
    items_remove: function(frm) { calculate_totals(frm); }
});

function calculate_item(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.amount = flt(row.quantity) * flt(row.rate);
    frm.refresh_field('items');
    calculate_totals(frm);
}

function calculate_totals(frm) {
    let total_qty = 0;
    let total_amount = 0;
    
    $.each(frm.doc.items || [], function(i, row) {
        total_qty += flt(row.quantity);
        total_amount += flt(row.amount);
    });
    
    frm.set_value('total_qty', total_qty);
    frm.set_value('total_amount', total_amount);
    update_indicators(frm);
}

function update_indicators(frm) {
    frm.page.clear_indicator();
    
    if (frm.doc.total_qty) {
        frm.page.add_indicator(__('Qty: {0}', [frm.doc.total_qty.toFixed(2)]), 'blue');
    }
    
    if (frm.doc.total_amount) {
        frm.page.add_indicator(__('Total: ₹{0}', [format_currency(frm.doc.total_amount)]), 'green');
    }
    
    if (frm.doc.docstatus === 1) {
        if (frm.doc.stock_entry) {
            frm.page.add_indicator(__('Stock: {0}', [frm.doc.stock_entry]), 'green');
        }
        if (frm.doc.purchase_invoice) {
            frm.page.add_indicator(__('PI: {0}', [frm.doc.purchase_invoice]), 'green');
        }
    }
}
