# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class ShiftSaleEntry(Document):
    def validate(self):
        """Validate and calculate all totals + summaries"""
        self.fetch_previous_shift_cash()
        self.calculate_nozzle_readings()
        self.calculate_fuel_type_summary()
        self.calculate_tank_consumption()
        self.calculate_other_sales()
        self.calculate_credit_sales()
        self.calculate_driver_cash()
        self.calculate_online_payments()
        self.calculate_employee_advances()
        self.calculate_expenses()
        self.calculate_total_sales()
        self.calculate_cash_reconciliation()
        self.calculate_cash_handover()
    
    def fetch_previous_shift_cash(self):
        """Auto-fetch cash from previous shift"""
        if not self.posting_date or not self.shift:
            return
        
        # Get previous shift entry for same date or previous date
        previous_entry = frappe.get_all('Shift Sale Entry',
            filters={
                'posting_date': ['<=', self.posting_date],
                'docstatus': 1,
                'name': ['!=', self.name]
            },
            fields=['name', 'cash_given_to_next_shift', 'posting_date'],
            order_by='posting_date desc, creation desc',
            limit=1
        )
        
        if previous_entry and previous_entry[0].cash_given_to_next_shift:
            self.previous_shift_cash = previous_entry[0].cash_given_to_next_shift
    
    def calculate_nozzle_readings(self):
        """Calculate totals from nozzle readings"""
        total = 0
        for row in self.nozzle_readings:
            if row.closing_reading and row.opening_reading:
                row.total_sale_qty = row.closing_reading - row.opening_reading
            row.actual_sale_qty = (row.total_sale_qty or 0) - (row.testing_qty or 0)
            if row.actual_sale_qty and row.rate_per_liter:
                row.amount = row.actual_sale_qty * row.rate_per_liter
            total += row.amount or 0
        self.total_fuel_sales = total
    
    def calculate_fuel_type_summary(self):
        """Auto-calculate fuel type summary from nozzle readings"""
        fuel_summary = {}
        
        for row in self.nozzle_readings:
            if row.fuel_item and row.actual_sale_qty:
                if row.fuel_item not in fuel_summary:
                    fuel_summary[row.fuel_item] = {
                        'qty': 0,
                        'amount': 0,
                        'rate': row.rate_per_liter or 0
                    }
                fuel_summary[row.fuel_item]['qty'] += row.actual_sale_qty
                fuel_summary[row.fuel_item]['amount'] += row.amount or 0
        
        # Clear and rebuild summary table
        self.fuel_type_summary = []
        for fuel_item, data in fuel_summary.items():
            self.append('fuel_type_summary', {
                'fuel_item': fuel_item,
                'total_qty': data['qty'],
                'rate': data['rate'],
                'total_amount': data['amount']
            })
    
    def calculate_tank_consumption(self):
        """Auto-calculate tank consumption from nozzle readings"""
        tank_summary = {}
        
        for row in self.nozzle_readings:
            if row.tank and row.actual_sale_qty:
                if row.tank not in tank_summary:
                    tank_summary[row.tank] = {
                        'fuel_item': row.fuel_item,
                        'consumption': 0,
                        'nozzle_count': 0
                    }
                tank_summary[row.tank]['consumption'] += row.actual_sale_qty
                tank_summary[row.tank]['nozzle_count'] += 1
        
        # Clear and rebuild tank summary
        self.tank_consumption = []
        for tank, data in tank_summary.items():
            self.append('tank_consumption', {
                'tank': tank,
                'fuel_item': data['fuel_item'],
                'total_consumption': data['consumption'],
                'nozzle_count': data['nozzle_count']
            })
    
    def calculate_other_sales(self):
        """Calculate total other items"""
        total = 0
        for row in self.other_sales:
            if row.quantity and row.rate:
                row.amount = row.quantity * row.rate
            total += row.amount or 0
        self.total_other_sales = total
    
    def calculate_credit_sales(self):
        """Calculate total credit fuel (amount-based)"""
        total = 0
        for row in self.credit_fuel_sales:
            if row.amount and row.rate_per_liter:
                row.quantity_liters = row.amount / row.rate_per_liter
            total += row.amount or 0
        self.total_credit_fuel = total
    
    def calculate_driver_cash(self):
        """Calculate total driver cash"""
        total = 0
        for row in self.driver_cash_advances:
            total += row.cash_amount or 0
        self.total_driver_cash = total
    
    def calculate_online_payments(self):
        """Calculate total online"""
        total = 0
        for row in self.online_payments:
            total += row.amount or 0
        self.total_online = total
    
    def calculate_employee_advances(self):
        """Calculate total employee advances"""
        total = 0
        for row in self.employee_advances:
            total += row.amount or 0
        self.total_emp_advances = total
    
    def calculate_expenses(self):
        """Calculate total expenses"""
        total = 0
        for row in self.shift_expenses:
            total += row.amount or 0
        self.total_expenses = total
    
    def calculate_total_sales(self):
        """Calculate grand total"""
        self.total_sales = (
            (self.total_fuel_sales or 0) +
            (self.total_other_sales or 0) +
            (self.total_credit_fuel or 0)
        )
    
    def calculate_cash_reconciliation(self):
        """Calculate expected cash and variance"""
        # Add previous shift cash to expected
        self.expected_cash = (
            (self.previous_shift_cash or 0) +
            (self.total_fuel_sales or 0) +
            (self.total_other_sales or 0) -
            (self.total_online or 0) -
            (self.total_driver_cash or 0) -
            (self.total_emp_advances or 0) -
            (self.total_expenses or 0)
        )
        
        received = self.cash_received or 0
        expected = self.expected_cash or 0
        self.cash_variance = received - expected
    
    def calculate_cash_handover(self):
        """Calculate cash to next shift"""
        # Cash to next shift = Cash Received - Balances kept
        total_received = self.cash_received or 0
        incharge_balance = self.balance_with_shift_incharge or 0
        cashier_balance = self.balance_with_pump_cashier or 0
        
        self.cash_given_to_next_shift = total_received - incharge_balance - cashier_balance


