# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class CashierWiseShiftSaleEntry(Document):
    def validate(self):
        """Validate and calculate all totals"""
        self.calculate_fuel_sales()
        self.calculate_other_sales()
        self.calculate_credit_fuel()
        self.calculate_driver_cash()
        self.calculate_online_payments()
        self.calculate_employee_advances()
        self.calculate_total_sales()
        self.calculate_cash_reconciliation()
    
    def calculate_fuel_sales(self):
        """Calculate total fuel sales from nozzle readings"""
        total = 0
        for row in self.fuel_sales:
            if row.closing_reading and row.opening_reading:
                row.total_sale_qty = row.closing_reading - row.opening_reading
            row.actual_sale_qty = (row.total_sale_qty or 0) - (row.testing_qty or 0)
            if row.actual_sale_qty and row.rate_per_liter:
                row.amount = row.actual_sale_qty * row.rate_per_liter
            total += row.amount or 0
        self.total_fuel_sales = total
    
    def calculate_other_sales(self):
        """Calculate total other items (lubricants/accessories)"""
        total = 0
        for row in self.other_sales:
            if row.quantity and row.rate:
                row.amount = row.quantity * row.rate
            total += row.amount or 0
        self.total_other_sales = total
    
    def calculate_credit_fuel(self):
        """Calculate total credit fuel sales"""
        total = 0
        for row in self.credit_fuel_sales:
            if row.quantity_liters and row.rate_per_liter:
                row.amount = row.quantity_liters * row.rate_per_liter
            total += row.amount or 0
        self.total_credit_fuel = total
    
    def calculate_driver_cash(self):
        """Calculate total cash given to drivers"""
        total = 0
        for row in self.driver_cash_advances:
            total += row.cash_amount or 0
        self.total_driver_cash = total
    
    def calculate_online_payments(self):
        """Calculate total online payments"""
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
    
    def calculate_total_sales(self):
        """Calculate grand total sales"""
        self.total_sales = (
            (self.total_fuel_sales or 0) +
            (self.total_other_sales or 0) +
            (self.total_credit_fuel or 0)
        )
    
    def calculate_cash_reconciliation(self):
        """Calculate expected cash and variance"""
        # Expected = Total Sales - Online - Credit - Driver Cash - Emp Advances
        self.expected_cash = (
            (self.total_fuel_sales or 0) +
            (self.total_other_sales or 0) -
            (self.total_online or 0) -
            (self.total_driver_cash or 0) -
            (self.total_emp_advances or 0)
        )
        
        # Variance = Received - Expected
        received = self.cash_received or 0
        expected = self.expected_cash or 0
        self.cash_variance = received - expected


# Whitelisted API Methods

@frappe.whitelist()
def get_latest_fuel_price(fuel_item, posting_date=None):
    """Get latest fuel price from Fuel Price Update"""
    if not fuel_item:
        return 0
    
    if not posting_date:
        posting_date = frappe.utils.today()
    
    price_update = frappe.get_all('Fuel Price Update',
                                  filters={
                                      'docstatus': 1,
                                      'effective_date': ['<=', posting_date]
                                  },
                                  order_by='effective_date desc, effective_time desc',
                                  limit=1)
    
    if price_update:
        price_item = frappe.db.get_value('Fuel Price Update Item',
                                        filters={
                                            'parent': price_update[0].name,
                                            'fuel_item': fuel_item
                                        },
                                        fieldname='new_price')
        if price_item:
            return price_item
    
    return get_item_price(fuel_item)


@frappe.whitelist()
def get_item_price(item_code, price_list="Retail Fuel Prices"):
    """Get item price from Item Price"""
    if not item_code:
        return 0
    
    price = frappe.db.get_value('Item Price',
                               filters={
                                   'item_code': item_code,
                                   'price_list': price_list
                               },
                               fieldname='price_list_rate')
    
    return price or frappe.db.get_value('Item', item_code, 'standard_rate') or 0


@frappe.whitelist()
def get_item_details(item_code):
    """Get item name and price"""
    if not item_code:
        return {}
    
    item = frappe.db.get_value('Item', item_code, ['item_name', 'item_group'], as_dict=1)
    
    if not item:
        return {}
    
    is_fuel = item.item_group == 'Fuels'
    
    if is_fuel:
        price = get_latest_fuel_price(item_code)
    else:
        price = get_item_price(item_code, "Standard Selling")
    
    return {
        'item_name': item.item_name,
        'rate': price,
        'is_fuel': is_fuel
    }


@frappe.whitelist()
def get_nozzle_opening_reading(nozzle):
    """Get current reading from nozzle"""
    if not nozzle:
        return 0
    return frappe.db.get_value("Fuel Nozzle Master", nozzle, "current_reading") or 0
