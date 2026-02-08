# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe


def get_item_price(item_code: str, price_list: str | None = None) -> float:
	"""Get item price from Item Price or fallback to Item standard rate."""
	if not item_code:
		return 0

	filters = {"item_code": item_code}
	if price_list:
		filters["price_list"] = price_list

	price = frappe.db.get_value("Item Price", filters=filters, fieldname="price_list_rate")
	if price:
		return price

	return frappe.db.get_value("Item", item_code, "standard_rate") or 0


def get_latest_fuel_price(fuel_item: str, posting_date: str | None = None) -> float:
	"""Resolve latest fuel price from Fuel Price Update with fallbacks."""
	if not fuel_item:
		return 0

	if not posting_date:
		posting_date = frappe.utils.today()

	price_update = frappe.get_all(
		"Fuel Price Update",
		filters={"docstatus": 1, "effective_date": ["<=", posting_date]},
		order_by="effective_date desc, effective_time desc",
		limit=1,
	)

	if price_update:
		price = frappe.db.get_value(
			"Fuel Price Update Item",
			filters={"parent": price_update[0].name, "fuel_item": fuel_item},
			fieldname="new_price",
		)
		if price:
			return price

	# Prefer retail price list if configured
	price = get_item_price(fuel_item, "Retail Fuel Prices")
	if price:
		return price

	return get_item_price(fuel_item)


def get_customer_total_outstanding(customer: str) -> float:
	"""
	Get total outstanding for customer.
	
	SINGLE SOURCE OF TRUTH: Only count Credit Sale documents.
	Credit Sales are auto-created from:
	- Shift Sale Entry (on submit)
	- Cashier Wise Shift Sale Entry (on submit)
	- Direct Credit Sale entry
	
	This prevents duplicate counting.
	"""
	if not customer:
		return 0

	# Get total outstanding from Credit Sale documents only
	outstanding = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(outstanding_amount), 0)
		FROM `tabCredit Sale`
		WHERE customer = %s
		AND docstatus = 1
		""",
		(customer,),
	)

	return outstanding[0][0] if outstanding else 0


def update_customer_balance(customer: str) -> float:
	"""Update customer custom fields with latest outstanding balance."""
	if not customer:
		return 0
	
	outstanding = get_customer_total_outstanding(customer)
	
	# Update Customer master custom fields if they exist
	try:
		if frappe.db.exists('Customer', customer):
			frappe.db.set_value('Customer', customer, 'custom_credit_balance', outstanding, update_modified=False)
	except Exception as e:
		frappe.log_error(f"Could not update customer balance: {str(e)}")
	
	return outstanding
