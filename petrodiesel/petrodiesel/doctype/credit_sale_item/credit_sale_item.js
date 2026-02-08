// Copyright (c) 2026, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on('Credit Sale Item', {
    nozzle: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.nozzle) {
            // Auto-fetch fuel item and rate from nozzle
            frappe.db.get_value('Fuel Nozzle Master', row.nozzle, ['fuel_item', 'source_tank', 'current_reading'])
                .then(r => {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'fuel_item', r.message.fuel_item);
                        
                        // Fetch rate for fuel item
                        if (r.message.fuel_item) {
                            fetch_fuel_rate(frm, cdt, cdn, r.message.fuel_item);
                        }
                    }
                });
        }
    },
    
    fuel_item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.fuel_item && !row.rate_per_liter) {
            fetch_fuel_rate(frm, cdt, cdn, row.fuel_item);
        }
    },
    
    quantity_liters: function(frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    },
    
    rate_per_liter: function(frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    }
});

function fetch_fuel_rate(frm, cdt, cdn, fuel_item) {
    frappe.call({
        method: 'petrodiesel.petrodiesel.doctype.shift_sale_entry.shift_sale_entry.get_latest_fuel_price',
        args: {
            fuel_item: fuel_item,
            posting_date: frm.doc.posting_date
        },
        callback: function(r) {
            if (r.message) {
                frappe.model.set_value(cdt, cdn, 'rate_per_liter', r.message);
            }
        }
    });
}

function calculate_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.quantity_liters && row.rate_per_liter) {
        frappe.model.set_value(cdt, cdn, 'amount', flt(row.quantity_liters) * flt(row.rate_per_liter));
    }
}
