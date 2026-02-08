// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cashier Wise Shift Sale Entry', {
    refresh: function(frm) {
        update_indicators(frm);
    },
    
    cashier: function(frm) {
        if (frm.doc.cashier && frm.doc.fuel_sales && frm.doc.fuel_sales.length === 0) {
            // Auto-fetch nozzles assigned to this cashier
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.cashier_wise_shift_sale_entry.cashier_wise_shift_sale_entry.get_cashier_nozzles',
                args: { cashier: frm.doc.cashier },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        r.message.forEach(function(nozzle) {
                            let row = frm.add_child('fuel_sales');
                            row.nozzle = nozzle.name;
                            row.fuel_item = nozzle.fuel_item;
                        });
                        frm.refresh_field('fuel_sales');
                        frappe.show_alert({
                            message: __('Nozzles loaded for cashier'),
                            indicator: 'green'
                        });
                    }
                }
            });
        }
    },
    
    cash_received: function(frm) {
        calculate_cash_reconciliation(frm);
        calculate_cash_handover(frm);
    },
    
    balance_with_shift_incharge: function(frm) {
        calculate_cash_handover(frm);
    },
    
    balance_with_pump_cashier: function(frm) {
        calculate_cash_handover(frm);
    }
});


// FUEL SALES (Nozzle Reading Detail)
frappe.ui.form.on('Nozzle Reading Detail', {
    nozzle: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.nozzle) {
            // Auto-fetch all nozzle details
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.cashier_wise_shift_sale_entry.cashier_wise_shift_sale_entry.get_nozzle_details',
                args: { nozzle: row.nozzle },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'fuel_item', r.message.fuel_item);
                        frappe.model.set_value(cdt, cdn, 'tank', r.message.source_tank);
                        frappe.model.set_value(cdt, cdn, 'opening_reading', r.message.current_reading);
                        
                        // Auto-fetch price after fuel_item is set
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
        if (row.fuel_item) {
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.cashier_wise_shift_sale_entry.cashier_wise_shift_sale_entry.get_latest_fuel_price',
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
    
    opening_reading: function(frm, cdt, cdn) { calculate_fuel_row(frm, cdt, cdn); },
    closing_reading: function(frm, cdt, cdn) { calculate_fuel_row(frm, cdt, cdn); },
    testing_qty: function(frm, cdt, cdn) { calculate_fuel_row(frm, cdt, cdn); },
    rate_per_liter: function(frm, cdt, cdn) { calculate_fuel_row(frm, cdt, cdn); },
    
    fuel_sales_remove: function(frm) { calculate_all_totals(frm); }
});


// OTHER ITEMS SALES (Lubricants/Accessories)
frappe.ui.form.on('Other Product Sales Detail', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.cashier_wise_shift_sale_entry.cashier_wise_shift_sale_entry.get_item_details',
                args: { item_code: row.item_code },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'item_name', r.message.item_name);
                        frappe.model.set_value(cdt, cdn, 'rate', r.message.rate);
                    }
                }
            });
        }
    },
    
    quantity: function(frm, cdt, cdn) { calculate_other_row(frm, cdt, cdn); },
    rate: function(frm, cdt, cdn) { calculate_other_row(frm, cdt, cdn); },
    
    other_sales_remove: function(frm) { calculate_all_totals(frm); }
});


// CREDIT FUEL SALES
frappe.ui.form.on('Credit Sale Item', {
    nozzle: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.nozzle) {
            frappe.db.get_value('Fuel Nozzle Master', row.nozzle, ['fuel_item', 'current_reading'])
                .then(r => {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'fuel_item', r.message.fuel_item);
                    }
                });
        }
    },
    
    fuel_item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.fuel_item) {
            frappe.call({
                method: 'petrodiesel.petrodiesel.doctype.cashier_wise_shift_sale_entry.cashier_wise_shift_sale_entry.get_latest_fuel_price',
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
    
    customer_name: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.customer_name) {
            frappe.db.get_value('Customer', {'customer_name': row.customer_name}, 'name')
                .then(r => {
                    if (r.message && r.message.name) {
                        row.customer = r.message.name;
                    }
                });
        }
    },
    
    amount: function(frm, cdt, cdn) { calculate_credit_row_from_amount(frm, cdt, cdn); },
    rate_per_liter: function(frm, cdt, cdn) { calculate_credit_row_from_amount(frm, cdt, cdn); },
    quantity_liters: function(frm, cdt, cdn) { calculate_credit_row_from_qty(frm, cdt, cdn); },
    
    credit_fuel_sales_remove: function(frm) { calculate_all_totals(frm); }
});


// DRIVER CASH ADVANCES
frappe.ui.form.on('Driver Cash Advance', {
    cash_amount: function(frm) { calculate_all_totals(frm); },
    driver_cash_advances_remove: function(frm) { calculate_all_totals(frm); }
});


// ONLINE PAYMENTS
frappe.ui.form.on('Online Payment Detail', {
    amount: function(frm) { calculate_all_totals(frm); },
    online_payments_remove: function(frm) { calculate_all_totals(frm); }
});


// EMPLOYEE ADVANCES
frappe.ui.form.on('Shift Employee Advance', {
    amount: function(frm) { calculate_all_totals(frm); },
    employee_advances_remove: function(frm) { calculate_all_totals(frm); }
});




// SHIFT EXPENSE DETAIL
frappe.ui.form.on('Shift Expense Detail', {
    amount: function(frm) { calculate_all_totals(frm); },
    shift_expenses_remove: function(frm) { calculate_all_totals(frm); }
});

