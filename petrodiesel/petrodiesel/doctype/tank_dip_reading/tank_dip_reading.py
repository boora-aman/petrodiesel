# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, nowtime

class TankDipReading(Document):
    def validate(self):
        self.calculate_totals()
        self.calculate_variance()
    
    def on_submit(self):
        self.update_tank_stock_levels()
        self.create_variance_stock_entry()
    
    def on_cancel(self):
        self.cancel_variance_stock_entry()
    
    def calculate_totals(self):
        """Calculate total stock as per dip readings"""
        total_dip = 0
        total_system = 0
        
        for row in self.tank_dip_details:
            # Get current dip reading in KL
            if row.current_dip_reading:
                total_dip += flt(row.current_dip_reading)
            
            # Get system stock (from Stock Ledger)
            if row.tank:
                tank_doc = frappe.get_doc('Fuel Tank Master', row.tank)
                system_stock = get_tank_system_stock(row.tank, tank_doc.fuel_item)
                row.system_stock = system_stock
                total_system += flt(system_stock)
            
            # Calculate variance for this tank
            row.variance = flt(row.current_dip_reading) - flt(row.system_stock)
            
            if row.system_stock:
                row.variance_percentage = (row.variance / row.system_stock) * 100
        
        self.total_stock_as_per_dip = total_dip
        self.total_stock_as_per_system = total_system
    
    def calculate_variance(self):
        """Calculate overall variance"""
        self.variance = flt(self.total_stock_as_per_dip) - flt(self.total_stock_as_per_system)
        
        if self.total_stock_as_per_system:
            self.variance_percentage = (self.variance / self.total_stock_as_per_system) * 100
    
    def update_tank_stock_levels(self):
        """Update actual dip reading in Fuel Tank Master"""
        for row in self.tank_dip_details:
            if row.tank and row.current_dip_reading:
                frappe.db.set_value('Fuel Tank Master', row.tank, {
                    'current_stock_level': row.current_dip_reading,
                    'last_dip_reading_date': self.posting_date,
                    'last_dip_reading_time': self.posting_time
                })
    
    def create_variance_stock_entry(self):
        """Create Stock Entry if variance exists (reconciliation)"""
        if abs(self.variance) < 0.01:  # Less than 10 liters
            return
        
        # Only create if reason is provided
        if not self.reason_for_variance:
            frappe.throw("Please provide Reason for Variance before submitting")
        
        items = []
        for row in self.tank_dip_details:
            if abs(row.variance) < 0.01:
                continue
            
            tank_doc = frappe.get_doc('Fuel Tank Master', row.tank)
            
            # Variance in Liters (KL × 1000)
            variance_qty = flt(row.variance) * 1000
            
            items.append({
                'item_code': tank_doc.fuel_item,
                's_warehouse': tank_doc.warehouse if variance_qty < 0 else None,
                't_warehouse': tank_doc.warehouse if variance_qty > 0 else None,
                'qty': abs(variance_qty),
                'basic_rate': 0,  # No valuation impact
                'uom': 'Litre',
                'stock_uom': 'Litre',
                'conversion_factor': 1
            })
        
        if items:
            stock_entry = frappe.get_doc({
                'doctype': 'Stock Entry',
                'stock_entry_type': 'Stock Reconciliation',
                'posting_date': self.posting_date,
                'posting_time': self.posting_time,
                'company': frappe.defaults.get_user_default('Company'),
                'reference_doctype': 'Tank Dip Reading',
                'reference_name': self.name,
                'remarks': f'Stock reconciliation for Tank Dip Reading {self.name}. Reason: {self.reason_for_variance}',
                'items': items
            })
            
            stock_entry.insert(ignore_permissions=True)
            stock_entry.submit()
            
            self.db_set('stock_entry', stock_entry.name)
            
            frappe.msgprint(f'Stock Entry {stock_entry.name} created for variance reconciliation')
    
    def cancel_variance_stock_entry(self):
        """Cancel associated Stock Entry"""
        if self.stock_entry:
            se = frappe.get_doc('Stock Entry', self.stock_entry)
            if se.docstatus == 1:
                se.cancel()
            self.db_set('stock_entry', None)


def get_tank_system_stock(tank, fuel_item):
    """Get current system stock from Stock Ledger Entry in KL"""
    tank_doc = frappe.get_doc('Fuel Tank Master', tank)
    
    stock_qty = frappe.db.sql("""
        SELECT SUM(actual_qty)
        FROM `tabStock Ledger Entry`
        WHERE item_code = %s
        AND warehouse = %s
        AND docstatus < 2
    """, (fuel_item, tank_doc.warehouse))
    
    qty_in_liters = flt(stock_qty[0][0]) if stock_qty else 0
    
    # Convert Liters to KL
    return qty_in_liters / 1000


@frappe.whitelist()
def get_tank_current_dip(tank):
    """API: Get current dip reading for a tank"""
    if not tank:
        return 0
    
    tank_doc = frappe.get_doc('Fuel Tank Master', tank)
    return tank_doc.current_stock_level or 0
