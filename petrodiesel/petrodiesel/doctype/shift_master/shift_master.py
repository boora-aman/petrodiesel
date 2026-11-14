# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ShiftMaster(Document):
	def validate(self):
		if frappe.db.exists("Shift Master", {"sequence": self.sequence, "is_active": 1, "name": ["!=", self.name]}) and self.is_active:
			frappe.throw(_("Another active shift already has sequence {0}.").format(self.sequence))
