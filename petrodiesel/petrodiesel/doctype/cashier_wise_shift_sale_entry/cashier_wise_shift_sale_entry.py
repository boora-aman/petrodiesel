# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt, nowdate, nowtime
from petrodiesel.utils import get_item_price as resolve_item_price, get_latest_fuel_price as resolve_fuel_price


class CashierWiseShiftSaleEntry(Document):
    def validate(self):
        """Validate and calculate all totals"""
        self.validate_nozzle_readings()
        self.calculate_fuel_sales()
        self.calculate_other_sales()
        self.calculate_credit_fuel()
        self.calculate_driver_cash()
        self.calculate_online_payments()
        self.calculate_employee_advances()
        self.calculate_expenses()
        self.calculate_total_sales()
        self.calculate_cash_reconciliation()
        self.validate_tank_stock_sufficiency()
        self.validate_credit_limits()
        self.validate_cash_variance()
    
    def validate_nozzle_readings(self):
        """Validate nozzle opening and closing readings"""
        for row in self.fuel_sales:
            if not row.nozzle:
                continue
            
            # Get nozzle master
            nozzle = frappe.get_doc("Fuel Nozzle Master", row.nozzle)
            
            # Validate closing > opening
            if flt(row.closing_reading) <= flt(row.opening_reading):
                frappe.throw(_(f"Row {row.idx}: Closing reading must be greater than opening reading for Nozzle {row.nozzle}"))
            
            # Validate opening reading matches last recorded reading
            if nozzle.current_reading and flt(row.opening_reading) < flt(nozzle.current_reading):
                frappe.throw(_(f"Row {row.idx}: Opening reading {row.opening_reading} cannot be less than last recorded reading {nozzle.current_reading} for Nozzle {row.nozzle}"))
    
    def calculate_fuel_sales(self):
        """Calculate total fuel sales from nozzle readings"""
        total = 0
        for row in self.fuel_sales:
            if row.closing_reading and row.opening_reading:
                row.total_sale_qty = flt(row.closing_reading) - flt(row.opening_reading)
            row.actual_sale_qty = flt(row.total_sale_qty) - flt(row.testing_qty or 0)
            if row.actual_sale_qty and row.rate_per_liter:
                row.amount = flt(row.actual_sale_qty) * flt(row.rate_per_liter)
            total += flt(row.amount)
        self.total_fuel_sales = total
    
    def calculate_other_sales(self):
        """Calculate total other items (lubricants/accessories)"""
        total = 0
        for row in self.other_sales:
            if row.quantity and row.rate:
                row.amount = flt(row.quantity) * flt(row.rate)
            total += flt(row.amount)
        self.total_other_sales = total
    
    def calculate_credit_fuel(self):
        """Calculate total credit fuel sales"""
        total = 0
        for row in self.credit_fuel_sales:
            if row.quantity_liters and row.rate_per_liter:
                row.amount = flt(row.quantity_liters) * flt(row.rate_per_liter)
            total += flt(row.amount)
        self.total_credit_fuel = total
    
    def calculate_driver_cash(self):
        """Calculate total cash given to drivers"""
        total = 0
        for row in self.driver_cash_advances:
            total += flt(row.cash_amount)
        self.total_driver_cash = total
    
    def calculate_online_payments(self):
        """Calculate total online payments"""
        total = 0
        for row in self.online_payments:
            total += flt(row.amount)
        self.total_online = total
    
    def calculate_employee_advances(self):
        """Calculate total employee advances"""
        total = 0
        for row in self.employee_advances:
            total += flt(row.amount)
        self.total_emp_advances = total
    
    def calculate_expenses(self):
        """Calculate total expenses"""
        total = 0
        for row in self.shift_expenses:
            total += flt(row.amount)
        self.total_expenses = total
    
    def calculate_total_sales(self):
        """Calculate grand total sales"""
        self.total_sales = (
            flt(self.total_fuel_sales) +
            flt(self.total_other_sales) +
            flt(self.total_credit_fuel)
        )
    
    def calculate_cash_reconciliation(self):
        """Calculate expected cash and variance"""
        # Expected Cash = Previous Cash + Cash Sales - Cash Outflows
        # Credit sales don't generate cash, so they must be excluded
        self.expected_cash = (
            flt(self.previous_shift_cash) +
            flt(self.total_fuel_sales) +
            flt(self.total_other_sales) -
            flt(self.total_credit_fuel) -  # Credit sales don't generate cash
            flt(self.total_online) -
            flt(self.total_driver_cash) -
            flt(self.total_emp_advances) -
            flt(self.total_expenses)
        )
        
        # Variance = Received - Expected
        received = flt(self.cash_received)
        expected = flt(self.expected_cash)
        self.cash_variance = received - expected
    
    def validate_tank_stock_sufficiency(self):
        """Validate that tank has sufficient stock for sales"""
        tank_consumption = {}
        
        for row in self.fuel_sales:
            if row.fuel_item and row.actual_sale_qty:
                nozzle = frappe.get_doc("Fuel Nozzle Master", row.nozzle)
                tank = nozzle.source_tank
                
                if tank:
                    if tank not in tank_consumption:
                        tank_consumption[tank] = 0
                    tank_consumption[tank] += flt(row.actual_sale_qty)
        
        for tank, consumption_liters in tank_consumption.items():
            tank_doc = frappe.get_doc("Fuel Tank Master", tank)
            current_stock_kl = flt(tank_doc.current_stock_level or 0)
            consumption_kl = consumption_liters / 1000
            
            if consumption_kl > current_stock_kl:
                frappe.throw(_(f"Insufficient stock in Tank {tank}. Available: {current_stock_kl} KL, Required: {consumption_kl} KL"))
    
    def validate_credit_limits(self):
        """Validate customer credit limits for credit sales"""
        from petrodiesel.utils import get_customer_total_outstanding
        
        for row in self.credit_fuel_sales:
            if not row.customer or not row.amount:
                continue
            
            credit_limit = frappe.db.get_value('Customer', row.customer, 'credit_limit')
            if not credit_limit:
                continue
            
            current_outstanding = get_customer_total_outstanding(row.customer)
            new_outstanding = current_outstanding + flt(row.amount)
            
            if new_outstanding > flt(credit_limit):
                frappe.msgprint(
                    _(f"Warning: Customer {row.customer} credit limit (₹{credit_limit}) will be exceeded. "
                      f"Current: ₹{current_outstanding}, After this sale: ₹{new_outstanding}"),
                    alert=True,
                    indicator='orange'
                )
    
    def validate_cash_variance(self):
        """Warn if cash variance is too high"""
        variance = abs(flt(self.cash_variance))
        try:
            threshold = frappe.db.get_single_value('Petrodiesel Settings', 'cash_variance_threshold') or 500
        except:
            threshold = 500
        
        if variance > threshold:
            frappe.msgprint(
                _(f"Cash variance of ₹{self.cash_variance} exceeds threshold of ₹{threshold}. "
                  f"Please verify cash count and transactions."),
                alert=True,
                indicator='orange'
            )
    
    def on_submit(self):
        """Update all masters and create credit sales"""
        self.update_nozzle_current_readings()
        self.update_tank_stock_levels()
        self.create_credit_sale_documents()
    
    def on_cancel(self):
        """Reverse all updates"""
        self.reverse_nozzle_readings()
        self.reverse_tank_stock()
        self.cancel_credit_sale_documents()
    
    def update_nozzle_current_readings(self):
        """Update current_reading in Fuel Nozzle Master after submit"""
        for row in self.fuel_sales:
            if row.nozzle and row.closing_reading:
                nozzle_doc = frappe.get_doc("Fuel Nozzle Master", row.nozzle)
                nozzle_doc.current_reading = flt(row.closing_reading)
                nozzle_doc.last_updated_on = self.posting_date
                nozzle_doc.last_shift = self.shift
                nozzle_doc.last_cashier = self.cashier
                nozzle_doc.flags.ignore_permissions = True
                nozzle_doc.save()
        
        frappe.msgprint(_("Nozzle readings updated successfully"), alert=True)
    
    def reverse_nozzle_readings(self):
        """Restore opening readings on cancel"""
        for row in self.fuel_sales:
            if row.nozzle and row.opening_reading:
                nozzle_doc = frappe.get_doc("Fuel Nozzle Master", row.nozzle)
                nozzle_doc.current_reading = flt(row.opening_reading)
                nozzle_doc.flags.ignore_permissions = True
                nozzle_doc.save()
    
    def update_tank_stock_levels(self):
        """Decrease tank stock based on fuel sales"""
        # Group by fuel item and tank
        tank_consumption = {}
        
        for row in self.fuel_sales:
            if row.fuel_item and row.actual_sale_qty:
                # Get tank from nozzle
                nozzle = frappe.get_doc("Fuel Nozzle Master", row.nozzle)
                tank = nozzle.source_tank
                
                if tank:
                    if tank not in tank_consumption:
                        tank_consumption[tank] = 0
                    tank_consumption[tank] += flt(row.actual_sale_qty)
        
        # Update each tank
        for tank, consumption_liters in tank_consumption.items():
            tank_doc = frappe.get_doc("Fuel Tank Master", tank)
            
            # Convert liters to KL
            consumption_kl = consumption_liters / 1000
            
            # Decrease current stock
            current_stock_kl = flt(tank_doc.current_stock_level or 0)
            new_stock_kl = current_stock_kl - consumption_kl
            
            tank_doc.current_stock_level = new_stock_kl
            tank_doc.last_updated_on = self.posting_date
            tank_doc.flags.ignore_permissions = True
            tank_doc.save()
        
        frappe.msgprint(_("Tank stock levels updated"), alert=True)
    
    def reverse_tank_stock(self):
        """Add back consumption to tank on cancel"""
        tank_consumption = {}
        
        for row in self.fuel_sales:
            if row.fuel_item and row.actual_sale_qty:
                nozzle = frappe.get_doc("Fuel Nozzle Master", row.nozzle)
                tank = nozzle.source_tank
                
                if tank:
                    if tank not in tank_consumption:
                        tank_consumption[tank] = 0
                    tank_consumption[tank] += flt(row.actual_sale_qty)
        
        for tank, consumption_liters in tank_consumption.items():
            tank_doc = frappe.get_doc("Fuel Tank Master", tank)
            
            consumption_kl = consumption_liters / 1000
            current_stock_kl = flt(tank_doc.current_stock_level or 0)
            new_stock_kl = current_stock_kl + consumption_kl
            
            tank_doc.current_stock_level = new_stock_kl
            tank_doc.flags.ignore_permissions = True
            tank_doc.save()
    
    def create_credit_sale_documents(self):
        """Create individual Credit Sale documents for each credit transaction"""
        created_count = 0
        
        for row in self.credit_fuel_sales:
            if not row.customer or flt(row.amount) <= 0:
                continue
            
            try:
                credit_doc = frappe.get_doc({
                    "doctype": "Credit Sale",
                    "naming_series": "CS-.YYYY.-",
                    "posting_date": self.posting_date,
                    "posting_time": self.posting_time or nowtime(),
                    "shift": self.shift,
                    "customer": row.customer,
                    "reference_type": "Cashier Wise Shift Sale Entry",
                    "reference_name": self.name,
                    "payment_status": "Unpaid",
                    "items": [{
                        "nozzle": row.nozzle or "",
                        "fuel_item": row.fuel_item or "",
                        "item_code": row.fuel_item or "",
                        "vehicle_number": row.vehicle_number or "",
                        "slip_number": row.slip_number or "",
                        "driver_name": row.driver_name or "",
                        "quantity_liters": flt(row.quantity_liters),
                        "rate_per_liter": flt(row.rate_per_liter),
                        "amount": flt(row.amount)
                    }]
                })
                
                credit_doc.flags.ignore_permissions = True
                credit_doc.flags.ignore_mandatory = True
                credit_doc.insert()
                credit_doc.submit()
                
                created_count += 1
                
            except Exception as e:
                frappe.log_error(f"Failed to create Credit Sale for customer {row.customer}: {str(e)}")
        
        if created_count > 0:
            frappe.msgprint(_(f"{created_count} Credit Sale document(s) created successfully"), alert=True)
    
    def cancel_credit_sale_documents(self):
        """Cancel linked Credit Sale documents"""
        credit_sales = frappe.get_all("Credit Sale",
            filters={
                "reference_type": "Cashier Wise Shift Sale Entry",
                "reference_name": self.name,
                "docstatus": 1
            }
        )
        
        for cs in credit_sales:
            try:
                cs_doc = frappe.get_doc("Credit Sale", cs.name)
                cs_doc.flags.ignore_permissions = True
                cs_doc.cancel()
            except Exception as e:
                frappe.log_error(f"Failed to cancel Credit Sale {cs.name}: {str(e)}")


