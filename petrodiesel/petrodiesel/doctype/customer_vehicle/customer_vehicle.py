# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import re

from frappe.model.document import Document


class CustomerVehicle(Document):
	def autoname(self):
		self.vehicle_no = normalize_vehicle_no(self.vehicle_no)
		self.name = self.vehicle_no

	def validate(self):
		self.vehicle_no = normalize_vehicle_no(self.vehicle_no)


def normalize_vehicle_no(value: str) -> str:
	"""HR 26 AB 1234 / hr-26-ab-1234 -> HR26AB1234"""
	return re.sub(r"[^A-Z0-9]", "", (value or "").upper())
