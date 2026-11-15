# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Internal Stock Transfer between outlet warehouses (shop stores or tank to tank)."""

from collections import defaultdict

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from petrodiesel.petrodiesel.utils import validate_not_future


class InternalStockTransfer(Document):
	ignore_linked_doctypes = (
		"GL Entry",
		"Stock Ledger Entry",
		"Stock Entry",
		"Repost Item Valuation",
		"Serial and Batch Bundle",
	)

	def validate(self):
		self.company = frappe.get_cached_value("Fuel Station", self.station, "company")
		if self.from_warehouse == self.to_warehouse:
			frappe.throw(_("Source and target warehouse must differ."))
		tank_of = {w: t for t, w in frappe.get_all("Fuel Tank Master", ["name", "warehouse"], as_list=True)}

		if self.transfer_type == "Fuel Tank to Tank":
			src, dst = tank_of.get(self.from_warehouse), tank_of.get(self.to_warehouse)
			if not src or not dst:
				frappe.throw(_("Choose two tank warehouses for a tank-to-tank transfer."))
			fuel = frappe.db.get_value("Fuel Tank Master", src, "fuel_item")
			if frappe.db.get_value("Fuel Tank Master", dst, "fuel_item") != fuel:
				frappe.throw(
					_(
						"Tank {0} holds {1} and tank {2} holds {3}. Fuel can only move between tanks of the same product."
					).format(src, fuel, dst, frappe.db.get_value("Fuel Tank Master", dst, "fuel_item"))
				)
			if len(self.items) != 1:
				frappe.throw(_("A tank-to-tank transfer has exactly one line: the tank's fuel."))
			if self.items[0].item_code and self.items[0].item_code != fuel:
				frappe.throw(_("Tank {0} holds {1}, not {2}.").format(src, fuel, self.items[0].item_code))
			self.items[0].item_code = fuel
		else:
			for w in (self.from_warehouse, self.to_warehouse):
				if w in tank_of:
					frappe.throw(
						_("{0} is a fuel tank. Use the type 'Fuel Tank to Tank' to move fuel.").format(w)
					)
			for r in self.items:
				if frappe.get_cached_value("Item", r.item_code, "petro_product_type") == "Fuel":
					frappe.throw(
						_("Row {0}: {1} is fuel and is kept only in tanks.").format(r.idx, r.item_code)
					)

		validate_not_future(self.posting_date)
		total = defaultdict(float)
		for r in self.items:
			if flt(r.qty) <= 0:
				frappe.throw(_("Row {0}: quantity must be positive.").format(r.idx))
			total[r.item_code] += flt(r.qty)
		for r in self.items:
			r.available_qty = available_on(r.item_code, self.from_warehouse, self.posting_date)
		for item, qty in total.items():
			avail = available_on(item, self.from_warehouse, self.posting_date)
			if qty > avail + 0.001:
				frappe.throw(
					_("Only {0} of {1} available in {2} on {3}.").format(
						avail, item, self.from_warehouse, frappe.format(self.posting_date, "Date")
					)
				)
		if self.transfer_type == "Fuel Tank to Tank":
			dst = frappe.db.get_value(
				"Fuel Tank Master",
				{"warehouse": self.to_warehouse},
				["name", "capacity_liters", "safe_fill_percent", "fuel_item"],
				as_dict=True,
			)
			if dst and flt(dst.capacity_liters):
				room = flt(dst.capacity_liters) * (flt(dst.safe_fill_percent) or 100) / 100 - flt(
					frappe.db.get_value(
						"Bin", {"item_code": dst.fuel_item, "warehouse": self.to_warehouse}, "actual_qty"
					)
				)
				if sum(total.values()) > room + 0.5:
					frappe.throw(
						_("Tank {0} has room for only {1} L up to its safe-fill level.").format(
							dst.name, flt(max(room, 0), 0)
						)
					)

	def on_submit(self):
		se = frappe.new_doc("Stock Entry")
		se.update(
			{
				"stock_entry_type": "Material Transfer",
				"purpose": "Material Transfer",
				"company": self.company,
				"posting_date": self.posting_date,
				"set_posting_time": 1,
				"remarks": _("Internal transfer {0}: {1}").format(self.name, self.remarks or ""),
			}
		)
		for r in self.items:
			se.append(
				"items",
				{
					"item_code": r.item_code,
					"qty": r.qty,
					"s_warehouse": self.from_warehouse,
					"t_warehouse": self.to_warehouse,
				},
			)
		se.flags.ignore_permissions = True
		se.insert()
		se.submit()
		self.db_set("stock_entry", se.name)

	def on_cancel(self):
		if self.stock_entry and frappe.db.get_value("Stock Entry", self.stock_entry, "docstatus") == 1:
			se = frappe.get_doc("Stock Entry", self.stock_entry)
			se.flags.ignore_permissions = True
			se.cancel()


def available_on(item_code, warehouse, posting_date=None) -> float:
	"""Stock that can be moved: the lower of the balance on the posting date and today's balance
	(a back-dated transfer must not make later stock negative)."""
	now = flt(frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty"))
	if not posting_date:
		return now
	from erpnext.stock.utils import get_stock_balance

	return min(now, flt(get_stock_balance(item_code, warehouse, posting_date, "23:59:59")))


@frappe.whitelist()
def get_available(item_code: str, warehouse: str, posting_date: str | None = None) -> float:
	frappe.has_permission("Internal Stock Transfer", "create", throw=True)
	return available_on(item_code, warehouse, posting_date)
