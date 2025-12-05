# Copyright (c) 2025,  Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class NozzleShiftReading(Document):
    def validate(self):
        """Validate before saving"""
        self.calculate_nozzle_totals()
        self.calculate_other_sales()
        self.calculate_payment_totals()
        self.calculate_employee_advances()
        self.calculate_expected_collection()
        self.calculate_variance()
        self.adjust_cash_variance_for_advances()
    
    def calculate_nozzle_totals(self):
        """Calculate totals from nozzle readings"""
        total_qty = 0
        total_amount = 0
        
        for row in self.nozzle_readings:
            # Calculate total sale quantity (closing - opening)
            if row.closing_reading and row.opening_reading:
                row.total_sale_qty = row.closing_reading - row.opening_reading
            
            # Calculate actual sale quantity (total - testing)
            row.actual_sale_qty = (row.total_sale_qty or 0) - (row.testing_qty or 0)
            
            # Calculate amount
            if row.actual_sale_qty and row.rate_per_liter:
                row.amount = row.actual_sale_qty * row.rate_per_liter
            
            # Add to totals
            total_qty += row.actual_sale_qty or 0
            total_amount += row.amount or 0
            
            # Update nozzle's current reading
            if row.closing_reading and row.nozzle:
                frappe.db.set_value("Fuel Nozzle Master", row.nozzle, "current_reading", row.closing_reading)
        
        self.total_fuel_sales_qty = total_qty
        self.total_fuel_sales_amount = total_amount
    
    def calculate_other_sales(self):
        """Calculate total sales including lubricants and accessories"""
        self.total_sales_amount = (
            (self.total_fuel_sales_amount or 0) + 
            (self.lubricant_sales_amount or 0) + 
            (self.accessories_sales_amount or 0)
        )
    
    def calculate_payment_totals(self):
        """Calculate total online payments"""
        total_online = 0
        
        for row in self.online_payment_details:
            total_online += row.amount or 0
        
        self.total_online_collection = total_online
    
    def calculate_employee_advances(self):
        """Calculate total employee advances"""
        total = 0
        for row in self.employee_advances:
            total += row.amount or 0
        
        self.total_employee_advances = total
    
    def calculate_expected_collection(self):
        """Calculate expected cash collection"""
        # Expected = Total Sales - Online - Credit
        self.expected_cash_collection = (
            (self.total_sales_amount or 0) - 
            (self.total_online_collection or 0) - 
            (self.credit_sales_amount or 0)
        )
    
    def calculate_variance(self):
        """Calculate cash shortage or excess"""
        expected = self.expected_cash_collection or 0
        received = self.cash_received or 0
        
        if received < expected:
            self.cash_shortage = expected - received
            self.cash_excess = 0
        else:
            self.cash_excess = received - expected
            self.cash_shortage = 0
    
    def adjust_cash_variance_for_advances(self):
        """
        Adjust cash variance to account for advances given.
        If cash was given to employees, actual cash in hand will be less.
        So we reduce expected cash by the advances given.
        """
        if self.total_employee_advances:
            # Adjusted expected = Original expected - Advances given
            adjusted_expected = (self.expected_cash_collection or 0) - (self.total_employee_advances or 0)
            
            # Recalculate variance based on adjusted expected
            received = self.cash_received or 0
            
            if received < adjusted_expected:
                self.cash_shortage = adjusted_expected - received
                self.cash_excess = 0
            else:
                self.cash_excess = received - adjusted_expected
                self.cash_shortage = 0
    
    def on_submit(self):
        """Actions on submit"""
        # Create stock entry for fuel sales
        # self.create_stock_entry()
        
        # Update nozzle current readings (already done in calculate_nozzle_totals)
        pass
    
    def on_cancel(self):
        """Actions on cancel"""
        # Cancel linked stock entry
        if self.stock_entry:
            stock_entry = frappe.get_doc("Stock Entry", self.stock_entry)
            if stock_entry.docstatus == 1:
                stock_entry.cancel()
                frappe.msgprint(_("Stock Entry {0} cancelled").format(self.stock_entry))
    
    def create_stock_entry(self):
        """Create stock entry for fuel consumption"""
        if self.stock_entry:
            return
        
        # Group by fuel item and tank
        fuel_items = {}
        
        for row in self.nozzle_readings:
            if row.actual_sale_qty and row.fuel_item and row.nozzle:
                # Get tank for this nozzle
                nozzle = frappe.get_doc("Fuel Nozzle Master", row.nozzle)
                tank = nozzle.tank
                
                if not tank:
                    continue
                
                # Get warehouse for this tank
                tank_doc = frappe.get_doc("Fuel Tank Master", tank)
                warehouse = tank_doc.warehouse
                
                if not warehouse:
                    continue
                
                # Group by fuel item + warehouse
                key = f"{row.fuel_item}|{warehouse}"
                
                if key not in fuel_items:
                    fuel_items[key] = {
                        "item": row.fuel_item,
                        "warehouse": warehouse,
                        "qty": 0
                    }
                
                fuel_items[key]["qty"] += row.actual_sale_qty
        
        # Create stock entry
        if fuel_items:
            stock_entry = frappe.get_doc({
                "doctype": "Stock Entry",
                "stock_entry_type": "Material Issue",
                "posting_date": self.posting_date,
                "posting_time": self.shift_end_time or "23:59:59",
                "items": []
            })
            
            for data in fuel_items.values():
                stock_entry.append("items", {
                    "item_code": data["item"],
                    "s_warehouse": data["warehouse"],
                    "qty": data["qty"],
                    "basic_rate": 0,  # Will be fetched from valuation
                    "uom": "Litre"
                })
            
            stock_entry.insert()
            stock_entry.submit()
            
            # Link to this document
            self.db_set("stock_entry", stock_entry.name)
            
            frappe.msgprint(_("Stock Entry {0} created").format(stock_entry.name))


