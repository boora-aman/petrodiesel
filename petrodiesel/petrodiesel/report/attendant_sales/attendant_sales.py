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
			"label": _("Attendant"),
			"fieldname": "attendant",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{"label": _("Name"), "fieldname": "attendant_name", "fieldtype": "Data", "width": 150},
		{"label": _("Shifts"), "fieldname": "shifts", "fieldtype": "Int", "width": 80},
		{"label": _("Litres Sold"), "fieldname": "qty", "fieldtype": "Float", "width": 120},
		{"label": _("Sales Value"), "fieldname": "amount", "fieldtype": "Currency", "width": 140},
		{"label": _("Avg L / Shift"), "fieldname": "avg", "fieldtype": "Float", "width": 120},
	]
	cond = _station_cond(filters)
	data = frappe.db.sql(
		f"""select n.attendant, n.attendant_name, count(distinct s.name) shifts,
		sum(n.sale_qty) qty, sum(n.amount) amount
		from `tabShift Nozzle Reading` n join `tabShift Sale Entry` s on s.name = n.parent
		where s.docstatus = 1 and ifnull(n.attendant, '') != '' and s.posting_date between %(from_date)s and %(to_date)s {cond}
		group by n.attendant, n.attendant_name order by qty desc""",
		filters,
		as_dict=True,
	)
	for d in data:
		d["avg"] = flt(d.qty / d.shifts, 1) if d.shifts else 0
	return columns, data
