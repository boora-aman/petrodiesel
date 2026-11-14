# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class FuelNozzleMaster(Document):
	def validate(self):
		du_station = frappe.get_cached_value("Dispensing Unit", self.dispensing_unit, "station")
		tank_station = frappe.get_cached_value("Fuel Tank Master", self.tank, "station")
		if du_station != tank_station:
			frappe.throw(
				_("Tank {0} is at {1} but dispensing unit {2} is at {3}.").format(
					self.tank, tank_station, self.dispensing_unit, du_station
				)
			)
		self.station = du_station
		if self.is_new() and not self.last_shift_entry:
			self.last_reading = flt(self.opening_totalizer)
