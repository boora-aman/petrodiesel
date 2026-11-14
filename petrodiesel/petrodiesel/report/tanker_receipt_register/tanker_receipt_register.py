# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def _station_cond(filters, alias="s"):
	return f" and {alias}.station = %(station)s" if filters.get("station") else ""


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = [
		{
			"label": _("Receipt"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Tanker Receipt",
			"width": 130,
		},
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{"label": _("Tank Lorry"), "fieldname": "truck_no", "fieldtype": "Data", "width": 100},
		{"label": _("OMC Invoice"), "fieldname": "supplier_invoice_no", "fieldtype": "Data", "width": 130},
		{
			"label": _("Tank"),
			"fieldname": "tank",
			"fieldtype": "Link",
			"options": "Fuel Tank Master",
			"width": 90,
		},
		{"label": _("Fuel"), "fieldname": "fuel_item", "fieldtype": "Link", "options": "Item", "width": 70},
		{"label": _("Invoice Qty"), "fieldname": "invoice_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Received"), "fieldname": "received_qty", "fieldtype": "Float", "width": 100},
		{
			"label": _("Short (+) / Excess (-)"),
			"fieldname": "shortage_qty",
			"fieldtype": "Float",
			"width": 130,
		},
		{"label": _("Challan Density"), "fieldname": "challan_density", "fieldtype": "Float", "width": 110},
		{"label": _("Density @15"), "fieldname": "density_at_15", "fieldtype": "Float", "width": 100},
		{"label": _("Variance"), "fieldname": "density_variance", "fieldtype": "Float", "width": 80},
		{"label": _("Density OK"), "fieldname": "density_ok", "fieldtype": "Check", "width": 80},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
		{
			"label": _("Purchase Invoice"),
			"fieldname": "purchase_invoice",
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 150,
		},
	]
	cond = _station_cond(filters, "t")
	if filters.supplier:
		cond += " and t.supplier = %(supplier)s"
	data = frappe.db.sql(
		f"""
		select t.name, t.posting_date, t.truck_no, t.supplier_invoice_no, i.tank, i.fuel_item, i.invoice_qty,
			i.received_qty, i.shortage_qty, i.challan_density, i.density_at_15, i.density_variance, i.density_ok,
			i.amount, t.purchase_invoice
		from `tabTanker Receipt Item` i join `tabTanker Receipt` t on t.name = i.parent
		where t.docstatus = 1 and t.posting_date between %(from_date)s and %(to_date)s {cond}
		order by t.posting_date, t.name""",
		filters,
		as_dict=True,
	)
	return columns, data
