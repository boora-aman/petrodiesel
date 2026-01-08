// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on('Internal Stock Transfer', {
    refresh: function(frm) {
        update_indicators(frm);
        
        if (frm.doc.docstatus === 1 && frm.doc.stock_entry) {
            frm.add_custom_button(__('View Stock Entry'), function() {
                frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry);
            });
        }
        
        // Add button to view available items in from warehouse
        if (frm.doc.from_warehouse && frm.doc.docstatus === 0) {
            frm.add_custom_button(__('View Available Items'), function() {
                show_warehouse_stock(frm);
            });
        }
    },
    
    posting_date: function(frm) {
        if (!frm.doc.posting_time) {
            frm.set_value('posting_time', frappe.datetime.now_time());
        }
    },
    
    from_warehouse: function(frm) {
        // Refresh available qty for existing items
        if (frm.doc.items && frm.doc.items.length > 0) {
            $.each(frm.doc.items, function(i, row) {
                if (row.item_code) {
                    fetch_available_qty(frm, row.doctype, row.name);
                }
            });
        }
    },
    
    to_warehouse: function(frm) {
        if (frm.doc.from_warehouse === frm.doc.to_warehouse) {
            frappe.msgprint({
                title: __('Invalid Selection'),
                message: __('From Warehouse and To Warehouse cannot be same'),
                indicator: 'red'
            });
            frm.set_value('to_warehouse', '');
        }
    }
});

frappe.ui.form.on('Internal Stock Transfer Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code && frm.doc.from_warehouse) {
            fetch_available_qty(frm, cdt, cdn);
        }
    },
    
    quantity: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.quantity > row.available_qty) {
            frappe.msgprint({
                title: __('Insufficient Stock'),
                message: __('Transfer quantity {0} exceeds available stock {1}', [row.quantity, row.available_qty]),
                indicator: 'red'
            });
        }
        calculate_totals(frm);
    },
    
    items_remove: function(frm) {
        calculate_totals(frm);
    }
});

function fetch_available_qty(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    frappe.call({
        method: 'petrodiesel.petrodiesel.doctype.internal_stock_transfer.internal_stock_transfer.get_item_stock_in_warehouse',
        args: {
            item_code: row.item_code,
            warehouse: frm.doc.from_warehouse
        },
        callback: function(r) {
            if (r.message !== undefined) {
                frappe.model.set_value(cdt, cdn, 'available_qty', r.message);
                
                if (r.message === 0) {
                    frappe.show_alert({
                        message: __('No stock available for {0} in {1}', [row.item_code, frm.doc.from_warehouse]),
                        indicator: 'orange'
                    });
                }
            }
        }
    });
}

function calculate_totals(frm) {
    let total_qty = 0;
    
    $.each(frm.doc.items || [], function(i, row) {
        total_qty += flt(row.quantity);
    });
    
    frm.set_value('total_qty', total_qty);
    update_indicators(frm);
}

function update_indicators(frm) {
    frm.page.clear_indicator();
    
    if (frm.doc.from_warehouse) {
        frm.page.add_indicator(__('From: {0}', [frm.doc.from_warehouse.split(' - ')[0]]), 'blue');
    }
    
    if (frm.doc.to_warehouse) {
        frm.page.add_indicator(__('To: {0}', [frm.doc.to_warehouse.split(' - ')[0]]), 'green');
    }
    
    if (frm.doc.total_qty) {
        frm.page.add_indicator(__('Qty: {0}', [frm.doc.total_qty.toFixed(2)]), 'orange');
    }
    
    if (frm.doc.docstatus === 1 && frm.doc.stock_entry) {
        frm.page.add_indicator(__('Stock: {0}', [frm.doc.stock_entry]), 'green');
    }
}

function show_warehouse_stock(frm) {
    frappe.call({
        method: 'petrodiesel.petrodiesel.doctype.internal_stock_transfer.internal_stock_transfer.get_warehouse_items',
        args: { warehouse: frm.doc.from_warehouse },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let html = '<h4>Available Stock in ' + frm.doc.from_warehouse + '</h4>';
                html += '<table class="table table-bordered table-sm">';
                html += '<tr><th>Item</th><th>Item Name</th><th>Available Qty</th><th>UOM</th><th>Action</th></tr>';
                
                $.each(r.message, function(i, item) {
                    html += `<tr>
                        <td>${item.item_code}</td>
                        <td>${item.item_name}</td>
                        <td><b>${item.qty.toFixed(2)}</b></td>
                        <td>${item.stock_uom}</td>
                        <td><button class="btn btn-xs btn-primary" onclick="add_transfer_item('${item.item_code}', ${item.qty}, '${item.stock_uom}')">Add</button></td>
                    </tr>`;
                });
                html += '</table>';
                
                frappe.msgprint({
                    title: __('Available Items'),
                    message: html,
                    wide: true
                });
            } else {
                frappe.msgprint({
                    title: __('No Stock'),
                    message: __('No items with stock found in {0}', [frm.doc.from_warehouse]),
                    indicator: 'orange'
                });
            }
        }
    });
}

// Helper function to add item from popup
window.add_transfer_item = function(item_code, available_qty, uom) {
    let frm = cur_frm;
    let row = frappe.model.add_child(frm.doc, 'Internal Stock Transfer Item', 'items');
    row.item_code = item_code;
    row.available_qty = available_qty;
    row.uom = uom;
    row.quantity = available_qty; // Default to full available qty
    frm.refresh_field('items');
    calculate_totals(frm);
};
