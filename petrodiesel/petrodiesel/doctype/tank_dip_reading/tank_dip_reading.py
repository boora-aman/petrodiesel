# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TankDipReading(Document):
    def validate(self):
        """Calculate stock variance"""
        self.calculate_variance()
    
    def calculate_variance(self):
        """Calculate variance between dip reading and system stock"""
        total_dip_stock = 0
        
        # Calculate total from dip readings
        for row in self.tank_dip_details:
            total_dip_stock += row.calculated_quantity_liters or 0
        
        self.total_stock_as_per_dip = total_dip_stock
        
        # Get system stock from Stock Ledger
        total_system_stock = 0
        
        for row in self.tank_dip_details:
            if row.tank and row.fuel_item:
                # Get tank details
                tank = frappe.get_doc("Fuel Tank Master", row.tank)
                
                # Get stock balance from warehouse
                stock_qty = frappe.db.get_value(
                    "Bin",
                    {
                        "item_code": row.fuel_item,
                        "warehouse": tank.warehouse
                    },
                    "actual_qty"
                ) or 0
                
                total_system_stock += stock_qty
        
        self.total_stock_as_per_system = total_system_stock
        
        # Calculate variance
        self.variance = total_dip_stock - total_system_stock
        
        # Calculate variance percentage
        if total_system_stock > 0:
            self.variance_percentage = (self.variance / total_system_stock) * 100
        else:
            self.variance_percentage = 0
        
        # Alert if variance is high
        if abs(self.variance_percentage) > 1:
            frappe.msgprint(
                f"Stock variance of {self.variance_percentage:.2f}% detected. Please investigate!",
                indicator='orange',
                alert=True
            )
