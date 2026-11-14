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
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": _("Tank"), "fieldname": "tank", "fieldtype": "Link", "options": "Fuel Tank Master", "width": 110},
		{"label": _("Fuel"), "fieldname": "fuel_item", "fieldtype": "Link", "options": "Item", "width": 90},
		{"label": _("Opening"), "fieldname": "opening_stock", "fieldtype": "Float", "width": 110},
		{"label": _("Receipts"), "fieldname": "receipts", "fieldtype": "Float", "width": 110},
		{"label": _("Net Sales"), "fieldname": "net_sales", "fieldtype": "Float", "width": 110},
		{"label": _("Book Closing"), "fieldname": "book_closing", "fieldtype": "Float", "width": 120},
		{"label": _("Dip Closing"), "fieldname": "closing_stock", "fieldtype": "Float", "width": 120},
		{"label": _("Gain / Loss"), "fieldname": "variance", "fieldtype": "Float", "width": 100},
		{"label": _("DSR"), "fieldname": "dsr", "fieldtype": "Link", "options": "Daily Stock Register", "width": 140},
	]
	cond = _station_cond(filters, "d")
	if filters.tank:
		cond += " and i.tank = %(tank)s"
	data = frappe.db.sql(f"""
		select d.posting_date, i.tank, i.fuel_item, i.opening_stock, i.receipts, i.net_sales,
			i.book_closing, i.closing_stock, i.variance, d.name dsr
		from `tabDaily Stock Register Item` i join `tabDaily Stock Register` d on d.name = i.parent
		where d.docstatus = 1 and d.posting_date between %(from_date)s and %(to_date)s {cond}
		order by d.posting_date, i.tank""", filters, as_dict=True)
	dates = sorted({str(d.posting_date) for d in data})
	tanks = sorted({d.tank for d in data})
	closing = {(str(d.posting_date), d.tank): flt(d.closing_stock, 2) for d in data}
	chart = {
		"data": {"labels": [frappe.format(d, "Date") for d in dates],
			"datasets": [{"name": t, "values": [closing.get((dt, t), 0) for dt in dates]} for t in tanks]},
		"type": "line", "fieldtype": "Float",
	}
	return columns, data, None, chart
