# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PetrodieselSettings(Document):
	def validate(self):
		# shift cash maths assumes rates are tax-inclusive (pump prices include VAT/GST)
		for field in ("fuel_tax_template", "lube_tax_template"):
			template = self.get(field)
			if not template:
				continue
			exclusive = frappe.get_all(
				"Sales Taxes and Charges",
				{
					"parent": template,
					"parenttype": "Sales Taxes and Charges Template",
					"included_in_print_rate": 0,
				},
				pluck="account_head",
			)
			if exclusive:
				frappe.throw(
					_(
						"Tax template {0} must have 'Is this Tax included in Basic Rate?' ticked on every row, "
						"because pump prices include tax."
					).format(frappe.bold(template))
				)

	def on_update(self):
		sync_shift_workflow(self.require_shift_approval)


def sync_shift_workflow(active):
	"""Turn the approval workflow on/off and keep workflow_state in step with docstatus."""
	if not frappe.db.exists("Workflow", "Shift Sale Entry Approval"):
		return
	frappe.db.set_value("Workflow", "Shift Sale Entry Approval", "is_active", 1 if active else 0)
	frappe.db.sql(
		"""update `tabShift Sale Entry` set workflow_state = case docstatus
			when 1 then 'Approved' when 2 then 'Cancelled' else workflow_state end
		where docstatus > 0 and ifnull(workflow_state, '') not in ('Approved', 'Cancelled')"""
	)
	if active:
		frappe.db.sql(
			"""update `tabShift Sale Entry` set workflow_state = 'Draft'
			where docstatus = 0 and ifnull(workflow_state, '') = ''"""
		)
	frappe.clear_cache(doctype="Shift Sale Entry")
