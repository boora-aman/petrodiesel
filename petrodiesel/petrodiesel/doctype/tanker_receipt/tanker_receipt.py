# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt


class TankerReceipt(Document):
    def validate(self):
        """Validate and calculate totals"""
        self.validate_required_fields()
        self.validate_dip_readings()
        self.calculate_items()
        self.calculate_totals()
        self.check_variance_threshold()
    
    def validate_required_fields(self):
        """Validate all required fields"""
        if not self.supplier:
            frappe.throw(_("Supplier is mandatory"), title=_("Missing Supplier"))
        if not self.posting_date:
            frappe.throw(_("Posting Date is mandatory"), title=_("Missing Date"))
        if not self.items:
            frappe.throw(_("Please add at least one item to the receipt"), title=_("No Items"))
    
    def validate_dip_readings(self):
        """Validate dip readings are logical"""
        for row in self.items:
            if row.dip_after_unloading and row.dip_before_unloading:
                if flt(row.dip_after_unloading) <= flt(row.dip_before_unloading):
                    frappe.throw(_(f"Row {row.idx}: Dip after unloading ({row.dip_after_unloading} KL) must be greater than "
                                  f"dip before unloading ({row.dip_before_unloading} KL)"), 
                                title=_("Invalid Dip Reading"))
    
    def check_variance_threshold(self):
        """Check if variance exceeds acceptable threshold"""
        for row in self.items:
            if row.shortage_excess:
                variance_liters = abs(flt(row.shortage_excess) * 1000)
                if variance_liters > 50:  # More than 50 liters
                    msg = _(f"Row {row.idx} ({row.fuel_item}): Variance of {variance_liters:.2f} liters detected.\n"
                           f"Invoiced: {row.invoiced_quantity * 1000:.2f}L, Received: {row.calculated_received_qty * 1000:.2f}L")
                    frappe.msgprint(msg, alert=True, indicator='orange', title=_("High Variance"))
    
    def calculate_items(self):
        """Calculate received qty and shortage/excess for each item"""
        for row in self.items:
            # Calculate received quantity from dip readings (in KL)
            if row.dip_after_unloading and row.dip_before_unloading:
                row.calculated_received_qty = flt(row.dip_after_unloading) - flt(row.dip_before_unloading)
            
            # Calculate shortage or excess (KL)
            if row.invoiced_quantity and row.calculated_received_qty:
                row.shortage_excess = flt(row.calculated_received_qty) - flt(row.invoiced_quantity)
            
            # Calculate amount (based on invoiced quantity)
            if row.invoiced_quantity and row.rate_per_liter:
                # Convert KL to Liters for rate calculation (rate is per liter)
                qty_in_liters = flt(row.invoiced_quantity) * 1000
                row.amount = qty_in_liters * flt(row.rate_per_liter)
    
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
        """Create Purchase Invoice, Stock Entry, and Update Tank Levels"""
        self.update_tank_stock_levels()
        self.create_purchase_invoice()
        self.create_stock_entry()
        
        msg = _(f"✓ Tanker Receipt {self.name} processed successfully\n\n"
               f"Supplier: {self.supplier}\n"
               f"Total Invoiced: {self.total_invoiced_qty * 1000:.2f} Liters\n"
               f"Total Received: {self.total_received_qty * 1000:.2f} Liters\n"
               f"Amount: ₹{self.grand_total:,.2f}\n\n"
               f"Tank stock levels have been updated.")
        frappe.msgprint(msg, alert=True, indicator='green', title=_("Receipt Processed"))
    
    def on_cancel(self):
        """Cancel linked documents and reverse tank updates"""
        self.cancel_stock_entry()
        self.cancel_purchase_invoice()
        self.reverse_tank_stock_levels()
    
    def update_tank_stock_levels(self):
        """Increase tank stock levels after fuel receipt"""
        for row in self.items:
            if row.tank and row.calculated_received_qty:
                tank_doc = frappe.get_doc("Fuel Tank Master", row.tank)
                
                # Store dip reading before receipt for variance checking
                dip_before_kl = flt(row.dip_before_unloading)
                
                # Add received quantity (in KL) to current stock
                current_stock_kl = flt(tank_doc.current_stock_level or 0)
                new_stock_kl = current_stock_kl + flt(row.calculated_received_qty)
                
                tank_doc.current_stock_level = new_stock_kl
                tank_doc.last_updated_on = self.posting_date
                tank_doc.last_receipt_date = self.posting_date
                
                # Store receipt reference for dip reading sync
                tank_doc.last_receipt_ref = self.name
                tank_doc.last_receipt_dip_before = dip_before_kl
                tank_doc.last_receipt_dip_after = flt(row.dip_after_unloading)
                
                tank_doc.flags.ignore_permissions = True
                tank_doc.save()
                
                # Check variance with system stock
                variance_kl = flt(row.calculated_received_qty) - flt(row.invoiced_quantity)
                if abs(variance_kl) > 0.05:  # More than 50 liters variance
                    frappe.msgprint(
                        _(f"Tank {row.tank}: Variance of {variance_kl * 1000:.2f} liters detected. "
                          f"Invoiced: {row.invoiced_quantity * 1000:.2f}L, Received: {row.calculated_received_qty * 1000:.2f}L"),
                        alert=True,
                        indicator='orange'
                    )
        
        frappe.msgprint(_("Tank stock levels updated"), alert=True)
    
    def reverse_tank_stock_levels(self):
        """Decrease tank stock levels on cancel"""
        for row in self.items:
            if row.tank and row.calculated_received_qty:
                tank_doc = frappe.get_doc("Fuel Tank Master", row.tank)
                
                current_stock_kl = flt(tank_doc.current_stock_level or 0)
                new_stock_kl = current_stock_kl - flt(row.calculated_received_qty)
                
                tank_doc.current_stock_level = new_stock_kl
                tank_doc.flags.ignore_permissions = True
                tank_doc.save()
    
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
        
        # Add items (use INVOICED quantity for billing)
        for row in self.items:
            qty_in_liters = flt(row.invoiced_quantity) * 1000
            
            pi.append("items", {
                "item_code": row.fuel_item,
                "qty": qty_in_liters,
                "uom": row.uom or "Litre",
                "rate": row.rate_per_liter,
                "warehouse": row.warehouse
            })
        
        # Add freight as expense
        if self.freight_charges:
            pi.append("taxes", {
                "charge_type": "Actual",
                "account_head": frappe.db.get_value("Company", pi.company, "default_expense_account") or "Freight and Forwarding Charges - Company",
                "description": "Freight Charges",
                "tax_amount": self.freight_charges
            })
        
        try:
            pi.flags.ignore_permissions = True
            pi.insert()
            pi.submit()
            
            self.db_set("purchase_invoice", pi.name)
            frappe.msgprint(_("Purchase Invoice {0} created").format(pi.name))
        except Exception as e:
            frappe.log_error(f"Failed to create Purchase Invoice: {str(e)}")
            frappe.throw(_("Failed to create Purchase Invoice. Check error log."))
    
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
        
        # Add items (use RECEIVED quantity for stock)
        for row in self.items:
            qty_in_liters = flt(row.calculated_received_qty) * 1000
            
            se.append("items", {
                "item_code": row.fuel_item,
                "t_warehouse": row.warehouse,
                "qty": qty_in_liters,
                "uom": row.uom or "Litre",
                "basic_rate": row.rate_per_liter,
                "cost_center": frappe.db.get_value("Company", se.company, "cost_center")
            })
        
        try:
            se.flags.ignore_permissions = True
            se.insert()
            se.submit()
            
            self.db_set("stock_entry", se.name)
            frappe.msgprint(_("Stock Entry {0} created").format(se.name))
        except Exception as e:
            frappe.log_error(f"Failed to create Stock Entry: {str(e)}")
            frappe.throw(_("Failed to create Stock Entry. Check error log."))
    
    def cancel_stock_entry(self):
        """Cancel Stock Entry"""
        if self.stock_entry:
            try:
                se = frappe.get_doc("Stock Entry", self.stock_entry)
                if se.docstatus == 1:
                    se.flags.ignore_permissions = True
                    se.cancel()
                    frappe.msgprint(_("Stock Entry {0} cancelled").format(self.stock_entry))
            except Exception as e:
                frappe.log_error(f"Failed to cancel Stock Entry: {str(e)}")
    
    def cancel_purchase_invoice(self):
        """Cancel Purchase Invoice"""
        if self.purchase_invoice:
            try:
                pi = frappe.get_doc("Purchase Invoice", self.purchase_invoice)
                if pi.docstatus == 1:
                    pi.flags.ignore_permissions = True
                    pi.cancel()
                    frappe.msgprint(_("Purchase Invoice {0} cancelled").format(self.purchase_invoice))
            except Exception as e:
                frappe.log_error(f"Failed to cancel Purchase Invoice: {str(e)}")


# Whitelisted Methods

@frappe.whitelist()
def get_tank_dip_reading(tank):
    """Get current dip reading from tank"""
    if not tank:
        return 0
    
    # Get tank current stock level (in KL)
    tank_doc = frappe.get_doc("Fuel Tank Master", tank)
    return flt(tank_doc.current_stock_level or 0)


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
