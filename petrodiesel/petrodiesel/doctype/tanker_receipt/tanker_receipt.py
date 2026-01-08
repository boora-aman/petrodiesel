# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt

class TankerReceipt(Document):
    def validate(self):
        """Validate and calculate totals"""
        self.calculate_items()
        self.calculate_totals()
    
    def calculate_items(self):
        """Calculate received qty and shortage/excess for each item"""
        for row in self.items:
            # Calculate received quantity from dip readings (in KL)
            if row.dip_after_unloading and row.dip_before_unloading:
                row.calculated_received_qty = row.dip_after_unloading - row.dip_before_unloading
            
            # Calculate shortage or excess (KL)
            if row.invoiced_quantity and row.calculated_received_qty:
                row.shortage_excess = row.calculated_received_qty - row.invoiced_quantity
            
            # Calculate amount (based on invoiced quantity)
            if row.invoiced_quantity and row.rate_per_liter:
                # Convert KL to Liters for rate calculation (rate is per liter)
                qty_in_liters = row.invoiced_quantity * 1000
                row.amount = qty_in_liters * row.rate_per_liter
    
    def calculate_totals(self):
        """Calculate total quantities and amounts"""
        total_invoiced = 0
        total_received = 0
        total_amount = 0
        
        for row in self.items:
            total_invoiced += flt(row.invoiced_quantity)
            total_received += flt(row.calculated_received_qty)
            total_amount += flt(row.amount)
        
        self.total_invoiced_qty = total_invoiced
        self.total_received_qty = total_received
        self.total_amount = total_amount
        self.grand_total = total_amount + flt(self.freight_charges)
    
    def on_submit(self):
        """Create Purchase Invoice and Stock Entry on submit"""
        self.create_purchase_invoice()
        self.create_stock_entry()
    
    def create_purchase_invoice(self):
        """Create Purchase Invoice for tanker receipt"""
        if self.purchase_invoice:
            frappe.msgprint(_("Purchase Invoice {0} already exists").format(self.purchase_invoice))
            return
        
        # Create Purchase Invoice
        pi = frappe.get_doc({
            "doctype": "Purchase Invoice",
            "supplier": self.supplier,
            "posting_date": self.posting_date,
            "posting_time": self.posting_time,
            "bill_no": self.supplier_invoice_no,
            "bill_date": self.supplier_invoice_date,
            "items": []
        })
        
        # Add items
        for row in self.items:
            # Convert KL to Liters for purchase invoice
            qty_in_liters = flt(row.invoiced_quantity) * 1000
            
            pi.append("items", {
                "item_code": row.fuel_item,
                "qty": qty_in_liters,
                "uom": "Litre",
                "rate": row.rate_per_liter,
                "warehouse": row.warehouse
            })
        
        # Add freight as expense
        if self.freight_charges:
            # Add freight to taxes
            pi.append("taxes", {
                "charge_type": "Actual",
                "account_head": frappe.db.get_value("Company", pi.company, "default_expense_account"),
                "description": "Freight Charges",
                "tax_amount": self.freight_charges
            })
        
        pi.insert()
        pi.submit()
        
        # Link Purchase Invoice
        self.db_set("purchase_invoice", pi.name)
        
        frappe.msgprint(_("Purchase Invoice {0} created").format(pi.name))
    
    def create_stock_entry(self):
        """Create Stock Entry for fuel receipt"""
        if self.stock_entry:
            frappe.msgprint(_("Stock Entry {0} already exists").format(self.stock_entry))
            return
        
        # Create Stock Entry - Material Receipt
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "posting_date": self.posting_date,
            "posting_time": self.posting_time,
            "items": []
        })
        
        # Add items (use RECEIVED quantity, not invoiced)
        for row in self.items:
            # Convert KL to Liters for stock entry
            qty_in_liters = flt(row.calculated_received_qty) * 1000
            
            se.append("items", {
                "item_code": row.fuel_item,
                "t_warehouse": row.warehouse,
                "qty": qty_in_liters,
                "uom": "Litre",
                "basic_rate": row.rate_per_liter,
                "cost_center": frappe.db.get_value("Company", se.company, "cost_center")
            })
        
        se.insert()
        se.submit()
        
        # Link Stock Entry
        self.db_set("stock_entry", se.name)
        
        frappe.msgprint(_("Stock Entry {0} created").format(se.name))
    
    def on_cancel(self):
        """Cancel linked Purchase Invoice and Stock Entry"""
        # Cancel Stock Entry first
        if self.stock_entry:
            se = frappe.get_doc("Stock Entry", self.stock_entry)
            if se.docstatus == 1:
                se.cancel()
                frappe.msgprint(_("Stock Entry {0} cancelled").format(self.stock_entry))
        
        # Cancel Purchase Invoice
        if self.purchase_invoice:
            pi = frappe.get_doc("Purchase Invoice", self.purchase_invoice)
            if pi.docstatus == 1:
                pi.cancel()
                frappe.msgprint(_("Purchase Invoice {0} cancelled").format(self.purchase_invoice))


# Whitelisted Methods

@frappe.whitelist()
def get_tank_dip_reading(tank):
    """Get current dip reading from tank"""
    if not tank:
        return 0
    
    # Get latest Tank Dip Reading for this tank
    latest_dip = frappe.get_all('Tank Dip Reading',
        filters={'docstatus': 1},
        fields=['name', 'posting_date'],
        order_by='posting_date desc, creation desc',
        limit=1
    )
    
    if latest_dip:
        # Get dip detail for this tank
        dip_detail = frappe.get_value('Tank Dip Detail',
            filters={'parent': latest_dip[0].name, 'tank': tank},
            fieldname='calculated_quantity_liters'
        )
        
        if dip_detail:
            # Convert Liters to KL
            return flt(dip_detail) / 1000
    
    return 0


@frappe.whitelist()
def get_fuel_rate(fuel_item, posting_date=None):
    """Get fuel purchase rate"""
    if not fuel_item:
        return 0
    
    if not posting_date:
        posting_date = frappe.utils.today()
    
    # Get from Fuel Price Update
    price_update = frappe.get_all('Fuel Price Update',
        filters={'docstatus': 1, 'effective_date': ['<=', posting_date]},
        order_by='effective_date desc',
        limit=1
    )
    
    if price_update:
        price = frappe.db.get_value('Fuel Price Update Item',
            filters={'parent': price_update[0].name, 'fuel_item': fuel_item},
            fieldname='new_price'
        )
        if price:
            return price
    
    # Fallback to Item standard rate
    return frappe.db.get_value('Item', fuel_item, 'standard_rate') or 0
