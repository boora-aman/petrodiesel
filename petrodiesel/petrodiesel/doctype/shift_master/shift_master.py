# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import get_time


class ShiftMaster(Document):
    def validate(self):
        self.validate_shift_timings()
        self.validate_duplicate_shift()
    
    def validate_shift_timings(self):
        """Validate start and end times"""
        if not self.start_time or not self.end_time:
            frappe.throw(_("Start Time and End Time are mandatory"))
        
        start = get_time(self.start_time)
        end = get_time(self.end_time)
        
        # Calculate shift duration
        if end > start:
            duration = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)
        else:
            # Shift crosses midnight
            duration = (24 * 60) - (start.hour * 60 + start.minute) + (end.hour * 60 + end.minute)
        
        self.shift_duration_hours = duration / 60
    
    def validate_duplicate_shift(self):
        """Check for duplicate shift code"""
        duplicate = frappe.db.exists("Shift Master", {
            "shift_code": self.shift_code,
            "name": ["!=", self.name]
        })
        
        if duplicate:
            frappe.throw(_(f"Shift Code {self.shift_code} already exists"))


@frappe.whitelist()
def get_active_shifts():
    """Get all active shifts"""
    shifts = frappe.get_all("Shift Master",
        filters={"status": "Active"},
        fields=["name", "shift_name", "shift_code", "start_time", "end_time", "shift_duration_hours"],
        order_by="start_time"
    )
    
    return shifts


@frappe.whitelist()
def get_current_shift():
    """Get current active shift based on time"""
    from frappe.utils import now_datetime
    
    current_time = now_datetime().time()
    
    shifts = frappe.get_all("Shift Master",
        filters={"status": "Active"},
        fields=["name", "shift_name", "start_time", "end_time"]
    )
    
    for shift in shifts:
        start = get_time(shift.start_time)
        end = get_time(shift.end_time)
        
        if start <= end:
            # Normal shift (doesn't cross midnight)
            if start <= current_time <= end:
                return shift
        else:
            # Shift crosses midnight
            if current_time >= start or current_time <= end:
                return shift
    
    return None
