# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, nowtime
from frappe import _

class ProductPurchaseEntry(Document):
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
        """Check if any item is fuel and set flag"""
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
                # Find tank for this fuel item and warehouse
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
                    
                    # Convert quantity to KL (assuming quantity is in liters)
                    qty_kl = flt(row.quantity) / 1000
                    
                    # Increase tank level
                    current_stock_kl = flt(tank_doc.current_stock_level or 0)
                    new_stock_kl = current_stock_kl + qty_kl
                    
                    tank_doc.current_stock_level = new_stock_kl
                    tank_doc.last_updated_on = self.posting_date
                    tank_doc.last_receipt_date = self.posting_date
                    tank_doc.flags.ignore_permissions = True
                    tank_doc.save()
                    
                    frappe.msgprint(_(f"Tank {tank_doc.tank_name} updated: +{qty_kl} KL"), alert=True)
    
    def reverse_tank_levels_if_fuel(self):
        """Reverse tank stock levels for fuel items on cancel"""
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
            'posting_time': self.posting_time or nowtime(),
            'company': frappe.defaults.get_user_default('Company'),
            'remarks': f'Material Receipt from {self.supplier} - Bill No: {self.bill_no or "N/A"}',
            'items': items
        })
        
        stock_entry.flags.ignore_permissions = True
        stock_entry.insert()
        stock_entry.submit()
        
        self.db_set('stock_entry', stock_entry.name)
        frappe.msgprint(f'Stock Entry {stock_entry.name} created successfully', alert=True)
    
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
    
    def create_purchase_invoice_doc(self):
        """Create Purchase Invoice for accounting"""
        items = []
        
        for row in self.items:
            items.append({
                'item_code': row.item_code,
                'qty': row.quantity,
                'rate': row.rate,
                'amount': row.amount,
                'uom': row.uom,
                'warehouse': row.warehouse
            })
        
        pi = frappe.get_doc({
            'doctype': 'Purchase Invoice',
            'supplier': self.supplier,
            'posting_date': self.posting_date,
            'posting_time': self.posting_time or nowtime(),
            'company': frappe.defaults.get_user_default('Company'),
            'bill_no': self.bill_no,
            'bill_date': self.bill_date or self.posting_date,
            'items': items,
            'update_stock': 0
        })
        
        try:
            pi.flags.ignore_permissions = True
            pi.insert()
            pi.submit()
            
            self.db_set('purchase_invoice', pi.name)
            frappe.msgprint(f'Purchase Invoice {pi.name} created successfully', alert=True)
        except Exception as e:
            frappe.log_error(f'Failed to create Purchase Invoice: {str(e)}')
            frappe.msgprint(f'Stock Entry created but Purchase Invoice failed: {str(e)}', indicator='orange')
    
    def cancel_purchase_invoice_doc(self):
        """Cancel Purchase Invoice"""
        if self.purchase_invoice:
            try:
                pi = frappe.get_doc('Purchase Invoice', self.purchase_invoice)
                if pi.docstatus == 1:
                    pi.flags.ignore_permissions = True
                    pi.cancel()
                self.db_set('purchase_invoice', None)
            except Exception as e:
                frappe.log_error(f'Failed to cancel Purchase Invoice: {str(e)}')


@frappe.whitelist()
def get_item_details(item_code):
    """Get item details like UOM, last purchase rate"""
    if not item_code:
        return {}
    
    item = frappe.get_doc('Item', item_code)
    
    # Get last purchase rate
    last_rate = frappe.db.sql("""
        SELECT rate
        FROM `tabPurchase Invoice Item`
        WHERE item_code = %s
        AND docstatus = 1
        ORDER BY creation DESC
        LIMIT 1
    """, item_code)
    
    return {
        'uom': item.stock_uom,
        'last_rate': last_rate[0][0] if last_rate else (item.standard_rate or 0),
        'item_group': item.item_group,
        'is_fuel': item.item_group == 'Fuels'
    }
