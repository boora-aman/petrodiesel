# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowtime
from frappe import _

class InternalStockTransfer(Document):
    def validate(self):
        self.validate_warehouses()
        self.validate_stock_availability()
        self.calculate_totals()
        self.check_fuel_items()
    
    def on_submit(self):
        self.create_stock_entry()
        self.update_tank_levels_if_fuel()
    
    def on_cancel(self):
        self.cancel_stock_entry()
        self.reverse_tank_levels_if_fuel()
    
    def validate_warehouses(self):
        """Validate from and to warehouses are different"""
        if self.from_warehouse == self.to_warehouse:
            frappe.throw(_("From Warehouse and To Warehouse cannot be same"))
    
    def validate_stock_availability(self):
        """Check if sufficient stock is available in source warehouse"""
        for row in self.items:
            available = get_warehouse_stock(row.item_code, self.from_warehouse)
            row.available_qty = available
            
            if flt(row.quantity) > flt(available):
                frappe.throw(_(f"Insufficient stock for {row.item_code}. Available: {available}, Requested: {row.quantity}"))
    
    def calculate_totals(self):
        """Calculate total quantity"""
        total_qty = 0
        
        for row in self.items:
            total_qty += flt(row.quantity)
        
        self.total_qty = total_qty
    
    def check_fuel_items(self):
        """Check if any item is fuel"""
        for row in self.items:
            item_group = frappe.db.get_value("Item", row.item_code, "item_group")
            if item_group == "Fuels":
                row.is_fuel = 1
            else:
                row.is_fuel = 0
    
    def update_tank_levels_if_fuel(self):
        """Update tank levels for fuel transfers"""
        for row in self.items:
            if row.is_fuel:
                qty_kl = flt(row.quantity) / 1000
                
                # Decrease source tank
                source_tanks = frappe.get_all("Fuel Tank Master",
                    filters={
                        "fuel_item": row.item_code,
                        "warehouse": self.from_warehouse,
                        "status": "Active"
                    },
                    limit=1
                )
                
                if source_tanks:
                    source_tank = frappe.get_doc("Fuel Tank Master", source_tanks[0].name)
                    current_stock = flt(source_tank.current_stock_level or 0)
                    source_tank.current_stock_level = current_stock - qty_kl
                    source_tank.last_updated_on = self.posting_date
                    source_tank.flags.ignore_permissions = True
                    source_tank.save()
                
                # Increase target tank
                target_tanks = frappe.get_all("Fuel Tank Master",
                    filters={
                        "fuel_item": row.item_code,
                        "warehouse": self.to_warehouse,
                        "status": "Active"
                    },
                    limit=1
                )
                
                if target_tanks:
                    target_tank = frappe.get_doc("Fuel Tank Master", target_tanks[0].name)
                    current_stock = flt(target_tank.current_stock_level or 0)
                    target_tank.current_stock_level = current_stock + qty_kl
                    target_tank.last_updated_on = self.posting_date
                    target_tank.flags.ignore_permissions = True
                    target_tank.save()
    
    def reverse_tank_levels_if_fuel(self):
        """Reverse tank level changes on cancel"""
        for row in self.items:
            if row.is_fuel:
                qty_kl = flt(row.quantity) / 1000
                
                # Reverse source tank (add back)
                source_tanks = frappe.get_all("Fuel Tank Master",
                    filters={
                        "fuel_item": row.item_code,
                        "warehouse": self.from_warehouse
                    },
                    limit=1
                )
                
                if source_tanks:
                    source_tank = frappe.get_doc("Fuel Tank Master", source_tanks[0].name)
                    current_stock = flt(source_tank.current_stock_level or 0)
                    source_tank.current_stock_level = current_stock + qty_kl
                    source_tank.flags.ignore_permissions = True
                    source_tank.save()
                
                # Reverse target tank (subtract)
                target_tanks = frappe.get_all("Fuel Tank Master",
                    filters={
                        "fuel_item": row.item_code,
                        "warehouse": self.to_warehouse
                    },
                    limit=1
                )
                
                if target_tanks:
                    target_tank = frappe.get_doc("Fuel Tank Master", target_tanks[0].name)
                    current_stock = flt(target_tank.current_stock_level or 0)
                    target_tank.current_stock_level = current_stock - qty_kl
                    target_tank.flags.ignore_permissions = True
                    target_tank.save()
    
    def create_stock_entry(self):
        """Create Stock Entry for material transfer"""
        items = []
        
        for row in self.items:
            items.append({
                'item_code': row.item_code,
                's_warehouse': self.from_warehouse,
                't_warehouse': self.to_warehouse,
                'qty': row.quantity,
                'uom': row.uom,
                'stock_uom': row.uom,
                'conversion_factor': 1
            })
        
        stock_entry = frappe.get_doc({
            'doctype': 'Stock Entry',
            'stock_entry_type': 'Material Transfer',
            'posting_date': self.posting_date,
            'posting_time': self.posting_time or nowtime(),
            'company': frappe.defaults.get_user_default('Company'),
            'remarks': f'{self.transfer_type}: {self.from_warehouse} → {self.to_warehouse}',
            'items': items
        })
        
        stock_entry.flags.ignore_permissions = True
        stock_entry.insert()
        stock_entry.submit()
        
        self.db_set('stock_entry', stock_entry.name)
        frappe.msgprint(f'Stock Entry {stock_entry.name} created successfully', alert=True, indicator='green')
    
    def cancel_stock_entry(self):
        """Cancel Stock Entry"""
        if self.stock_entry:
            try:
                se = frappe.get_doc('Stock Entry', self.stock_entry)
                if se.docstatus == 1:
                    se.flags.ignore_permissions = True
                    se.cancel()
                self.db_set('stock_entry', None)
            except Exception as e:
                frappe.log_error(f'Failed to cancel Stock Entry: {str(e)}')


def get_warehouse_stock(item_code, warehouse):
    """Get available stock quantity for item in warehouse"""
    stock_qty = frappe.db.sql("""
        SELECT SUM(actual_qty)
        FROM `tabStock Ledger Entry`
        WHERE item_code = %s
        AND warehouse = %s
        AND docstatus < 2
    """, (item_code, warehouse))
    
    return flt(stock_qty[0][0]) if stock_qty else 0


@frappe.whitelist()
def get_item_stock_in_warehouse(item_code, warehouse):
    """API: Get stock for item in warehouse"""
    if not item_code or not warehouse:
        return 0
    
    return get_warehouse_stock(item_code, warehouse)


@frappe.whitelist()
def get_warehouse_items(warehouse):
    """Get all items with stock in a warehouse"""
    items = frappe.db.sql("""
        SELECT 
            sle.item_code,
            item.item_name,
            SUM(sle.actual_qty) as qty,
            item.stock_uom
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabItem` item ON item.name = sle.item_code
        WHERE sle.warehouse = %s
        AND sle.docstatus < 2
        GROUP BY sle.item_code
        HAVING qty > 0
        ORDER BY item.item_name
    """, warehouse, as_dict=1)
    
    return items
