# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Internal Stock Transfer between outlet warehouses (shop stores or tank to tank)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


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

		for r in self.items:
			r.available_qty = flt(
				frappe.db.get_value(
					"Bin", {"item_code": r.item_code, "warehouse": self.from_warehouse}, "actual_qty"
				)
			)
			if flt(r.qty) <= 0:
				frappe.throw(_("Row {0}: quantity must be positive.").format(r.idx))
			if flt(r.qty) > r.available_qty + 0.001:
				frappe.throw(
					_("Row {0}: only {1} of {2} available in {3}.").format(
						r.idx, r.available_qty, r.item_code, self.from_warehouse
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


@frappe.whitelist()
def get_available(item_code: str, warehouse: str) -> float:
	return flt(frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty"))
