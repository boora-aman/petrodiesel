# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    if not filters.get("shift"):
        frappe.throw(_("Please select a Shift"))
    
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {"fieldname": "category", "label": _("Category"), "fieldtype": "Data", "width": 200},
        {"fieldname": "detail_1", "label": _("Details"), "fieldtype": "Data", "width": 250},
        {"fieldname": "detail_2", "label": _("Info"), "fieldtype": "Data", "width": 150},
        {"fieldname": "qty", "label": _("Qty/Value"), "fieldtype": "Data", "width": 120},
        {"fieldname": "amount", "label": _("Amount (₹)"), "fieldtype": "Currency", "width": 150}
    ]

def get_data(filters):
    shift_entry = frappe.get_doc('Shift Sale Entry', filters.get("shift"))
    data = []
    
    # HEADER
    data.append({
        "category": f"<b>DAILY SALES REPORT</b>",
        "detail_1": f"<b>Shift: {shift_entry.shift}</b>",
        "detail_2": f"<b>Date: {shift_entry.posting_date}</b>",
        "qty": f"<b>DSR: {shift_entry.name}</b>",
        "amount": None
    })
    data.append({"category": "", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    
    # SALES SUMMARY
    data.append({"category": "<b>SALES SUMMARY</b>", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    data.append({"category": "Fuel Sales", "detail_1": "Petrol + Diesel", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_fuel_sales, 2)})
    data.append({"category": "Other Products", "detail_1": "Oil, Lubricants, etc", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_other_sales, 2)})
    data.append({"category": "<b>TOTAL SALES</b>", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_sales, 2)})
    data.append({"category": "", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    
    # PAYMENT BREAKDOWN
    data.append({"category": "<b>PAYMENT BREAKDOWN</b>", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    data.append({"category": "Cash Received", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.cash_received, 2)})
    data.append({"category": "Credit Sales", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_credit_fuel, 2)})
    data.append({"category": "Digital Payments", "detail_1": "UPI, Card, etc", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_online, 2)})
    data.append({"category": "", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    
    # CASH FLOW
    data.append({"category": "<b>CASH FLOW</b>", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    data.append({"category": "Previous Shift Cash", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.previous_shift_cash, 2)})
    data.append({"category": "Driver Cash Given", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_driver_cash, 2)})
    data.append({"category": "Employee Advances", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_emp_advances, 2)})
    data.append({"category": "Expenses", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_expenses, 2)})
    data.append({"category": "Cash to Next Shift", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.cash_given_to_next_shift, 2)})
    data.append({"category": "Balance (Pump Cashier)", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.balance_with_pump_cashier, 2)})
    data.append({"category": "Balance (Shift Incharge)", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.balance_with_shift_incharge, 2)})
    data.append({"category": "<b>Cash Variance</b>", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.cash_variance, 2)})
    data.append({"category": "", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    
    # FUEL TYPE SUMMARY
    data.append({"category": "<b>FUEL SUMMARY</b>", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    fuel_summary = frappe.get_all('Fuel Type Sales Summary',
        filters={'parent': shift_entry.name},
        fields=['fuel_item', 'total_qty', 'rate', 'total_amount'],
        order_by='idx')
    
    if fuel_summary:
        for f in fuel_summary:
            data.append({
                "category": f.fuel_item,
                "detail_1": f"Rate: ₹{f.rate:.2f}/L",
                "detail_2": "",
                "qty": f"{f.total_qty:.2f} L",
                "amount": flt(f.total_amount, 2)
            })
    data.append({"category": "", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    
    # NOZZLE READINGS
    data.append({"category": "<b>NOZZLE READINGS</b>", "detail_1": "Opening → Closing", "detail_2": "Testing", "qty": "Actual Sale (L)", "amount": None})
    nozzles = frappe.get_all('Shift Nozzle Reading',
        filters={'parent': shift_entry.name},
        fields=['nozzle', 'fuel_item', 'opening_reading', 'closing_reading', 'testing_qty', 'actual_sale_qty', 'amount'],
        order_by='idx')
    
    if nozzles:
        for n in nozzles:
            data.append({
                "category": f"{n.nozzle} ({n.fuel_item})",
                "detail_1": f"{n.opening_reading:.2f} → {n.closing_reading:.2f}",
                "detail_2": f"{n.testing_qty:.2f} L",
                "qty": f"{n.actual_sale_qty:.2f}",
                "amount": flt(n.amount, 2)
            })
    data.append({"category": "", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    
    # TANK CONSUMPTION
    data.append({"category": "<b>TANK CONSUMPTION</b>", "detail_1": "Fuel Type", "detail_2": "Nozzles", "qty": "Consumption (L)", "amount": None})
    tanks = frappe.get_all('Tank Consumption Summary',
        filters={'parent': shift_entry.name},
        fields=['tank', 'fuel_item', 'total_consumption', 'nozzle_count'],
        order_by='idx')
    
    if tanks:
        for t in tanks:
            data.append({
                "category": t.tank,
                "detail_1": t.fuel_item,
                "detail_2": f"{t.nozzle_count} units",
                "qty": f"{t.total_consumption:.2f}",
                "amount": None
            })
    data.append({"category": "", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    
    # CREDIT SALES
    data.append({"category": "<b>CREDIT SALES</b>", "detail_1": "Vehicle | Slip", "detail_2": "Fuel", "qty": "Qty (L)", "amount": None})
    credit_sales = frappe.get_all('Shift Credit Sale', 
        filters={'parent': shift_entry.name},
        fields=['customer', 'vehicle_number', 'fuel_item', 'slip_number', 'quantity_liters', 'amount'],
        order_by='idx')
    
    if credit_sales:
        for cs in credit_sales:
            veh = cs.vehicle_number or "-"
            slip = cs.slip_number or "-"
            data.append({
                "category": cs.customer or "N/A",
                "detail_1": f"{veh} | {slip}",
                "detail_2": cs.fuel_item,
                "qty": f"{cs.quantity_liters:.2f}",
                "amount": flt(cs.amount, 2)
            })
        data.append({"category": "<b>TOTAL CREDIT</b>", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_credit_fuel, 2)})
    data.append({"category": "", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    
    # OTHER PRODUCT SALES
    data.append({"category": "<b>OTHER SALES</b>", "detail_1": "Item Name", "detail_2": "Type", "qty": "Qty", "amount": None})
    other_sales = frappe.get_all('Shift Other Sales',
        filters={'parent': shift_entry.name},
        fields=['item_name', 'item_code', 'product_type', 'quantity', 'rate', 'amount'],
        order_by='idx')
    
    if other_sales:
        for o in other_sales:
            item = o.item_name or o.item_code
            data.append({
                "category": item,
                "detail_1": f"Rate: ₹{o.rate:.2f}",
                "detail_2": o.product_type,
                "qty": f"{o.quantity:.2f}",
                "amount": flt(o.amount, 2)
            })
        data.append({"category": "<b>TOTAL OTHER</b>", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_other_sales, 2)})
    data.append({"category": "", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    
    # EXPENSES
    data.append({"category": "<b>EXPENSES</b>", "detail_1": "Description", "detail_2": "Type", "qty": "", "amount": None})
    expenses = frappe.get_all('Shift Expense Detail',
        filters={'parent': shift_entry.name},
        fields=['expense_type', 'description', 'amount'],
        order_by='idx')
    
    if expenses:
        for exp in expenses:
            desc = exp.description or "-"
            data.append({
                "category": exp.expense_type,
                "detail_1": desc,
                "detail_2": "",
                "qty": "",
                "amount": flt(exp.amount, 2)
            })
        data.append({"category": "<b>TOTAL EXPENSES</b>", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_expenses, 2)})
    data.append({"category": "", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    
    # DRIVER CASH
    data.append({"category": "<b>DRIVER CASH</b>", "detail_1": "Customer | Vehicle", "detail_2": "Driver", "qty": "Reason", "amount": None})
    driver_cash = frappe.get_all('Shift Driver Cash',
        filters={'parent': shift_entry.name},
        fields=['customer', 'vehicle_number', 'driver_name', 'cash_amount', 'reason'],
        order_by='idx')
    
    if driver_cash:
        for d in driver_cash:
            veh = d.vehicle_number or "-"
            driver = d.driver_name or "-"
            reason = d.reason or "-"
            data.append({
                "category": f"{d.customer or 'N/A'} | {veh}",
                "detail_1": driver,
                "detail_2": "",
                "qty": reason,
                "amount": flt(d.cash_amount, 2)
            })
        data.append({"category": "<b>TOTAL DRIVER CASH</b>", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_driver_cash, 2)})
    data.append({"category": "", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    
    # ONLINE PAYMENTS
    data.append({"category": "<b>ONLINE PAYMENTS</b>", "detail_1": "Account/UPI", "detail_2": "Reference", "qty": "", "amount": None})
    online = frappe.get_all('Shift Online Payment',
        filters={'parent': shift_entry.name},
        fields=['payment_method', 'account_id', 'amount', 'reference_number'],
        order_by='idx')
    
    if online:
        for op in online:
            acc = op.account_id or "-"
            ref = op.reference_number or "-"
            data.append({
                "category": op.payment_method,
                "detail_1": acc,
                "detail_2": ref,
                "qty": "",
                "amount": flt(op.amount, 2)
            })
        data.append({"category": "<b>TOTAL ONLINE</b>", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_online, 2)})
    data.append({"category": "", "detail_1": "", "detail_2": "", "qty": "", "amount": None})
    
    # EMPLOYEE ADVANCES
    data.append({"category": "<b>EMPLOYEE ADVANCES</b>", "detail_1": "Employee Name", "detail_2": "Type", "qty": "Reason", "amount": None})
    emp_advances = frappe.get_all('Shift Employee Advance',
        filters={'parent': shift_entry.name},
        fields=['employee', 'employee_name', 'advance_type', 'amount', 'reason'],
        order_by='idx')
    
    if emp_advances:
        for ea in emp_advances:
            emp = ea.employee_name or ea.employee
            reason = ea.reason or "-"
            data.append({
                "category": emp,
                "detail_1": "",
                "detail_2": ea.advance_type,
                "qty": reason,
                "amount": flt(ea.amount, 2)
            })
        data.append({"category": "<b>TOTAL ADVANCES</b>", "detail_1": "", "detail_2": "", "qty": "", "amount": flt(shift_entry.total_emp_advances, 2)})
    
    return data
