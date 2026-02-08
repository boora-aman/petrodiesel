# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt


class FuelTankMaster(Document):
    def validate(self):
        self.validate_duplicate_tank()
        self.validate_capacity()
        self.check_stock_level()
    
    def validate_duplicate_tank(self):
        """Ensure no duplicate tank ID"""
        duplicate = frappe.db.exists("Fuel Tank Master", {
            "tank_id": self.tank_id,
            "name": ["!=", self.name]
        })
        
        if duplicate:
            frappe.throw(_(f"Tank ID {self.tank_id} already exists"))
    
    def validate_capacity(self):
        """Validate current stock doesn't exceed capacity"""
        if self.current_stock_level and self.capacity_in_liters:
            capacity_kl = flt(self.capacity_in_liters) / 1000
            
            if flt(self.current_stock_level) > capacity_kl:
                frappe.throw(_(f"Current stock level {self.current_stock_level} KL exceeds tank capacity {capacity_kl} KL"))
    
    def check_stock_level(self):
        """Check if stock is low and warn"""
        if self.current_stock_level and self.capacity_in_liters:
            capacity_kl = flt(self.capacity_in_liters) / 1000
            current_percentage = (flt(self.current_stock_level) / capacity_kl) * 100
            
            if current_percentage < 20:
                frappe.msgprint(_(f"Warning: Tank {self.tank_name} stock is low ({current_percentage:.1f}%)"), 
                              indicator='orange', alert=True)


@frappe.whitelist()
def get_tank_status(tank):
    """Get current status of tank"""
    if not tank:
        return {}
    
    tank_doc = frappe.get_doc("Fuel Tank Master", tank)
    
    capacity_kl = flt(tank_doc.capacity_in_liters) / 1000 if tank_doc.capacity_in_liters else 0
    current_percentage = (flt(tank_doc.current_stock_level) / capacity_kl * 100) if capacity_kl else 0
    
    return {
        "current_stock_level": tank_doc.current_stock_level,
        "capacity_kl": capacity_kl,
        "fill_percentage": current_percentage,
        "status": tank_doc.status,
        "fuel_item": tank_doc.fuel_item,
        "last_updated_on": tank_doc.last_updated_on,
        "last_receipt_date": tank_doc.last_receipt_date
    }


@frappe.whitelist()
def get_tank_stock_ledger(tank, limit=50):
    """Get stock movement history for tank"""
    if not tank:
        return []
    
    tank_doc = frappe.get_doc("Fuel Tank Master", tank)
    
    ledger = frappe.db.sql("""
        SELECT 
            posting_date, posting_time, voucher_type, voucher_no,
            actual_qty, qty_after_transaction, stock_uom
        FROM `tabStock Ledger Entry`
        WHERE warehouse = %s
        AND item_code = %s
        AND docstatus < 2
        ORDER BY posting_date DESC, posting_time DESC
        LIMIT %s
    """, (tank_doc.warehouse, tank_doc.fuel_item, limit), as_dict=1)
    
    return ledger
