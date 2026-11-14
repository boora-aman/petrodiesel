# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from petrodiesel.petrodiesel.utils import get_tank_book_stock


class FuelTankMaster(Document):
	@property
	def current_stock(self):
		return flt(get_tank_book_stock(self.name), 2) if not self.is_new() else 0

	@property
	def ullage(self):
		safe = flt(self.capacity_liters) * (flt(self.safe_fill_percent) or 100) / 100
		return flt(safe - self.current_stock, 2)

	def validate(self):
		company = frappe.get_cached_value("Fuel Station", self.station, "company")
		wh_company = frappe.get_cached_value("Warehouse", self.warehouse, "company")
		if wh_company != company:
			frappe.throw(_("Warehouse {0} belongs to {1}, not {2}.").format(self.warehouse, wh_company, company))
		if frappe.get_cached_value("Item", self.fuel_item, "petro_product_type") != "Fuel":
			frappe.throw(_("Item {0} is not marked as Fuel (Item > Petrol Pump > Product Type).").format(self.fuel_item))
		other = frappe.db.get_value("Fuel Tank Master", {"warehouse": self.warehouse, "name": ["!=", self.name]})
		if other:
			frappe.throw(_("Warehouse {0} is already used by tank {1}. Use one warehouse per tank.").format(self.warehouse, other))
		self.calibration_data.sort(key=lambda r: flt(r.dip_mm))
		prev = None
		for i, row in enumerate(self.calibration_data, 1):
			row.idx = i
			if prev and (flt(row.dip_mm) == flt(prev.dip_mm) or flt(row.volume_liters) < flt(prev.volume_liters)):
				frappe.throw(_("Calibration chart row {0}: dips must be unique and volumes must increase with dip.").format(i))
			prev = row
		if self.calibration_data and flt(self.calibration_data[-1].volume_liters) > flt(self.capacity_liters) * 1.05:
			frappe.msgprint(_("Calibration chart volume exceeds tank capacity. Check the chart."), indicator="orange")
