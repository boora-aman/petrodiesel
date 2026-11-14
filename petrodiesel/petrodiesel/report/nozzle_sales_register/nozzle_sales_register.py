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
		{"label": _("Shift"), "fieldname": "shift", "fieldtype": "Link", "options": "Shift Master", "width": 85},
		{"label": _("Entry"), "fieldname": "entry", "fieldtype": "Link", "options": "Shift Sale Entry", "width": 150},
		{"label": _("Nozzle"), "fieldname": "nozzle", "fieldtype": "Link", "options": "Fuel Nozzle Master", "width": 85},
		{"label": _("Fuel"), "fieldname": "fuel_item", "fieldtype": "Link", "options": "Item", "width": 70},
		{"label": _("Attendant"), "fieldname": "attendant_name", "fieldtype": "Data", "width": 120},
		{"label": _("Opening"), "fieldname": "opening_reading", "fieldtype": "Float", "width": 110},
		{"label": _("Closing"), "fieldname": "closing_reading", "fieldtype": "Float", "width": 110},
		{"label": _("Meter Qty"), "fieldname": "meter_qty", "fieldtype": "Float", "width": 90},
		{"label": _("Test"), "fieldname": "test_qty", "fieldtype": "Float", "width": 60},
		{"label": _("Sale Qty"), "fieldname": "sale_qty", "fieldtype": "Float", "width": 90},
		{"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 80},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
	]
	cond = _station_cond(filters)
	if filters.nozzle:
		cond += " and n.nozzle = %(nozzle)s"
	if filters.fuel_item:
		cond += " and n.fuel_item = %(fuel_item)s"
	data = frappe.db.sql(f"""
		select s.posting_date, s.shift, s.name entry, n.nozzle, n.fuel_item, n.attendant_name,
			n.opening_reading, n.closing_reading, n.meter_qty, n.test_qty, n.sale_qty, n.rate, n.amount
		from `tabShift Nozzle Reading` n join `tabShift Sale Entry` s on s.name = n.parent
		left join `tabShift Master` sm on sm.name = s.shift
		where s.docstatus = 1 and s.posting_date between %(from_date)s and %(to_date)s {cond}
		order by s.posting_date, sm.sequence, n.nozzle, n.opening_reading""", filters, as_dict=True)
	return columns, data
