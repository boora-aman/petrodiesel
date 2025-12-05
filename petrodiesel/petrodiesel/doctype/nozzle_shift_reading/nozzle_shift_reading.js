// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on('Nozzle Shift Reading', {
    refresh: function(frm) {
        // Add custom buttons or actions here if needed
    },
    
    cash_received: function(frm) {
        calculate_variance(frm);
    },
    
    credit_sales_amount: function(frm) {
        calculate_expected_collection(frm);
    }
});

// Child table: Nozzle Reading Detail
frappe.ui.form.on('Nozzle Reading Detail', {
    opening_reading: function(frm, cdt, cdn) {
        calculate_nozzle_row(frm, cdt, cdn);
    },
    
    closing_reading: function(frm, cdt, cdn) {
        calculate_nozzle_row(frm, cdt, cdn);
    },
    
    testing_qty: function(frm, cdt, cdn) {
        calculate_nozzle_row(frm, cdt, cdn);
    },
    
    rate_per_liter: function(frm, cdt, cdn) {
        calculate_nozzle_row(frm, cdt, cdn);
    },
    
    nozzle: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        
        // Auto-fetch opening reading from nozzle's current reading
        if (row.nozzle) {
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.nozzle_shift_reading.nozzle_shift_reading.get_nozzle_opening_reading',
                args: {
                    nozzle: row.nozzle
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'opening_reading', r.message);
                    }
                }
            });
        }
    },
    
    fuel_item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        
        // Auto-fetch fuel rate
        if (row.fuel_item) {
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.nozzle_shift_reading.nozzle_shift_reading.get_fuel_rate',
                args: {
                    fuel_item: row.fuel_item
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'rate_per_liter', r.message);
                    }
                }
            });
        }
    },
    
    nozzle_readings_remove: function(frm) {
        calculate_all_totals(frm);
    }
});

// Child table: Online Payment Detail
frappe.ui.form.on('Online Payment Detail', {
    amount: function(frm) {
        calculate_online_total(frm);
    },
    
    online_payment_details_remove: function(frm) {
        calculate_online_total(frm);
    }
});

// Child table: Shift Employee Advance
frappe.ui.form.on('Shift Employee Advance', {
    amount: function(frm) {
        calculate_advance_total(frm);
    },
    
    employee_advances_remove: function(frm) {
        calculate_advance_total(frm);
    }
});

// Helper Functions

function calculate_nozzle_row(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    // Calculate total sale qty
    if (row.opening_reading && row.closing_reading) {
        row.total_sale_qty = row.closing_reading - row.opening_reading;
    } else {
        row.total_sale_qty = 0;
    }
    
    // Calculate actual sale qty
    row.actual_sale_qty = (row.total_sale_qty || 0) - (row.testing_qty || 0);
    
    // Calculate amount
    if (row.actual_sale_qty && row.rate_per_liter) {
        row.amount = row.actual_sale_qty * row.rate_per_liter;
    } else {
        row.amount = 0;
    }
    
    // Refresh row
    frm.refresh_field('nozzle_readings');
    
    // Recalculate totals
    calculate_all_totals(frm);
}

function calculate_all_totals(frm) {
    let total_qty = 0;
    let total_amount = 0;
    
    // Sum all nozzle readings
    $.each(frm.doc.nozzle_readings || [], function(i, row) {
        total_qty += row.actual_sale_qty || 0;
        total_amount += row.amount || 0;
    });
    
    frm.set_value('total_fuel_sales_qty', total_qty);
    frm.set_value('total_fuel_sales_amount', total_amount);
    
    // Calculate total sales
    let total_sales = (total_amount || 0) + 
                     (frm.doc.lubricant_sales_amount || 0) + 
                     (frm.doc.accessories_sales_amount || 0);
    frm.set_value('total_sales_amount', total_sales);
    
    // Recalculate expected collection
    calculate_expected_collection(frm);
}

function calculate_online_total(frm) {
    let total = 0;
    
    $.each(frm.doc.online_payment_details || [], function(i, row) {
        total += row.amount || 0;
    });
    
    frm.set_value('total_online_collection', total);
    
    // Recalculate expected collection
    calculate_expected_collection(frm);
}

function calculate_advance_total(frm) {
    let total = 0;
    
    $.each(frm.doc.employee_advances || [], function(i, row) {
        total += row.amount || 0;
    });
    
    frm.set_value('total_employee_advances', total);
    
    // Recalculate variance
    calculate_variance(frm);
}

function calculate_expected_collection(frm) {
    let expected = (frm.doc.total_sales_amount || 0) - 
                  (frm.doc.total_online_collection || 0) - 
                  (frm.doc.credit_sales_amount || 0);
    
    frm.set_value('expected_cash_collection', expected);
    
    // Recalculate variance
    calculate_variance(frm);
}

function calculate_variance(frm) {
    let expected = (frm.doc.expected_cash_collection || 0) - (frm.doc.total_employee_advances || 0);
    let received = frm.doc.cash_received || 0;
    
    if (received < expected) {
        frm.set_value('cash_shortage', expected - received);
        frm.set_value('cash_excess', 0);
    } else {
        frm.set_value('cash_excess', received - expected);
        frm.set_value('cash_shortage', 0);
    }
}
