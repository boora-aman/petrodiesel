# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Recover a staff advance by cash return or salary deduction (HRMS Additional Salary)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_first_day, getdate

from petrodiesel.petrodiesel.advances import advance_outstanding
from petrodiesel.petrodiesel.utils import get_mode_of_payment_account

RECOVERY_COMPONENT = "Advance Recovery"


class StaffAdvanceRecovery(Document):
	ignore_linked_doctypes = ("GL Entry", "Payment Ledger Entry", "Journal Entry", "Additional Salary")

	def validate(self):
		self.company = frappe.get_cached_value("Fuel Station", self.station, "company")
		self.outstanding = advance_outstanding(self.employee, exclude=self.name)
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be positive."))
		if flt(self.amount) > flt(self.outstanding) + 0.01:
			frappe.throw(_("Recovery {0} is more than the outstanding advance {1}.").format(
				frappe.format(self.amount, "Currency"), frappe.format(self.outstanding, "Currency")))
		if self.method == "Salary Deduction":
			if "hrms" not in frappe.get_installed_apps():
				frappe.throw(_("Salary deduction needs the HRMS app. Use Cash Return instead."))
			self.payroll_date = self.payroll_date or get_first_day(self.posting_date)
			if not frappe.db.exists("Salary Structure Assignment", {"employee": self.employee, "docstatus": 1,
					"from_date": ["<=", self.payroll_date]}):
				frappe.throw(_("{0} has no salary structure assigned, so the advance cannot be deducted from salary. "
					"Assign a salary structure in HR, or recover by Cash Return.").format(self.employee_name))
			self.salary_component = self.salary_component or ensure_recovery_component(self.company, self.station)

	def on_submit(self):
		if self.method == "Cash Return":
			station = frappe.get_cached_doc("Fuel Station", self.station)
			je = frappe.get_doc({
				"doctype": "Journal Entry", "voucher_type": "Journal Entry", "company": self.company,
				"posting_date": self.posting_date,
				"user_remark": _("Advance returned by {0} ({1})").format(self.employee_name, self.name),
				"accounts": [
					{"account": get_mode_of_payment_account(self.mode_of_payment or "Cash", self.company),
						"debit_in_account_currency": self.amount, "cost_center": station.cost_center},
					{"account": station.employee_advance_account, "credit_in_account_currency": self.amount,
						"cost_center": station.cost_center, "user_remark": self.employee_name},
				],
			})
			je.flags.ignore_permissions = True
			je.insert()
			je.submit()
			self.db_set("journal_entry", je.name)
		else:
			ads = frappe.get_doc({
				"doctype": "Additional Salary",
				"employee": self.employee,
				"company": self.company,
				"salary_component": self.salary_component,
				"type": "Deduction",
				"amount": self.amount,
				"payroll_date": self.payroll_date,
				"overwrite_salary_structure_amount": 0,
				"ref_doctype": self.doctype,
				"ref_docname": self.name,
			})
			ads.flags.ignore_permissions = True
			ads.insert()
			ads.submit()
			self.db_set("additional_salary", ads.name)

	def on_cancel(self):
		for dt, name in (("Journal Entry", self.journal_entry), ("Additional Salary", self.additional_salary)):
			if name and frappe.db.get_value(dt, name, "docstatus") == 1:
				d = frappe.get_doc(dt, name)
				d.flags.ignore_permissions = True
				d.cancel()


def ensure_recovery_component(company, station):
	"""Deduction component whose GL account is the staff advance account."""
	account = frappe.get_cached_value("Fuel Station", station, "employee_advance_account")
	if not frappe.db.exists("Salary Component", RECOVERY_COMPONENT):
		frappe.get_doc({"doctype": "Salary Component", "salary_component": RECOVERY_COMPONENT,
			"salary_component_abbr": "ADVR", "type": "Deduction", "depends_on_payment_days": 0,
			"accounts": [{"company": company, "account": account}]}).insert(ignore_permissions=True)
	else:
		comp = frappe.get_doc("Salary Component", RECOVERY_COMPONENT)
		if not any(a.company == company for a in comp.accounts):
			comp.append("accounts", {"company": company, "account": account})
			comp.save(ignore_permissions=True)
	return RECOVERY_COMPONENT
