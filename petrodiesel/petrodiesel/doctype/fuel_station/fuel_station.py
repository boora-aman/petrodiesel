# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class FuelStation(Document):
	def validate(self):
		for field in ("cash_account", "cash_short_excess_account", "employee_advance_account"):
			acc = self.get(field)
			if acc and frappe.get_cached_value("Account", acc, "company") != self.company:
				frappe.throw(
					_("{0} {1} does not belong to company {2}.").format(
						_(self.meta.get_label(field)), acc, self.company
					)
				)
		for field in ("cost_center",):
			val = self.get(field)
			if val and frappe.get_cached_value("Cost Center", val, "company") != self.company:
				frappe.throw(_("Cost Center {0} does not belong to company {1}.").format(val, self.company))
		if (
			self.lube_warehouse
			and frappe.get_cached_value("Warehouse", self.lube_warehouse, "company") != self.company
		):
			frappe.throw(
				_("Warehouse {0} does not belong to company {1}.").format(self.lube_warehouse, self.company)
			)
