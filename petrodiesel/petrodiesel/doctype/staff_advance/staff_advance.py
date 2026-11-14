# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from petrodiesel.petrodiesel.utils import get_mode_of_payment_account


class StaffAdvance(Document):
	ignore_linked_doctypes = ("GL Entry", "Payment Ledger Entry", "Journal Entry")

	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be positive."))
		self.company = frappe.get_cached_value("Fuel Station", self.station, "company")
		if not frappe.get_cached_value("Fuel Station", self.station, "employee_advance_account"):
			frappe.throw(_("Set the Employee Advance Account on Fuel Station {0}.").format(self.station))

	def on_submit(self):
		station = frappe.get_cached_doc("Fuel Station", self.station)
		je = frappe.get_doc(
			{
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"company": self.company,
				"posting_date": self.posting_date,
				"user_remark": _("Staff advance {0} to {1}: {2}").format(
					self.name, self.employee_name, self.purpose or ""
				),
				"accounts": [
					{
						"account": station.employee_advance_account,
						"debit_in_account_currency": self.amount,
						"cost_center": station.cost_center,
						"user_remark": self.employee_name,
					},
					{
						"account": get_mode_of_payment_account(self.mode_of_payment, self.company),
						"credit_in_account_currency": self.amount,
						"cost_center": station.cost_center,
					},
				],
			}
		)
		je.flags.ignore_permissions = True
		je.insert()
		je.submit()
		self.db_set("journal_entry", je.name)

	def on_cancel(self):
		if self.journal_entry and frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus") == 1:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			je.flags.ignore_permissions = True
			je.cancel()
