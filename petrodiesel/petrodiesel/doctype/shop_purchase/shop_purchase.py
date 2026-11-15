# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Shop Purchase: lubricant / accessory purchase into the shop store (posts a Purchase Invoice)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class ShopPurchase(Document):
	ignore_linked_doctypes = (
		"GL Entry",
		"Stock Ledger Entry",
		"Payment Ledger Entry",
		"Purchase Invoice",
		"Repost Item Valuation",
		"Serial and Batch Bundle",
	)

	def validate(self):
		self.company = frappe.get_cached_value("Fuel Station", self.station, "company")
		if not self.warehouse:
			self.warehouse = frappe.get_cached_value("Fuel Station", self.station, "lube_warehouse")
		for r in self.items:
			if frappe.get_cached_value("Item", r.item_code, "petro_product_type") == "Fuel":
				frappe.throw(
					_("Row {0}: fuel is received through Tanker Receipt, not Shop Purchase.").format(r.idx)
				)
			r.amount = flt(flt(r.qty) * flt(r.rate), 2)
		self.total_qty = flt(sum(flt(r.qty) for r in self.items), 2)
		self.total_amount = flt(sum(flt(r.amount) for r in self.items), 2)

	def on_submit(self):
		cc = frappe.get_cached_value("Fuel Station", self.station, "cost_center")
		pi = frappe.new_doc("Purchase Invoice")
		pi.update(
			{
				"company": self.company,
				"supplier": self.supplier,
				"posting_date": self.posting_date,
				"set_posting_time": 1,
				"bill_no": self.bill_no,
				"bill_date": self.bill_date or self.posting_date,
				"due_date": self.posting_date,
				"update_stock": 1,
				"cost_center": cc,
				"disable_rounded_total": 1,
				"remarks": _("Shop purchase {0}").format(self.name),
			}
		)
		for r in self.items:
			pi.append(
				"items",
				{
					"item_code": r.item_code,
					"qty": r.qty,
					"rate": r.rate,
					"price_list_rate": r.rate,
					"warehouse": self.warehouse,
					"cost_center": cc,
				},
			)
		pi.set_missing_values()
		pi.taxes_and_charges = None
		pi.set("taxes", [])
		if self.taxes_and_charges:
			pi.taxes_and_charges = self.taxes_and_charges
			pi.set("taxes", [])
			for t in frappe.get_doc("Purchase Taxes and Charges Template", self.taxes_and_charges).taxes:
				pi.append(
					"taxes",
					{
						k: t.get(k)
						for k in (
							"charge_type",
							"account_head",
							"rate",
							"description",
							"included_in_print_rate",
							"cost_center",
							"category",
							"add_deduct_tax",
						)
					},
				)
		for row, src in zip(pi.items, self.items, strict=False):
			row.rate = src.rate
		pi.calculate_taxes_and_totals()
		pi.flags.ignore_permissions = True
		pi.insert()
		pi.submit()
		self.db_set("purchase_invoice", pi.name)

	def on_cancel(self):
		if (
			self.purchase_invoice
			and frappe.db.get_value("Purchase Invoice", self.purchase_invoice, "docstatus") == 1
		):
			pi = frappe.get_doc("Purchase Invoice", self.purchase_invoice)
			pi.flags.ignore_permissions = True
			pi.cancel()
