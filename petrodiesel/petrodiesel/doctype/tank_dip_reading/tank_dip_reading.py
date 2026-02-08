# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, nowtime


class TankDipReading(Document):
    def validate(self):
        self.calculate_tank_details()
        self.calculate_totals()
        self.calculate_variance()
    
    def on_submit(self):
        self.update_tank_stock_levels()
        self.create_variance_stock_entry()
    
    def on_cancel(self):
        self.cancel_variance_stock_entry()
        self.reverse_tank_updates()
    
    def calculate_tank_details(self):
        """Calculate quantity from dip height using calibration chart"""
        for row in self.tank_dip_details:
            if row.tank and row.dip_height_mm:
                # Get tank master
                tank_doc = frappe.get_doc("Fuel Tank Master", row.tank)
                
                # Calculate quantity from calibration chart
                calculated_qty = self.get_quantity_from_dip(tank_doc, row.dip_height_mm)
                
                # Convert liters to KL
                row.calculated_quantity_liters = calculated_qty
                row.calculated_quantity_kl = calculated_qty / 1000
                
                # Get system stock from Stock Ledger
                system_stock_liters = get_tank_system_stock_liters(row.tank, tank_doc.fuel_item)
                row.system_stock_liters = system_stock_liters
                row.system_stock_kl = system_stock_liters / 1000
                
                # Calculate variance
                row.variance_liters = calculated_qty - system_stock_liters
                row.variance_kl = row.variance_liters / 1000
                
                if system_stock_liters:
                    row.variance_percentage = (row.variance_liters / system_stock_liters) * 100
                
                # Check if there's a recent tanker receipt for this tank
                if hasattr(tank_doc, 'last_receipt_ref') and tank_doc.last_receipt_ref:
                    receipt_doc = frappe.get_doc('Tanker Receipt', tank_doc.last_receipt_ref)
                    if receipt_doc.posting_date == self.posting_date:
                        # Same day receipt - check if dip matches receipt dip
                        receipt_dip_after = flt(tank_doc.last_receipt_dip_after)
                        current_dip_kl = row.calculated_quantity_kl
                        
                        if abs(current_dip_kl - receipt_dip_after) > 0.05:
                            frappe.msgprint(
                                _(f"Tank {row.tank}: Dip reading variance with tanker receipt. "
                                  f"Receipt dip: {receipt_dip_after * 1000:.2f}L, Current dip: {current_dip_kl * 1000:.2f}L"),
                                alert=True,
                                indicator='orange'
                            )
    
    def get_quantity_from_dip(self, tank_doc, dip_height_mm):
        """Get quantity from calibration chart"""
        if not tank_doc.calibration_data:
            # No calibration, use simple proportional calculation
            # Assume linear relationship between dip height and volume
            max_dip = flt(tank_doc.diameter_mm or 2000)  # Use diameter as max dip height
            if max_dip == 0:
                max_dip = 2000
            return (dip_height_mm / max_dip) * flt(tank_doc.capacity_in_liters or 0)
        
        # Use calibration chart (linear interpolation)
        calibration = sorted(tank_doc.calibration_data, key=lambda x: x.dip_height_mm)
        
        # Find closest calibration points
        for i, cal in enumerate(calibration):
            if dip_height_mm <= cal.dip_height_mm:
                if i == 0:
                    return cal.quantity_liters
                
                # Linear interpolation
                cal_lower = calibration[i-1]
                cal_upper = cal
                
                dip_diff = cal_upper.dip_height_mm - cal_lower.dip_height_mm
                qty_diff = cal_upper.quantity_liters - cal_lower.quantity_liters
                
                ratio = (dip_height_mm - cal_lower.dip_height_mm) / dip_diff
                return cal_lower.quantity_liters + (ratio * qty_diff)
        
        # If dip higher than all calibration points, use last value
        return calibration[-1].quantity_liters if calibration else 0
    
    def calculate_totals(self):
        """Calculate total stock as per dip readings"""
        total_dip_kl = 0
        total_system_kl = 0
        
        for row in self.tank_dip_details:
            total_dip_kl += flt(row.calculated_quantity_kl)
            total_system_kl += flt(row.system_stock_kl)
        
        self.total_stock_as_per_dip = total_dip_kl
        self.total_stock_as_per_system = total_system_kl
    
    def calculate_variance(self):
        """Calculate overall variance"""
        self.variance = flt(self.total_stock_as_per_dip) - flt(self.total_stock_as_per_system)
        
        if self.total_stock_as_per_system:
            self.variance_percentage = (self.variance / self.total_stock_as_per_system) * 100
    
    def update_tank_stock_levels(self):
        """Update actual dip reading in Fuel Tank Master"""
        for row in self.tank_dip_details:
            if row.tank and row.calculated_quantity_kl:
                tank_doc = frappe.get_doc("Fuel Tank Master", row.tank)
                tank_doc.current_stock_level = flt(row.calculated_quantity_kl)
                tank_doc.last_dip_reading_date = self.posting_date
                tank_doc.last_dip_reading_time = self.posting_time
                tank_doc.last_dip_height_mm = row.dip_height_mm
                tank_doc.flags.ignore_permissions = True
                tank_doc.save()
        
        frappe.msgprint(_("Tank dip readings updated"), alert=True)
    
    def reverse_tank_updates(self):
        """Reverse tank updates on cancel"""
        # Note: We don't reverse the dip reading as it's historical data
        pass
    
    def create_variance_stock_entry(self):
        """Create Stock Entry if variance exists (reconciliation)"""
        if abs(self.variance * 1000) < 10:  # Less than 10 liters
            return
        
        # Only create if reason is provided
        if not self.reason_for_variance:
            frappe.msgprint(_("Please provide Reason for Variance"), alert=True)
            return
        
        items = []
        for row in self.tank_dip_details:
            if abs(row.variance_liters) < 1:
                continue
            
            tank_doc = frappe.get_doc('Fuel Tank Master', row.tank)
            variance_qty = flt(row.variance_liters)
            
            items.append({
                'item_code': tank_doc.fuel_item,
                's_warehouse': tank_doc.warehouse if variance_qty < 0 else None,
                't_warehouse': tank_doc.warehouse if variance_qty > 0 else None,
                'qty': abs(variance_qty),
                'basic_rate': 0,
                'uom': 'Litre',
                'stock_uom': 'Litre',
                'conversion_factor': 1
            })
        
        if items:
            try:
                stock_entry = frappe.get_doc({
                    'doctype': 'Stock Entry',
                    'stock_entry_type': 'Stock Reconciliation',
                    'posting_date': self.posting_date,
                    'posting_time': self.posting_time,
                    'company': frappe.defaults.get_user_default('Company'),
                    'remarks': f'Stock reconciliation for Tank Dip Reading {self.name}. Reason: {self.reason_for_variance}',
                    'items': items
                })
                
                stock_entry.flags.ignore_permissions = True
                stock_entry.insert()
                stock_entry.submit()
                
                self.db_set('stock_entry', stock_entry.name)
                frappe.msgprint(f'Stock Entry {stock_entry.name} created for variance reconciliation')
            except Exception as e:
                frappe.log_error(f"Failed to create Stock Entry: {str(e)}")
    
    def cancel_variance_stock_entry(self):
        """Cancel associated Stock Entry"""
        if self.stock_entry:
            try:
                se = frappe.get_doc('Stock Entry', self.stock_entry)
                if se.docstatus == 1:
                    se.flags.ignore_permissions = True
                    se.cancel()
            except Exception as e:
                frappe.log_error(f"Failed to cancel Stock Entry: {str(e)}")


def get_tank_system_stock_liters(tank, fuel_item):
    """Get current system stock from Stock Ledger Entry in Liters"""
    tank_doc = frappe.get_doc('Fuel Tank Master', tank)
    
    stock_qty = frappe.db.sql("""
        SELECT SUM(actual_qty)
        FROM `tabStock Ledger Entry`
        WHERE item_code = %s
        AND warehouse = %s
        AND docstatus < 2
    """, (fuel_item, tank_doc.warehouse))
    
    return flt(stock_qty[0][0]) if stock_qty else 0


@frappe.whitelist()
def get_tank_current_dip(tank):
    """API: Get current dip reading for a tank"""
    if not tank:
        return 0
    
    tank_doc = frappe.get_doc('Fuel Tank Master', tank)
    return tank_doc.last_dip_height_mm or 0
