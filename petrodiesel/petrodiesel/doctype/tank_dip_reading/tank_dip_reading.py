# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Tank Dip Reading: physical stock check of tanks with dip rod and water paste."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from petrodiesel.petrodiesel.utils import dip_to_volume, get_tank_book_stock


class TankDipReading(Document):
	def validate(self):
		seen = set()
		for row in self.readings:
			tank = frappe.get_cached_doc("Fuel Tank Master", row.tank)
			if tank.station != self.station:
				frappe.throw(_("Row {0}: tank {1} is not at station {2}.").format(row.idx, row.tank, self.station))
			if row.tank in seen:
				frappe.throw(_("Tank {0} appears twice.").format(row.tank))
			seen.add(row.tank)
			row.fuel_item = tank.fuel_item
			gross = dip_to_volume(row.tank, row.dip_mm)
			row.water_volume = dip_to_volume(row.tank, row.water_dip_mm) if flt(row.water_dip_mm) else 0
			row.dip_stock = flt(gross - row.water_volume, 2)
			row.book_stock = flt(get_tank_book_stock(row.tank, self.posting_date, self.posting_time), 2)
			row.variance = flt(row.dip_stock - row.book_stock, 2)
			if flt(row.water_dip_mm) > 0:
				frappe.msgprint(_("Water found in tank {0} ({1} mm). Inform the OMC and arrange removal.").format(
					row.tank, row.water_dip_mm), indicator="orange", alert=True)
		self.total_dip_stock = flt(sum(flt(r.dip_stock) for r in self.readings), 2)
		self.total_book_stock = flt(sum(flt(r.book_stock) for r in self.readings), 2)
		self.total_variance = flt(self.total_dip_stock - self.total_book_stock, 2)

	def on_submit(self):
		for row in self.readings:
			last = frappe.db.get_value("Fuel Tank Master", row.tank, "last_dip_on")
			now = f"{self.posting_date} {self.posting_time}"
			if not last or str(last) <= now:
				frappe.db.set_value("Fuel Tank Master", row.tank, {
					"last_dip_mm": row.dip_mm, "last_dip_stock": row.dip_stock, "last_dip_on": now,
				})


	def on_cancel(self):
		for row in self.readings:
			refresh_last_dip(row.tank)


def refresh_last_dip(tank):
	"""Point the tank's last dip at its latest submitted dip reading."""
	last = frappe.db.sql("""select r.dip_mm, r.dip_stock, timestamp(d.posting_date, d.posting_time) at
		from `tabTank Dip Detail` r join `tabTank Dip Reading` d on d.name = r.parent
		where r.tank = %s and d.docstatus = 1 order by d.posting_date desc, d.posting_time desc limit 1""", tank, as_dict=True)
	frappe.db.set_value("Fuel Tank Master", tank, {
		"last_dip_mm": last[0].dip_mm if last else 0,
		"last_dip_stock": last[0].dip_stock if last else 0,
		"last_dip_on": last[0].at if last else None,
	})


@frappe.whitelist()
def get_tanks(station: str) -> list[dict]:
	frappe.has_permission("Tank Dip Reading", "create", throw=True)
	return frappe.get_all("Fuel Tank Master", {"station": station, "status": "Active"},
		["name as tank", "fuel_item"], order_by="name asc")
