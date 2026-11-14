# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PetrodieselSettings(Document):
	def on_update(self):
		if frappe.db.exists("Workflow", "Shift Sale Entry Approval"):
			frappe.db.set_value("Workflow", "Shift Sale Entry Approval", "is_active", 1 if self.require_shift_approval else 0)
			frappe.clear_cache(doctype="Shift Sale Entry")