# Whitelisted API Methods

@frappe.whitelist()
def get_latest_fuel_price(fuel_item, posting_date=None):
    """Get latest fuel price from Fuel Price Update"""
    return resolve_fuel_price(fuel_item, posting_date)


@frappe.whitelist()
def get_item_price(item_code, price_list="Retail Fuel Prices"):
    """Get item price from Item Price"""
    return resolve_item_price(item_code, price_list)


@frappe.whitelist()
def get_cashier_nozzles(cashier):
    """Get nozzles assigned to a cashier"""
    if not cashier:
        return []
    
    # Get nozzles where this cashier is assigned
    nozzles = frappe.get_all('Fuel Nozzle Master',
        filters={'assigned_cashier': cashier, 'status': 'Active'},
        fields=['name', 'fuel_item', 'nozzle_number', 'current_reading']
    )
    
    # If no assigned nozzles, return all active nozzles
    if not nozzles:
        nozzles = frappe.get_all('Fuel Nozzle Master',
            filters={'status': 'Active'},
            fields=['name', 'fuel_item', 'nozzle_number', 'current_reading']
        )
    
    return nozzles

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
        price = resolve_fuel_price(item_code)
    else:
        price = resolve_item_price(item_code, "Standard Selling")
    
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


@frappe.whitelist()
def get_nozzle_details(nozzle):
    """Get nozzle details including fuel item and tank"""
    if not nozzle:
        return {}
    
    return frappe.get_value("Fuel Nozzle Master", nozzle, 
                           ["fuel_item", "source_tank", "current_reading"], as_dict=1) or {}
