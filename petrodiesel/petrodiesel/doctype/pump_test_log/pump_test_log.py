# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Pump Test Log: 5 litre measure test of nozzles (Legal Metrology)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from petrodiesel.petrodiesel.utils import get_settings


class PumpTestLog(Document):
	def validate(self):
		tol_per_5l = flt(get_settings().pump_test_tolerance_ml) or 15
		for row in self.tests:
			if frappe.db.get_value("Fuel Nozzle Master", row.nozzle, "station") != self.station:
				frappe.throw(
					_("Row {0}: nozzle {1} is not at station {2}.").format(row.idx, row.nozzle, self.station)
				)
			measure = flt(row.measure_liters) or 5
			allowed = tol_per_5l * measure / 5
			row.result = "Pass" if abs(flt(row.error_ml)) <= allowed else "Fail"
		self.all_passed = 1 if all(r.result == "Pass" for r in self.tests) else 0

	def on_submit(self):
		failed = [r.nozzle for r in self.tests if r.result == "Fail"]
		if failed:
			for n in failed:
				frappe.db.set_value("Fuel Nozzle Master", n, "status", "Under Maintenance")
			frappe.msgprint(
				_(
					"Nozzles {0} failed the measure test and were set to Under Maintenance. "
					"Stop sales and call the DU service engineer / Legal Metrology."
				).format(", ".join(failed)),
				indicator="red",
				title=_("Test Failed"),
			)
