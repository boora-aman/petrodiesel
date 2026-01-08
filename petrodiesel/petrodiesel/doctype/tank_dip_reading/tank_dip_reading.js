// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tank Dip Reading', {
    refresh: function(frm) {
        update_indicators(frm);
        
        if (frm.doc.docstatus === 1 && frm.doc.stock_entry) {
            frm.add_custom_button(__('View Stock Entry'), function() {
                frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry);
            });
        }
    },
    
    posting_date: function(frm) {
        if (!frm.doc.posting_time) {
            frm.set_value('posting_time', frappe.datetime.now_time());
        }
    }
});

frappe.ui.form.on('Tank Dip Detail', {
    tank: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.tank) {
            // Auto-fetch current dip reading
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.tank_dip_reading.tank_dip_reading.get_tank_current_dip',
                args: { tank: row.tank },
                callback: function(r) {
                    if (r.message !== undefined) {
                        frappe.model.set_value(cdt, cdn, 'previous_dip_reading', r.message);
                    }
                }
            });
        }
    },
    
    current_dip_reading: function(frm, cdt, cdn) {
        calculate_row(frm, cdt, cdn);
    },
    
    system_stock: function(frm, cdt, cdn) {
        calculate_row(frm, cdt, cdn);
    },
    
    tank_dip_details_remove: function(frm) {
        calculate_totals(frm);
    }
});

function calculate_row(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    // Calculate variance
    row.variance = flt(row.current_dip_reading) - flt(row.system_stock);
    
    if (row.system_stock) {
        row.variance_percentage = (row.variance / row.system_stock) * 100;
    }
    
    frm.refresh_field('tank_dip_details');
    calculate_totals(frm);
}

function calculate_totals(frm) {
    let total_dip = 0;
    let total_system = 0;
    
    $.each(frm.doc.tank_dip_details || [], function(i, row) {
        total_dip += flt(row.current_dip_reading);
        total_system += flt(row.system_stock);
    });
    
    frm.set_value('total_stock_as_per_dip', total_dip);
    frm.set_value('total_stock_as_per_system', total_system);
    
    let variance = total_dip - total_system;
    frm.set_value('variance', variance);
    
    if (total_system) {
        frm.set_value('variance_percentage', (variance / total_system) * 100);
    }
    
    update_indicators(frm);
}

function update_indicators(frm) {
    frm.page.clear_indicator();
    
    if (frm.doc.total_stock_as_per_dip) {
        frm.page.add_indicator(__('Dip: {0} KL', [frm.doc.total_stock_as_per_dip.toFixed(3)]), 'blue');
    }
    
    if (frm.doc.total_stock_as_per_system) {
        frm.page.add_indicator(__('System: {0} KL', [frm.doc.total_stock_as_per_system.toFixed(3)]), 'green');
    }
    
    if (frm.doc.variance) {
        let color = Math.abs(frm.doc.variance) < 0.01 ? 'green' : (frm.doc.variance > 0 ? 'orange' : 'red');
        frm.page.add_indicator(__('Variance: {0} KL', [frm.doc.variance.toFixed(3)]), color);
    }
}