// ========== CALCULATION FUNCTIONS ==========

function calculate_fuel_row(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    if (row.opening_reading && row.closing_reading) {
        row.total_sale_qty = row.closing_reading - row.opening_reading;
    }
    row.actual_sale_qty = (row.total_sale_qty || 0) - (row.testing_qty || 0);
    
    if (row.actual_sale_qty && row.rate_per_liter) {
        row.amount = row.actual_sale_qty * row.rate_per_liter;
    }
    
    frm.refresh_field('fuel_sales');
    calculate_all_totals(frm);
}

function calculate_other_row(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    if (row.quantity && row.rate) {
        row.amount = row.quantity * row.rate;
    }
    
    frm.refresh_field('other_sales');
    calculate_all_totals(frm);
}

function calculate_credit_row_from_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    // Calculate quantity from amount (reverse calculation)
    if (row.amount && row.rate_per_liter) {
        row.quantity_liters = row.amount / row.rate_per_liter;
    }
    
    frm.refresh_field('credit_fuel_sales');
    calculate_all_totals(frm);
}

function calculate_credit_row_from_qty(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    // Calculate amount from quantity
    if (row.quantity_liters && row.rate_per_liter) {
        row.amount = row.quantity_liters * row.rate_per_liter;
    }
    
    frm.refresh_field('credit_fuel_sales');
    calculate_all_totals(frm);
}

function calculate_all_totals(frm) {
    // Fuel sales
    let fuel_total = 0;
    $.each(frm.doc.fuel_sales || [], function(i, row) {
        fuel_total += row.amount || 0;
    });
    frm.set_value('total_fuel_sales', fuel_total);
    
    // Other sales
    let other_total = 0;
    $.each(frm.doc.other_sales || [], function(i, row) {
        other_total += row.amount || 0;
    });
    frm.set_value('total_other_sales', other_total);
    
    // Credit fuel
    let credit_total = 0;
    $.each(frm.doc.credit_fuel_sales || [], function(i, row) {
        credit_total += row.amount || 0;
    });
    frm.set_value('total_credit_fuel', credit_total);
    
    // Driver cash
    let driver_cash = 0;
    $.each(frm.doc.driver_cash_advances || [], function(i, row) {
        driver_cash += row.cash_amount || 0;
    });
    frm.set_value('total_driver_cash', driver_cash);
    
    // Online payments
    let online_total = 0;
    $.each(frm.doc.online_payments || [], function(i, row) {
        online_total += row.amount || 0;
    });
    frm.set_value('total_online', online_total);
    
    // Employee advances
    let emp_adv = 0;
    $.each(frm.doc.employee_advances || [], function(i, row) {
        emp_adv += row.amount || 0;
    });
    frm.set_value('total_emp_advances', emp_adv);
    
    // Expenses
    let expenses = 0;
    $.each(frm.doc.shift_expenses || [], function(i, row) {
        expenses += row.amount || 0;
    });
    frm.set_value('total_expenses', expenses);
    
    // Total sales
    let total_sales = fuel_total + other_total + credit_total;
    frm.set_value('total_sales', total_sales);
    
    // Cash reconciliation
    calculate_cash_reconciliation(frm);
    
    // Cash handover
    calculate_cash_handover(frm);
    
    // Update indicators
    update_indicators(frm);
}


function calculate_cash_handover(frm) {
    // Cash to Next Shift = Received - Incharge Balance - Cashier Balance
    let received = frm.doc.cash_received || 0;
    let incharge = frm.doc.balance_with_shift_incharge || 0;
    let cashier = frm.doc.balance_with_pump_cashier || 0;
    
    let next_shift_cash = received - incharge - cashier;
    frm.set_value('cash_given_to_next_shift', next_shift_cash);
    
    update_indicators(frm);
}

function calculate_cash_reconciliation(frm) {
    let expected = (frm.doc.previous_shift_cash || 0) +
                  (frm.doc.total_fuel_sales || 0) + 
                  (frm.doc.total_other_sales || 0) - 
                  (frm.doc.total_online || 0) - 
                  (frm.doc.total_driver_cash || 0) - 
                  (frm.doc.total_emp_advances || 0) -
                  (frm.doc.total_expenses || 0);
    
    frm.set_value('expected_cash', expected);
    
    let variance = (frm.doc.cash_received || 0) - expected;
    frm.set_value('cash_variance', variance);
    
    update_indicators(frm);
}

function update_indicators(frm) {
    // Clear existing indicators
    frm.page.clear_indicator();
    
    // Total Sales - Green
    if (frm.doc.total_sales) {
        frm.page.add_indicator(__('Total Sales: ₹{0}', [format_currency(frm.doc.total_sales)]), 'green');
    }
    
    // Cash Variance - Red/Green/Orange
    if (frm.doc.cash_variance) {
        let color = frm.doc.cash_variance == 0 ? 'green' : (frm.doc.cash_variance > 0 ? 'blue' : 'red');
        let label = frm.doc.cash_variance > 0 ? 'Excess' : (frm.doc.cash_variance < 0 ? 'Short' : 'Balanced');
        frm.page.add_indicator(__('{0}: ₹{1}', [label, Math.abs(frm.doc.cash_variance).toFixed(2)]), color);
    }
    
    // Credit Sales - Orange
    if (frm.doc.total_credit_fuel) {
        frm.page.add_indicator(__('Credit: ₹{0}', [format_currency(frm.doc.total_credit_fuel)]), 'orange');
    }
}
