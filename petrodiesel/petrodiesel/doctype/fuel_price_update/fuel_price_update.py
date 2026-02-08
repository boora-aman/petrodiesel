# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt, getdate, nowtime


class FuelPriceUpdate(Document):
    def validate(self):
        self.validate_effective_date()
        self.calculate_price_changes()
    
    def on_submit(self):
        self.update_item_prices()
        items_updated = len(self.price_updates)
        msg = _(f"✓ Fuel Price Update {self.name} applied successfully\n\n"
               f"Effective Date: {self.effective_date}\n"
               f"Items Updated: {items_updated}\n\n"
               f"All fuel prices have been updated in the system.")
        frappe.msgprint(msg, alert=True, indicator='green', title=_("Prices Updated"))
    
    def on_cancel(self):
        self.revert_item_prices()
        frappe.msgprint(_(f"Fuel Price Update {self.name} cancelled. Prices reverted to previous values."), 
                       alert=True, indicator='orange', title=_("Prices Reverted"))
    
    def validate_effective_date(self):
        """Validate effective date is not in past"""
        if not self.effective_date:
            frappe.throw(_("Effective Date is mandatory"), title=_("Missing Date"))
        
        if getdate(self.effective_date) < getdate(frappe.utils.today()):
            frappe.msgprint(_(f"Warning: Effective date ({self.effective_date}) is in the past. "
                            "This will apply historical pricing."), 
                          alert=True, indicator='orange')
    
    def calculate_price_changes(self):
        """Calculate price change percentage"""
        for row in self.price_updates:
            if row.old_price and row.new_price:
                price_diff = flt(row.new_price) - flt(row.old_price)
                row.change_amount = price_diff
                row.change_percentage = (price_diff / flt(row.old_price)) * 100 if row.old_price else 0
    
    def update_item_prices(self):
        """Update Item Price master for all fuel items"""
        price_list = self.price_list or "Retail Fuel Prices"
        
        for row in self.price_updates:
            # Check if Item Price exists
            existing_price = frappe.db.exists("Item Price", {
                "item_code": row.fuel_item,
                "price_list": price_list
            })
            
            if existing_price:
                # Update existing
                frappe.db.set_value("Item Price", existing_price, {
                    "price_list_rate": row.new_price,
                    "valid_from": self.effective_date
                })
            else:
                # Create new Item Price
                item_price = frappe.get_doc({
                    "doctype": "Item Price",
                    "item_code": row.fuel_item,
                    "price_list": price_list,
                    "price_list_rate": row.new_price,
                    "valid_from": self.effective_date
                })
                item_price.flags.ignore_permissions = True
                item_price.insert()
            
            # Also update Item standard_rate
            frappe.db.set_value("Item", row.fuel_item, "standard_rate", row.new_price)
        
        frappe.db.commit()
    
    def revert_item_prices(self):
        """Revert to old prices on cancel"""
        price_list = self.price_list or "Retail Fuel Prices"
        
        for row in self.price_updates:
            if row.old_price:
                existing_price = frappe.db.exists("Item Price", {
                    "item_code": row.fuel_item,
                    "price_list": price_list
                })
                
                if existing_price:
                    frappe.db.set_value("Item Price", existing_price, "price_list_rate", row.old_price)
                
                frappe.db.set_value("Item", row.fuel_item, "standard_rate", row.old_price)
        
        frappe.db.commit()


@frappe.whitelist()
def get_current_fuel_price(fuel_item, price_list="Retail Fuel Prices"):
    """Get current price for fuel item"""
    if not fuel_item:
        return 0
    
    # Try to get from Item Price
    price = frappe.db.get_value("Item Price", 
        filters={"item_code": fuel_item, "price_list": price_list},
        fieldname="price_list_rate"
    )
    
    if price:
        return price
    
    # Fallback to Item standard_rate
    return frappe.db.get_value("Item", fuel_item, "standard_rate") or 0


@frappe.whitelist()
def get_price_history(fuel_item, limit=10):
    """Get price change history for fuel item"""
    history = frappe.db.sql("""
        SELECT 
            fpu.name,
            fpu.effective_date,
            fpu.effective_time,
            fpui.old_price,
            fpui.new_price,
            fpui.change_percentage
        FROM `tabFuel Price Update Item` fpui
        INNER JOIN `tabFuel Price Update` fpu ON fpu.name = fpui.parent
        WHERE fpui.fuel_item = %s
        AND fpu.docstatus = 1
        ORDER BY fpu.effective_date DESC, fpu.effective_time DESC
        LIMIT %s
    """, (fuel_item, limit), as_dict=1)
    
    return history