# API Methods

@frappe.whitelist()
def get_nozzle_details(nozzle):
    """Get nozzle fuel_item, tank, and opening reading"""
    if not nozzle:
        return {}
    
    nozzle_doc = frappe.get_value("Fuel Nozzle Master", nozzle, 
                                  ["fuel_item", "source_tank", "current_reading"], as_dict=1)
    return nozzle_doc or {}


@frappe.whitelist()
def get_latest_fuel_price(fuel_item, posting_date=None):
    """Get fuel price"""
    if not fuel_item:
        return 0
    
    if not posting_date:
        posting_date = frappe.utils.today()
    
    price_update = frappe.get_all('Fuel Price Update',
                                  filters={'docstatus': 1, 'effective_date': ['<=', posting_date]},
                                  order_by='effective_date desc, effective_time desc',
                                  limit=1)
    
    if price_update:
        price = frappe.db.get_value('Fuel Price Update Item',
                                   filters={'parent': price_update[0].name, 'fuel_item': fuel_item},
                                   fieldname='new_price')
        if price:
            return price
    
    # Fallback to Item Price or standard rate
    item_price = frappe.db.get_value('Item Price', 
                                     filters={'item_code': fuel_item},
                                     fieldname='price_list_rate')
    if item_price:
        return item_price
    
    return frappe.db.get_value('Item', fuel_item, 'standard_rate') or 0


@frappe.whitelist()
def get_item_details(item_code):
    """Get item details with price"""
    if not item_code:
        return {}
    
    item = frappe.db.get_value('Item', item_code, ['item_name', 'item_group'], as_dict=1)
    if not item:
        return {}
    
    # Get price from Item Price
    price = frappe.db.get_value('Item Price', 
                               filters={'item_code': item_code},
                               fieldname='price_list_rate')
    
    if not price:
        price = frappe.db.get_value('Item', item_code, 'standard_rate') or 0
    
    return {
        'item_name': item.item_name,
        'standard_rate': price
    }
