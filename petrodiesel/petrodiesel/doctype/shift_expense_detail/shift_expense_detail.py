# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import frappe.utils


class ShiftExpenseDetail(Document):
	def validate(self):
		"""Validate expense detail"""
		if self.amount and flt(self.amount) <= 0:
			frappe.throw("Amount must be greater than 0")
			
		if not self.expense_type:
			frappe.throw("Expense Type is required")
