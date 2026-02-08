# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt, nowdate, nowtime
from petrodiesel.utils import get_item_price, get_latest_fuel_price as resolve_fuel_price


class ShiftSaleEntry(Document):
    def validate(self):
        """Validate and calculate all totals + summaries"""
        self.validate_nozzle_readings()
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
        self.validate_tank_stock_sufficiency()
        self.validate_credit_limits()
        self.validate_cash_variance()
    
    def validate_nozzle_readings(self):
        """Validate nozzle opening and closing readings"""
        for row in self.nozzle_readings:
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
                row.total_sale_qty = flt(row.closing_reading) - flt(row.opening_reading)
            row.actual_sale_qty = flt(row.total_sale_qty) - flt(row.testing_qty or 0)
            if row.actual_sale_qty and row.rate_per_liter:
                row.amount = flt(row.actual_sale_qty) * flt(row.rate_per_liter)
            total += flt(row.amount)
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
                fuel_summary[row.fuel_item]['qty'] += flt(row.actual_sale_qty)
                fuel_summary[row.fuel_item]['amount'] += flt(row.amount)
        
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
                tank_summary[row.tank]['consumption'] += flt(row.actual_sale_qty)
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
                row.amount = flt(row.quantity) * flt(row.rate)
            total += flt(row.amount)
        self.total_other_sales = total
    
    def calculate_credit_sales(self):
        """Calculate total credit fuel (amount-based)"""
        total = 0
        for row in self.credit_fuel_sales:
            if row.amount and row.rate_per_liter:
                row.quantity_liters = flt(row.amount) / flt(row.rate_per_liter)
            total += flt(row.amount)
        self.total_credit_fuel = total
    
    def calculate_driver_cash(self):
        """Calculate total driver cash"""
        total = 0
        for row in self.driver_cash_advances:
            total += flt(row.cash_amount)
        self.total_driver_cash = total
    
    def calculate_online_payments(self):
        """Calculate total online"""
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
        """Calculate grand total"""
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
        
        received = flt(self.cash_received)
        expected = flt(self.expected_cash)
        self.cash_variance = received - expected
    
    def calculate_cash_handover(self):
        """Calculate cash to next shift"""
        # Cash to next shift = Cash Received - Balances kept
        total_received = flt(self.cash_received)
        incharge_balance = flt(self.balance_with_shift_incharge)
        cashier_balance = flt(self.balance_with_pump_cashier)
        
        self.cash_given_to_next_shift = total_received - incharge_balance - cashier_balance
    
    def validate_tank_stock_sufficiency(self):
        """Validate that tank has sufficient stock for sales"""
        for row in self.tank_consumption:
            if not row.tank or not row.total_consumption:
                continue
            
            tank_doc = frappe.get_doc("Fuel Tank Master", row.tank)
            current_stock_kl = flt(tank_doc.current_stock_level or 0)
            consumption_kl = flt(row.total_consumption) / 1000
            
            if consumption_kl > current_stock_kl:
                frappe.throw(_(f"Insufficient stock in Tank {row.tank}. Available: {current_stock_kl} KL, Required: {consumption_kl} KL"))
    
    def validate_credit_limits(self):
        """Validate customer credit limits for credit sales"""
        from petrodiesel.utils import get_customer_total_outstanding
        
        for row in self.credit_fuel_sales:
            if not row.customer or not row.amount:
                continue
            
            # Get customer credit limit
            credit_limit = frappe.db.get_value('Customer', row.customer, 'credit_limit')
            if not credit_limit:
                continue
            
            # Get current outstanding
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
        
        # Get variance threshold from settings (default 500)
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
        for row in self.nozzle_readings:
            if row.nozzle and row.closing_reading:
                nozzle_doc = frappe.get_doc("Fuel Nozzle Master", row.nozzle)
                nozzle_doc.current_reading = flt(row.closing_reading)
                nozzle_doc.last_updated_on = self.posting_date
                nozzle_doc.last_shift = self.shift
                nozzle_doc.flags.ignore_permissions = True
                nozzle_doc.save()
                
        frappe.msgprint(_("Nozzle readings updated successfully"), alert=True)
    
    def reverse_nozzle_readings(self):
        """Restore opening readings on cancel"""
        for row in self.nozzle_readings:
            if row.nozzle and row.opening_reading:
                nozzle_doc = frappe.get_doc("Fuel Nozzle Master", row.nozzle)
                nozzle_doc.current_reading = flt(row.opening_reading)
                nozzle_doc.flags.ignore_permissions = True
                nozzle_doc.save()
    
    def update_tank_stock_levels(self):
        """Decrease tank stock based on consumption"""
        for row in self.tank_consumption:
            if row.tank and row.total_consumption:
                tank_doc = frappe.get_doc("Fuel Tank Master", row.tank)
                
                # Convert liters to KL if needed
                consumption_kl = flt(row.total_consumption) / 1000
                
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
        for row in self.tank_consumption:
            if row.tank and row.total_consumption:
                tank_doc = frappe.get_doc("Fuel Tank Master", row.tank)
                
                consumption_kl = flt(row.total_consumption) / 1000
                current_stock_kl = flt(tank_doc.current_stock_level or 0)
                new_stock_kl = current_stock_kl + consumption_kl
                
                tank_doc.current_stock_level = new_stock_kl
                tank_doc.flags.ignore_permissions = True
                tank_doc.save()
    
    def create_credit_sale_documents(self):
        """Create individual Credit Sale documents for each credit transaction"""
        if not self.credit_fuel_sales:
            return
        
        created_count = 0
        
        for row in self.credit_fuel_sales:
            if not row.customer or flt(row.amount) <= 0:
                continue
            
            try:
                # Create Credit Sale document
                credit_doc = frappe.get_doc({
                    "doctype": "Credit Sale",
                    "naming_series": "CS-.YYYY.-",
                    "posting_date": self.posting_date,
                    "posting_time": nowtime(),
                    "shift": self.shift,
                    "customer": row.customer,
                    "reference_type": "Shift Sale Entry",
                    "reference_name": self.name,
                    "payment_status": "Unpaid",
                    "items": [{
                        "nozzle": row.nozzle or "",
                        "fuel_item": row.fuel_item or "",
                        "item_code": row.fuel_item or "",
                        "vehicle_number": row.vehicle_number or "",
                        "slip_number": row.slip_number or "",
                        "quantity_liters": flt(row.quantity_liters),
                        "rate_per_liter": flt(row.rate_per_liter),
                        "amount": flt(row.amount)
                    }]
                })
                
                credit_doc.flags.ignore_permissions = True
                credit_doc.flags.ignore_mandatory = True
                credit_doc.insert()
                credit_doc.submit()
                
                # Store reference back to row
                frappe.db.set_value("Shift Credit Sale", row.name, "credit_sale_ref", credit_doc.name)
                
                created_count += 1
                
            except Exception as e:
                frappe.log_error(
                    title=f"Failed to create Credit Sale for {row.customer}",
                    message=f"Shift: {self.name}\nCustomer: {row.customer}\nError: {str(e)}"
                )
                frappe.msgprint(
                    _(f"Warning: Failed to create Credit Sale for {row.customer}. Check Error Log."),
                    alert=True,
                    indicator='orange'
                )
        
        if created_count > 0:
            frappe.msgprint(_(f"{created_count} Credit Sale document(s) created successfully"), 
                          alert=True, indicator='green')
            
            # Update customer balances
            self.update_customer_balances()
    
    def cancel_credit_sale_documents(self):
        """Cancel linked Credit Sale documents"""
        credit_sales = frappe.get_all("Credit Sale",
            filters={
                "reference_type": "Shift Sale Entry",
                "reference_name": self.name,
                "docstatus": 1
            }
        )
        
        cancelled_count = 0
        for cs in credit_sales:
            try:
                cs_doc = frappe.get_doc("Credit Sale", cs.name)
                cs_doc.flags.ignore_permissions = True
                cs_doc.cancel()
                cancelled_count += 1
            except Exception as e:
                frappe.log_error(f"Failed to cancel Credit Sale {cs.name}: {str(e)}")
        
        if cancelled_count > 0:
            frappe.msgprint(_(f"{cancelled_count} Credit Sale(s) cancelled"), alert=True)
    
    def update_customer_balances(self):
        """Update customer outstanding balances after creating credit sales"""
        from petrodiesel.utils import update_customer_balance
        
        customers = set()
        for row in self.credit_fuel_sales:
            if row.customer:
                customers.add(row.customer)
        
        for customer in customers:
            try:
                update_customer_balance(customer)
            except:
                pass


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
    return resolve_fuel_price(fuel_item, posting_date)


@frappe.whitelist()
def get_item_details(item_code):
    """Get item details with price"""
    if not item_code:
        return {}
    
    item = frappe.db.get_value('Item', item_code, ['item_name', 'item_group'], as_dict=1)
    if not item:
        return {}
    
    price = get_item_price(item_code)
    
    return {
        'item_name': item.item_name,
        'standard_rate': price
    }
