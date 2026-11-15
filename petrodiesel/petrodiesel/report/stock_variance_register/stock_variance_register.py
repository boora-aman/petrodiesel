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
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{
			"label": _("DSR"),
			"fieldname": "dsr",
			"fieldtype": "Link",
			"options": "Daily Stock Register",
			"width": 140,
		},
		{
			"label": _("Tank"),
			"fieldname": "tank",
			"fieldtype": "Link",
			"options": "Fuel Tank Master",
			"width": 90,
		},
		{"label": _("Fuel"), "fieldname": "fuel_item", "fieldtype": "Link", "options": "Item", "width": 70},
		{"label": _("Opening"), "fieldname": "opening_stock", "fieldtype": "Float", "width": 100},
		{"label": _("Receipts"), "fieldname": "receipts", "fieldtype": "Float", "width": 100},
		{"label": _("Net Sales"), "fieldname": "net_sales", "fieldtype": "Float", "width": 100},
		{"label": _("Book Closing"), "fieldname": "book_closing", "fieldtype": "Float", "width": 110},
		{"label": _("Dip Closing"), "fieldname": "closing_stock", "fieldtype": "Float", "width": 110},
		{"label": _("Gain / Loss"), "fieldname": "variance", "fieldtype": "Float", "width": 100},
		{"label": _("% of Sales"), "fieldname": "variance_percent", "fieldtype": "Percent", "width": 90},
		{"label": _("Allowed %"), "fieldname": "permissible_percent", "fieldtype": "Percent", "width": 90},
		{"label": _("Within Limit"), "fieldname": "within_limit", "fieldtype": "Check", "width": 90},
		{
			"label": _("MTD Gain / Loss"),
			"fieldname": "cumulative_variance",
			"fieldtype": "Float",
			"width": 110,
		},
		{"label": _("Density @15"), "fieldname": "density_at_15", "fieldtype": "Float", "width": 90},
	]
	cond = _station_cond(filters, "d")
	if filters.tank:
		cond += " and i.tank = %(tank)s"
	data = frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
		f"""
		select d.posting_date, d.name dsr, i.tank, i.fuel_item, i.opening_stock, i.receipts, i.net_sales,
			i.book_closing, i.closing_stock, i.variance, i.variance_percent, i.permissible_percent,
			i.within_limit, i.cumulative_variance, i.density_at_15
		from `tabDaily Stock Register Item` i join `tabDaily Stock Register` d on d.name = i.parent
		where d.docstatus = 1 and d.posting_date between %(from_date)s and %(to_date)s {cond}
		order by d.posting_date, i.tank""",
		filters,
		as_dict=True,
	)
	return columns, data
