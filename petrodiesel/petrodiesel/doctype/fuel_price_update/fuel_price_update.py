# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Fuel Price Update: daily dynamic OMC prices kept as dated Item Prices."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, getdate

from petrodiesel.petrodiesel.utils import get_fuel_rate, get_settings


class FuelPriceUpdate(Document):
	def validate(self):
		if not self.price_list:
			self.price_list = get_settings().fuel_price_list
		seen = set()
		for row in self.items:
			if row.fuel_item in seen:
				frappe.throw(_("{0} is listed twice.").format(row.fuel_item))
			seen.add(row.fuel_item)
			if flt(row.new_price) <= 0:
				frappe.throw(_("Row {0}: new price must be positive.").format(row.idx))
			row.old_price = get_fuel_rate(row.fuel_item, add_days(self.effective_date, -1), self.price_list)
			row.change_amount = flt(flt(row.new_price) - flt(row.old_price), 2)
			row.change_percent = flt(row.change_amount * 100 / row.old_price, 2) if flt(row.old_price) else 0

	def on_submit(self):
		date = getdate(self.effective_date)
		for row in self.items:
			uom = frappe.db.get_value("Item", row.fuel_item, "stock_uom")
			# close the price that is valid on the effective date
			prev = frappe.db.sql("""
				select name, valid_from from `tabItem Price`
				where item_code=%s and price_list=%s and (valid_from is null or valid_from <= %s)
				and (valid_upto is null or valid_upto >= %s)
				order by valid_from desc limit 1""", (row.fuel_item, self.price_list, date, date), as_dict=True)
			if prev:
				p = prev[0]
				if p.valid_from and getdate(p.valid_from) == date:
					frappe.throw(_("{0} already has a price from {1} ({2}). Cancel that update first.").format(
						row.fuel_item, date, p.name))
				frappe.db.set_value("Item Price", p.name, "valid_upto", add_days(date, -1))
				row.db_set("previous_item_price", p.name)
			later = frappe.db.get_value("Item Price", {"item_code": row.fuel_item, "price_list": self.price_list,
				"valid_from": [">", date]}, "valid_from", order_by="valid_from asc")
			ip = frappe.get_doc({
				"doctype": "Item Price",
				"item_code": row.fuel_item,
				"price_list": self.price_list,
				"uom": uom,
				"price_list_rate": row.new_price,
				"valid_from": date,
				"valid_upto": add_days(later, -1) if later else None,
				"note": _("Fuel Price Update {0}").format(self.name),
			})
			ip.flags.ignore_permissions = True
			ip.insert()
			row.db_set("item_price", ip.name)
			frappe.db.set_value("Item", row.fuel_item, "standard_rate", row.new_price, update_modified=False)

	def on_cancel(self):
		for row in self.items:
			if row.item_price and frappe.db.exists("Item Price", row.item_price):
				upto = frappe.db.get_value("Item Price", row.item_price, "valid_upto")
				frappe.delete_doc("Item Price", row.item_price, ignore_permissions=True, force=True)
				if row.previous_item_price and frappe.db.exists("Item Price", row.previous_item_price):
					frappe.db.set_value("Item Price", row.previous_item_price, "valid_upto", upto)
				row.db_set("item_price", None)


@frappe.whitelist()
def get_fuel_items(effective_date: str | None = None, price_list: str | None = None) -> list[dict]:
	items = frappe.get_all("Item", {"petro_product_type": "Fuel", "disabled": 0}, pluck="name", order_by="name")
	return [{"fuel_item": i, "old_price": get_fuel_rate(i, add_days(effective_date or frappe.utils.today(), -1), price_list)}
		for i in items]
