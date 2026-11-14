# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Nozzle Meter Change: totalizer replaced / reset between two shifts."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class NozzleMeterChange(Document):
	def validate(self):
		last = flt(frappe.db.get_value("Fuel Nozzle Master", self.nozzle, "last_reading"))
		if self.docstatus == 0:
			self.previous_last_reading = last
		if abs(flt(self.old_meter_final_reading) - last) > 0.01:
			frappe.throw(_("Old meter final reading {0} must equal the nozzle's last closing reading {1}. "
				"Close the running shift first.").format(self.old_meter_final_reading, last))
		if frappe.db.exists("Shift Sale Entry", {"docstatus": 0, "name": ["in", frappe.get_all(
				"Shift Nozzle Reading", {"nozzle": self.nozzle, "parenttype": "Shift Sale Entry"}, pluck="parent")]}):
			frappe.msgprint(_("Draft shift entries exist for this nozzle; refresh their opening readings after this change."),
				indicator="orange", alert=True)

	def on_submit(self):
		frappe.db.set_value("Fuel Nozzle Master", self.nozzle, {
			"last_reading": flt(self.new_meter_start_reading), "last_reading_on": self.posting_date})

	def before_cancel(self):
		last = flt(frappe.db.get_value("Fuel Nozzle Master", self.nozzle, "last_reading"))
		if abs(last - flt(self.new_meter_start_reading)) > 0.01:
			frappe.throw(_("Shifts were recorded on the new meter. Cancel them first."))

	def on_cancel(self):
		frappe.db.set_value("Fuel Nozzle Master", self.nozzle, "last_reading", self.previous_last_reading)
