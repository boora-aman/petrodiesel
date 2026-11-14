# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Shared helpers for fuel retail operations."""

from __future__ import annotations

import itertools

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate


def get_settings():
	return frappe.get_cached_doc("Petrodiesel Settings")


# ------------------------------------------------------------------ tank calibration
def dip_to_volume(tank: str, dip_mm: float) -> float:
	"""Convert a dip (mm) to litres using the tank calibration chart (linear interpolation)."""
	dip_mm = flt(dip_mm)
	if dip_mm <= 0:
		return 0.0
	rows = frappe.get_all(
		"Tank Calibration Chart",
		filters={"parent": tank, "parenttype": "Fuel Tank Master"},
		fields=["dip_mm", "volume_liters"],
		order_by="dip_mm asc",
	)
	if not rows:
		frappe.throw(_("Tank {0} has no calibration chart. Add dip-to-volume rows on the tank.").format(tank))
	points = [(flt(r.dip_mm), flt(r.volume_liters)) for r in rows]
	if dip_mm <= points[0][0]:
		d0, v0 = points[0]
		return flt(v0 * dip_mm / d0, 2) if d0 else flt(v0, 2)
	for (d1, v1), (d2, v2) in itertools.pairwise(points):
		if d1 <= dip_mm <= d2:
			if d2 == d1:
				return flt(v2, 2)
			return flt(v1 + (v2 - v1) * (dip_mm - d1) / (d2 - d1), 2)
	# above chart: cap at last point
	return flt(points[-1][1], 2)


@frappe.whitelist()
def get_dip_volume(tank: str, dip_mm: float, water_dip_mm: float = 0) -> dict:
	frappe.has_permission("Fuel Tank Master", "read", tank, throw=True)
	gross = dip_to_volume(tank, dip_mm)
	water = dip_to_volume(tank, water_dip_mm) if flt(water_dip_mm) > 0 else 0
	return {"gross": gross, "water": water, "net": flt(gross - water, 2)}


# ------------------------------------------------------------------ stock
def get_tank_book_stock(tank: str, posting_date=None, posting_time=None) -> float:
	"""ERPNext book stock (litres) of the tank's warehouse, optionally as on a date/time."""
	warehouse, item = frappe.db.get_value("Fuel Tank Master", tank, ["warehouse", "fuel_item"])
	if not warehouse or not item:
		return 0.0
	if not posting_date:
		return flt(frappe.db.get_value("Bin", {"warehouse": warehouse, "item_code": item}, "actual_qty"))
	from erpnext.stock.utils import get_stock_balance

	return flt(get_stock_balance(item, warehouse, posting_date, posting_time or "23:59:59"))


# ------------------------------------------------------------------ prices
def get_fuel_rate(item_code: str, posting_date=None, price_list: str | None = None) -> float:
	"""Retail rate for an item on a date from dated Item Prices in the fuel price list."""
	if not item_code:
		return 0.0
	posting_date = getdate(posting_date or nowdate())
	price_list = price_list or get_settings().fuel_price_list or "Standard Selling"
	ip = frappe.qb.DocType("Item Price")
	rows = (
		frappe.qb.from_(ip)
		.select(ip.price_list_rate)
		.where(
			(ip.item_code == item_code)
			& (ip.price_list == price_list)
			& ((ip.valid_from.isnull()) | (ip.valid_from <= posting_date))
			& ((ip.valid_upto.isnull()) | (ip.valid_upto >= posting_date))
		)
		.orderby(ip.valid_from, order=frappe.qb.desc)
		.limit(1)
		.run()
	)
	if rows:
		return flt(rows[0][0])
	return flt(frappe.db.get_value("Item", item_code, "standard_rate"))


@frappe.whitelist()
def get_rate(item_code: str, posting_date: str | None = None) -> float:
	return get_fuel_rate(item_code, posting_date)


# ------------------------------------------------------------------ accounts
def get_mode_of_payment_account(mode_of_payment: str, company: str) -> str:
	account = frappe.db.get_value(
		"Mode of Payment Account",
		{"parent": mode_of_payment, "company": company},
		"default_account",
	)
	if not account:
		frappe.throw(
			_("Set the default account for Mode of Payment {0} for company {1}.").format(
				frappe.bold(mode_of_payment), company
			)
		)
	return account


def get_company_default(company: str, field: str) -> str | None:
	return frappe.get_cached_value("Company", company, field)


def is_fuel_item(item_code: str) -> bool:
	return frappe.get_cached_value("Item", item_code, "petro_product_type") == "Fuel"
