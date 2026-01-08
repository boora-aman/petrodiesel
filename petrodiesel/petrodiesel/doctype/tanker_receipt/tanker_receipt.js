// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tanker Receipt', {
    refresh: function(frm) {
        update_indicators(frm);
        
        // Add custom buttons after submit
        if (frm.doc.docstatus === 1) {
            if (frm.doc.purchase_invoice) {
                frm.add_custom_button(__('View Purchase Invoice'), function() {
                    frappe.set_route('Form', 'Purchase Invoice', frm.doc.purchase_invoice);
                }, __('View'));
            }
            
            if (frm.doc.stock_entry) {
                frm.add_custom_button(__('View Stock Entry'), function() {
                    frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry);
                }, __('View'));
            }
        }
    },
    
    freight_charges: function(frm) {
        calculate_grand_total(frm);
    }
});


// TANKER RECEIPT ITEM
frappe.ui.form.on('Tanker Receipt Item', {
    tank: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.tank) {
            // Auto-fetch current dip reading (before unloading)
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.tanker_receipt.tanker_receipt.get_tank_dip_reading',
                args: { tank: row.tank },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'dip_before_unloading', r.message);
                        frappe.msgprint(__('Current tank dip: {0} KL', [r.message]));
                    }
                }
            });
        }
    },
    
    fuel_item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.fuel_item) {
            // Auto-fetch fuel rate
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.tanker_receipt.tanker_receipt.get_fuel_rate',
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
    
    dip_before_unloading: function(frm, cdt, cdn) { calculate_item_row(frm, cdt, cdn); },
    dip_after_unloading: function(frm, cdt, cdn) { calculate_item_row(frm, cdt, cdn); },
    invoiced_quantity: function(frm, cdt, cdn) { calculate_item_row(frm, cdt, cdn); },
    rate_per_liter: function(frm, cdt, cdn) { calculate_item_row(frm, cdt, cdn); },
    
    items_remove: function(frm) { calculate_all_totals(frm); }
});


// ========== CALCULATION FUNCTIONS ==========

function calculate_item_row(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    // Calculate received quantity (KL)
    if (row.dip_after_unloading && row.dip_before_unloading) {
        row.calculated_received_qty = row.dip_after_unloading - row.dip_before_unloading;
    } else {
        row.calculated_received_qty = 0;
    }
    
    // Calculate shortage/excess (KL)
    if (row.invoiced_quantity && row.calculated_received_qty) {
        row.shortage_excess = row.calculated_received_qty - row.invoiced_quantity;
        
        // Alert if shortage > 1%
        let shortage_percent = Math.abs(row.shortage_excess / row.invoiced_quantity) * 100;
        if (shortage_percent > 1) {
            let msg = row.shortage_excess > 0 ? 'Excess' : 'Shortage';
            frappe.msgprint({
                title: __(msg + ' Detected'),
                message: __('{0}: {1} KL ({2}%)', [msg, Math.abs(row.shortage_excess).toFixed(3), shortage_percent.toFixed(2)]),
                indicator: row.shortage_excess > 0 ? 'blue' : 'red'
            });
        }
    }
    
    // Calculate amount (KL to Liters × rate)
    if (row.invoiced_quantity && row.rate_per_liter) {
        // Convert KL to Liters for rate calculation
        let qty_in_liters = row.invoiced_quantity * 1000;
        row.amount = qty_in_liters * row.rate_per_liter;
    } else {
        row.amount = 0;
    }
    
    frm.refresh_field('items');
    calculate_all_totals(frm);
}

function calculate_all_totals(frm) {
    let total_invoiced = 0;
    let total_received = 0;
    let total_amount = 0;
    
    $.each(frm.doc.items || [], function(i, row) {
        total_invoiced += row.invoiced_quantity || 0;
        total_received += row.calculated_received_qty || 0;
        total_amount += row.amount || 0;
    });
    
    frm.set_value('total_invoiced_qty', total_invoiced);
    frm.set_value('total_received_qty', total_received);
    frm.set_value('total_amount', total_amount);
    
    calculate_grand_total(frm);
    update_indicators(frm);
}

function calculate_grand_total(frm) {
    let grand_total = (frm.doc.total_amount || 0) + (frm.doc.freight_charges || 0);
    frm.set_value('grand_total', grand_total);
    
    update_indicators(frm);
}

function update_indicators(frm) {
    frm.page.clear_indicator();
    
    // Grand Total
    if (frm.doc.grand_total) {
        frm.page.add_indicator(__('Total: ₹{0}', [format_currency(frm.doc.grand_total)]), 'green');
    }
    
    // Received Quantity
    if (frm.doc.total_received_qty) {
        frm.page.add_indicator(__('Received: {0} KL', [frm.doc.total_received_qty.toFixed(3)]), 'blue');
    }
    
    // Shortage/Excess
    if (frm.doc.total_invoiced_qty && frm.doc.total_received_qty) {
        let variance = frm.doc.total_received_qty - frm.doc.total_invoiced_qty;
        if (Math.abs(variance) > 0.01) {
            let color = variance > 0 ? 'orange' : 'red';
            let label = variance > 0 ? 'Excess' : 'Shortage';
            frm.page.add_indicator(__('{0}: {1} KL', [label, Math.abs(variance).toFixed(3)]), color);
        }
    }
    
    // Purchase Invoice status
    if (frm.doc.docstatus === 1) {
        if (frm.doc.purchase_invoice) {
            frm.page.add_indicator(__('PI: {0}', [frm.doc.purchase_invoice]), 'green');
        }
        if (frm.doc.stock_entry) {
            frm.page.add_indicator(__('Stock: {0}', [frm.doc.stock_entry]), 'green');
        }
    }
}
