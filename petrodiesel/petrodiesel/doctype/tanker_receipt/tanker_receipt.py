# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Tanker Receipt: decantation of a tank lorry into underground tanks.

Follows the OMC Marketing Discipline Guidelines: seal check, density check
against the challan (±3 kg/m³ at 15°C), dips before and after decantation.
On submit a Purchase Invoice (update_stock) books the invoiced quantity into
the tank warehouse, and a Stock Entry books any transit short/excess.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from petrodiesel.petrodiesel.utils import dip_to_volume, get_settings


class TankerReceipt(Document):
	ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Payment Ledger Entry",
		"Purchase Invoice", "Stock Entry", "Repost Item Valuation", "Serial and Batch Bundle")

	def validate(self):
		station = frappe.get_cached_doc("Fuel Station", self.station)
		self.company = station.company
		tolerance = flt(get_settings().density_tolerance) or 3.0
		density_fail = []
		for row in self.items:
			tank = frappe.get_cached_doc("Fuel Tank Master", row.tank)
			if tank.station != self.station:
				frappe.throw(_("Row {0}: tank {1} is not at station {2}.").format(row.idx, row.tank, self.station))
			row.fuel_item = tank.fuel_item
			row.amount = flt(flt(row.invoice_qty) * flt(row.rate), 2)

			if flt(row.challan_density) and flt(row.density_at_15):
				row.density_variance = flt(flt(row.density_at_15) - flt(row.challan_density), 1)
				row.density_ok = 1 if abs(row.density_variance) <= tolerance else 0
				if not row.density_ok:
					density_fail.append(row)
			else:
				row.density_variance = 0
				row.density_ok = 0

			if flt(row.dip_before_mm) or flt(row.dip_after_mm):
				row.stock_before = dip_to_volume(row.tank, row.dip_before_mm)
				row.stock_after = dip_to_volume(row.tank, row.dip_after_mm)
				row.received_qty = flt(row.stock_after - row.stock_before + flt(row.sales_during_decantation), 2)
			elif not flt(row.received_qty):
				row.received_qty = flt(row.invoice_qty)
			row.shortage_qty = flt(flt(row.invoice_qty) - flt(row.received_qty), 2)

			capacity = flt(tank.capacity_liters) * (flt(tank.safe_fill_percent) or 100) / 100
			if row.stock_after and capacity and row.stock_after > capacity + 1:
				frappe.msgprint(_("Row {0}: tank {1} filled above safe-fill level ({2} L).").format(
					row.idx, row.tank, flt(capacity, 0)), indicator="orange", alert=True)

		if density_fail and not self.override_density_check:
			frappe.throw(
				_("Density variance beyond ±{0} kg/m³ for: {1}. Do not decant. "
				"Raise a complaint with the OMC, or tick 'Accept Despite Density Variance' with remarks.").format(
					tolerance, ", ".join(f"{r.tank} ({r.density_variance:+})" for r in density_fail)),
				title=_("Density Check Failed"))
		if self.override_density_check and density_fail and not self.remarks:
			frappe.throw(_("Enter remarks explaining why the density variance was accepted."))
		if not self.seals_intact and not self.remarks:
			frappe.throw(_("Seals were not intact. Record the details in remarks."))

		self.total_invoice_qty = flt(sum(flt(r.invoice_qty) for r in self.items), 2)
		self.total_received_qty = flt(sum(flt(r.received_qty) for r in self.items), 2)
		self.total_shortage_qty = flt(sum(flt(r.shortage_qty) for r in self.items), 2)
		self.total_amount = flt(sum(flt(r.amount) for r in self.items), 2)

	def before_submit(self):
		if self.override_density_check and not frappe.db.get_value(
			"Has Role", {"parent": frappe.session.user, "role": ["in", ["Pump Owner", "Pump Manager", "System Manager"]]}
		):
			frappe.throw(_("Only a Pump Manager or Owner can accept a density variance."))

	def on_submit(self):
		self.make_purchase_invoice()
		self.make_transit_adjustment()
		for row in self.items:
			if flt(row.dip_after_mm):
				frappe.db.set_value("Fuel Tank Master", row.tank, {
					"last_dip_mm": row.dip_after_mm,
					"last_dip_stock": row.stock_after,
					"last_dip_on": f"{self.posting_date} {self.posting_time}",
				})

	def on_cancel(self):
		docs = [("Stock Entry", n) for n in frappe.get_all(
			"Stock Entry", {"tanker_receipt": self.name, "docstatus": 1}, pluck="name")]
		docs.append(("Purchase Invoice", self.purchase_invoice))
		for doctype, name in docs:
			if name and frappe.db.get_value(doctype, name, "docstatus") == 1:
				doc = frappe.get_doc(doctype, name)
				doc.flags.ignore_permissions = True
				doc.flags.ignore_links = True
				doc.cancel()

	def make_purchase_invoice(self):
		cost_center = frappe.get_cached_value("Fuel Station", self.station, "cost_center")
		pi = frappe.new_doc("Purchase Invoice")
		pi.update({
			"company": self.company,
			"supplier": self.supplier,
			"posting_date": self.posting_date,
			"set_posting_time": 1,
			"posting_time": self.posting_time,
			"bill_no": self.supplier_invoice_no,
			"bill_date": self.supplier_invoice_date or self.posting_date,
			"due_date": self.posting_date,
			"update_stock": 1,
			"disable_rounded_total": 1,
			"cost_center": cost_center,
			"tanker_receipt": self.name,
			"remarks": _("Tanker {0} decanted via {1}").format(self.truck_no, self.name),
		})
		for row in self.items:
			pi.append("items", {
				"item_code": row.fuel_item,
				"qty": row.invoice_qty,
				"rate": row.rate,
				"price_list_rate": row.rate,
				"warehouse": frappe.get_cached_value("Fuel Tank Master", row.tank, "warehouse"),
				"cost_center": cost_center,
			})
		pi.set_missing_values()
		for row, src in zip(pi.items, self.items):
			row.rate = src.rate
		pi.calculate_taxes_and_totals()
		pi.flags.ignore_permissions = True
		pi.insert()
		pi.submit()
		self.db_set("purchase_invoice", pi.name)

	def make_transit_adjustment(self):
		rows = [r for r in self.items if abs(flt(r.shortage_qty)) >= 0.01]
		if not rows:
			return
		shortages = [r for r in rows if r.shortage_qty > 0]
		excesses = [r for r in rows if r.shortage_qty < 0]
		account = frappe.get_cached_value("Company", self.company, "stock_adjustment_account")
		cost_center = frappe.get_cached_value("Fuel Station", self.station, "cost_center")
		names = []
		for purpose, group in (("Material Issue", shortages), ("Material Receipt", excesses)):
			if not group:
				continue
			se = frappe.new_doc("Stock Entry")
			se.update({
				"stock_entry_type": purpose,
				"purpose": purpose,
				"company": self.company,
				"posting_date": self.posting_date,
				"set_posting_time": 1,
				"posting_time": self.posting_time,
				"tanker_receipt": self.name,
				"remarks": _("Decantation {0} for tanker {1} ({2})").format(
					_("shortage") if purpose == "Material Issue" else _("excess"), self.truck_no, self.name),
			})
			for r in group:
				wh = frappe.get_cached_value("Fuel Tank Master", r.tank, "warehouse")
				se.append("items", {
					"item_code": r.fuel_item,
					"qty": abs(r.shortage_qty),
					"s_warehouse": wh if purpose == "Material Issue" else None,
					"t_warehouse": wh if purpose == "Material Receipt" else None,
					"basic_rate": r.rate,
					"expense_account": account,
					"cost_center": cost_center,
				})
			se.flags.ignore_permissions = True
			se.insert()
			se.submit()
			names.append(se.name)
		# the link field holds one entry; a receipt with both short and excess rows keeps the first
		self.db_set("adjustment_entry", names[0])
		if len(names) > 1:
			self.add_comment("Info", _("Transit adjustment entries: {0}").format(", ".join(names)))
