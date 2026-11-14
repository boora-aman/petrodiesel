# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Internal Stock Transfer between outlet warehouses (shop stores or tank to tank)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class InternalStockTransfer(Document):
	ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Stock Entry", "Repost Item Valuation",
		"Serial and Batch Bundle")

	def validate(self):
		self.company = frappe.get_cached_value("Fuel Station", self.station, "company")
		if self.from_warehouse == self.to_warehouse:
			frappe.throw(_("Source and target warehouse must differ."))
		tanks = {w: t for t, w in frappe.get_all("Fuel Tank Master", {"station": self.station}, ["name", "warehouse"], as_list=True)}
		if self.transfer_type == "Fuel Tank to Tank":
			if self.from_warehouse not in tanks or self.to_warehouse not in tanks:
				frappe.throw(_("Choose two tank warehouses for a tank-to-tank transfer."))
		for r in self.items:
			r.available_qty = flt(frappe.db.get_value("Bin", {"item_code": r.item_code, "warehouse": self.from_warehouse},
				"actual_qty"))
			if flt(r.qty) <= 0:
				frappe.throw(_("Row {0}: quantity must be positive.").format(r.idx))
			if flt(r.qty) > r.available_qty + 0.001:
				frappe.throw(_("Row {0}: only {1} of {2} available in {3}.").format(r.idx, r.available_qty, r.item_code,
					self.from_warehouse))
			if self.transfer_type == "Fuel Tank to Tank":
				for w in (self.from_warehouse, self.to_warehouse):
					if frappe.db.get_value("Fuel Tank Master", tanks[w], "fuel_item") != r.item_code:
						frappe.throw(_("Tank {0} does not hold {1}.").format(tanks[w], r.item_code))

	def on_submit(self):
		se = frappe.new_doc("Stock Entry")
		se.update({"stock_entry_type": "Material Transfer", "purpose": "Material Transfer", "company": self.company,
			"posting_date": self.posting_date, "set_posting_time": 1,
			"remarks": _("Internal transfer {0}: {1}").format(self.name, self.remarks or "")})
		for r in self.items:
			se.append("items", {"item_code": r.item_code, "qty": r.qty, "s_warehouse": self.from_warehouse,
				"t_warehouse": self.to_warehouse})
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
