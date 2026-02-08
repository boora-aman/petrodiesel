# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowtime
from frappe import _

class SimplePurchaseEntry(Document):
    def validate(self):
        self.calculate_totals()
        self.check_fuel_items()
    
    def on_submit(self):
        self.create_stock_entry()
        self.update_tank_levels_if_fuel()
        if self.create_purchase_invoice:
            self.create_purchase_invoice_doc()
    
    def on_cancel(self):
        self.cancel_stock_entry()
        self.reverse_tank_levels_if_fuel()
        self.cancel_purchase_invoice_doc()
    
    def calculate_totals(self):
        """Calculate total quantity and amount"""
        total_qty = 0
        total_amount = 0
        
        for row in self.items:
            row.amount = flt(row.quantity) * flt(row.rate)
            total_qty += flt(row.quantity)
            total_amount += flt(row.amount)
        
        self.total_qty = total_qty
        self.total_amount = total_amount
    
    def check_fuel_items(self):
        """Check if any item is fuel"""
        for row in self.items:
            item_group = frappe.db.get_value("Item", row.item_code, "item_group")
            if item_group == "Fuels":
                row.is_fuel = 1
            else:
                row.is_fuel = 0
    
    def update_tank_levels_if_fuel(self):
        """Update tank stock levels for fuel items"""
        for row in self.items:
            if row.is_fuel:
                tanks = frappe.get_all("Fuel Tank Master",
                    filters={
                        "fuel_item": row.item_code,
                        "warehouse": row.warehouse,
                        "status": "Active"
                    },
                    limit=1
                )
                
                if tanks:
                    tank_doc = frappe.get_doc("Fuel Tank Master", tanks[0].name)
                    qty_kl = flt(row.quantity) / 1000
                    current_stock_kl = flt(tank_doc.current_stock_level or 0)
                    new_stock_kl = current_stock_kl + qty_kl
                    
                    tank_doc.current_stock_level = new_stock_kl
                    tank_doc.last_updated_on = self.posting_date
                    tank_doc.last_receipt_date = self.posting_date
                    tank_doc.flags.ignore_permissions = True
                    tank_doc.save()
    
    def reverse_tank_levels_if_fuel(self):
        """Reverse tank stock levels on cancel"""
        for row in self.items:
            if row.is_fuel:
                tanks = frappe.get_all("Fuel Tank Master",
                    filters={
                        "fuel_item": row.item_code,
                        "warehouse": row.warehouse
                    },
                    limit=1
                )
                
                if tanks:
                    tank_doc = frappe.get_doc("Fuel Tank Master", tanks[0].name)
                    qty_kl = flt(row.quantity) / 1000
                    current_stock_kl = flt(tank_doc.current_stock_level or 0)
                    new_stock_kl = current_stock_kl - qty_kl
                    
                    tank_doc.current_stock_level = new_stock_kl
                    tank_doc.flags.ignore_permissions = True
                    tank_doc.save()
    
    def create_stock_entry(self):
        """Create Stock Entry for material receipt"""
        items = []
        
        for row in self.items:
            items.append({
                'item_code': row.item_code,
                't_warehouse': row.warehouse,
                'qty': row.quantity,
                'basic_rate': row.rate,
                'uom': row.uom,
                'stock_uom': row.uom,
                'conversion_factor': 1
            })
        
        stock_entry = frappe.get_doc({
            'doctype': 'Stock Entry',
            'stock_entry_type': 'Material Receipt',
            'posting_date': self.posting_date,
            'company': frappe.defaults.get_user_default('Company'),
            'remarks': f'Simple Purchase from {self.supplier}',
            'items': items
        })
        
        stock_entry.flags.ignore_permissions = True
        stock_entry.insert()
        stock_entry.submit()
        
        self.db_set('stock_entry', stock_entry.name)
        frappe.msgprint(f'Stock Entry {stock_entry.name} created', alert=True)
    
    def cancel_stock_entry(self):
        """Cancel Stock Entry"""
        if self.stock_entry:
            try:
                se = frappe.get_doc('Stock Entry', self.stock_entry)
                if se.docstatus == 1:
                    se.flags.ignore_permissions = True
                    se.cancel()
            except Exception as e:
                frappe.log_error(f'Failed to cancel Stock Entry: {str(e)}')
    
    def create_purchase_invoice_doc(self):
        """Create Purchase Invoice"""
        items = []
        
        for row in self.items:
            items.append({
                'item_code': row.item_code,
                'qty': row.quantity,
                'rate': row.rate,
                'uom': row.uom,
                'warehouse': row.warehouse
            })
        
        pi = frappe.get_doc({
            'doctype': 'Purchase Invoice',
            'supplier': self.supplier,
            'posting_date': self.posting_date,
            'company': frappe.defaults.get_user_default('Company'),
            'items': items,
            'update_stock': 0
        })
        
        try:
            pi.flags.ignore_permissions = True
            pi.insert()
            pi.submit()
            self.db_set('purchase_invoice', pi.name)
            frappe.msgprint(f'Purchase Invoice {pi.name} created', alert=True)
        except Exception as e:
            frappe.log_error(f'Failed to create Purchase Invoice: {str(e)}')
    
    def cancel_purchase_invoice_doc(self):
        """Cancel Purchase Invoice"""
        if self.purchase_invoice:
            try:
                pi = frappe.get_doc('Purchase Invoice', self.purchase_invoice)
                if pi.docstatus == 1:
                    pi.flags.ignore_permissions = True
                    pi.cancel()
            except Exception as e:
                frappe.log_error(f'Failed to cancel Purchase Invoice: {str(e)}')
