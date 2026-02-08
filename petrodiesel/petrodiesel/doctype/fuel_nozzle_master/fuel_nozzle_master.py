# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class FuelNozzleMaster(Document):
    def validate(self):
        self.validate_duplicate_nozzle()
        self.validate_tank_fuel_match()
        self.validate_required_fields()
    
    def validate_required_fields(self):
        """Validate all required fields are present"""
        if not self.fuel_item:
            frappe.throw(_("Fuel Item is mandatory"))
        if not self.source_tank:
            frappe.throw(_("Source Tank is mandatory"))
        if not self.nozzle_number:
            frappe.throw(_("Nozzle Number is mandatory"))
    
    def validate_duplicate_nozzle(self):
        """Ensure no duplicate nozzle ID or number"""
        # Check nozzle_id
        duplicate = frappe.db.exists("Fuel Nozzle Master", {
            "nozzle_id": self.nozzle_id,
            "name": ["!=", self.name]
        })
        
        if duplicate:
            frappe.throw(_(f"Nozzle ID {self.nozzle_id} already exists. Please use a unique Nozzle ID."), 
                        title=_("Duplicate Nozzle ID"))
        
        # Check nozzle_number
        duplicate_number = frappe.db.exists("Fuel Nozzle Master", {
            "nozzle_number": self.nozzle_number,
            "name": ["!=", self.name]
        })
        
        if duplicate_number:
            frappe.throw(_(f"Nozzle Number {self.nozzle_number} already exists. Please use a unique Nozzle Number."), 
                        title=_("Duplicate Nozzle Number"))
    
    def validate_tank_fuel_match(self):
        """Validate that nozzle fuel matches tank fuel"""
        if self.source_tank and self.fuel_item:
            tank_fuel = frappe.db.get_value("Fuel Tank Master", self.source_tank, "fuel_item")
            
            if tank_fuel and tank_fuel != self.fuel_item:
                frappe.throw(_(f"Nozzle fuel item '{self.fuel_item}' does not match Tank fuel item '{tank_fuel}'. "
                              f"Please select a tank that contains {self.fuel_item} or change the fuel item."), 
                            title=_("Fuel Mismatch"))


@frappe.whitelist()
def get_nozzle_status(nozzle):
    """Get current status and reading of nozzle"""
    if not nozzle:
        return {}
    
    nozzle_doc = frappe.get_doc("Fuel Nozzle Master", nozzle)
    
    return {
        "current_reading": nozzle_doc.current_reading,
        "status": nozzle_doc.status,
        "fuel_item": nozzle_doc.fuel_item,
        "source_tank": nozzle_doc.source_tank,
        "last_updated_on": nozzle_doc.last_updated_on,
        "last_shift": nozzle_doc.last_shift
    }