# Whitelisted methods for API calls

@frappe.whitelist()
def get_nozzle_opening_reading(nozzle):
    """Get current reading of nozzle as opening reading"""
    if not nozzle:
        return 0
    
    current_reading = frappe.db.get_value("Fuel Nozzle Master", nozzle, "current_reading")
    return current_reading or 0


@frappe.whitelist()
def get_fuel_rate(fuel_item):
    """Get current selling rate for fuel item"""
    if not fuel_item:
        return 0
    
    # Try to get from Price List (if using ERPNext pricing)
    try:
        from erpnext.stock.get_item_details import get_price_list_rate
        rate = get_price_list_rate({
            "item_code": fuel_item,
            "price_list": "Standard Selling",
            "uom": "Litre"
        })
        if rate:
            return rate
    except:
        pass
    
    # Fallback: Get from Item master's standard rate
    rate = frappe.db.get_value("Item", fuel_item, "standard_rate")
    return rate or 0


@frappe.whitelist()
def get_shift_summary(shift_name):
    """Get summary for a specific shift reading"""
    if not shift_name:
        return {}
    
    doc = frappe.get_doc("Nozzle Shift Reading", shift_name)
    
    return {
        "posting_date": doc.posting_date,
        "shift": doc.shift,
        "cashier": doc.cashier,
        "total_fuel_sales_qty": doc.total_fuel_sales_qty,
        "total_fuel_sales_amount": doc.total_fuel_sales_amount,
        "total_sales_amount": doc.total_sales_amount,
        "cash_received": doc.cash_received,
        "total_online_collection": doc.total_online_collection,
        "credit_sales_amount": doc.credit_sales_amount,
        "total_employee_advances": doc.total_employee_advances,
        "expected_cash_collection": doc.expected_cash_collection,
        "cash_shortage": doc.cash_shortage,
        "cash_excess": doc.cash_excess,
        "nozzle_count": len(doc.nozzle_readings),
        "employee_advance_count": len(doc.employee_advances)
    }
