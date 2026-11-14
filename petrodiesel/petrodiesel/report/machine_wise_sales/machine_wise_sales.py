# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = [
		{
			"label": _("Machine"),
			"fieldname": "dispensing_unit",
			"fieldtype": "Link",
			"options": "Dispensing Unit",
			"width": 90,
		},
		{"label": _("Side"), "fieldname": "side", "fieldtype": "Data", "width": 60},
		{"label": _("Fuel"), "fieldname": "fuel_item", "fieldtype": "Link", "options": "Item", "width": 80},
		{
			"label": _("Nozzle"),
			"fieldname": "nozzle",
			"fieldtype": "Link",
			"options": "Fuel Nozzle Master",
			"width": 90,
		},
		{"label": _("Shifts"), "fieldname": "shifts", "fieldtype": "Int", "width": 70},
		{"label": _("Meter (L)"), "fieldname": "meter_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Test (L)"), "fieldname": "test_qty", "fieldtype": "Float", "width": 90},
		{"label": _("Sale (L)"), "fieldname": "sale_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Sale Value"), "fieldname": "amount", "fieldtype": "Currency", "width": 130},
		{"label": _("Avg L / Shift"), "fieldname": "avg", "fieldtype": "Float", "width": 110},
	]
	cond = " and s.station = %(station)s" if filters.station else ""
	if filters.dispensing_unit:
		cond += " and nz.dispensing_unit = %(dispensing_unit)s"
	data = frappe.db.sql(
		f"""select nz.dispensing_unit, nz.side, n.fuel_item, n.nozzle, count(distinct s.name) shifts,
			sum(n.meter_qty) meter_qty, sum(n.test_qty) test_qty, sum(n.sale_qty) sale_qty, sum(n.amount) amount
		from `tabShift Nozzle Reading` n join `tabShift Sale Entry` s on s.name = n.parent
		join `tabFuel Nozzle Master` nz on nz.name = n.nozzle
		where s.docstatus = 1 and s.posting_date between %(from_date)s and %(to_date)s {cond}
		group by nz.dispensing_unit, nz.side, n.fuel_item, n.nozzle order by nz.dispensing_unit, nz.side, n.nozzle""",
		filters,
		as_dict=True,
	)
	per = {}
	for d in data:
		d.avg = flt(d.sale_qty / d.shifts, 1) if d.shifts else 0
		per[f"{d.dispensing_unit} {d.side or ''}".strip()] = per.get(
			f"{d.dispensing_unit} {d.side or ''}".strip(), 0
		) + flt(d.sale_qty)
	chart = {
		"data": {
			"labels": list(per),
			"datasets": [{"name": _("Litres"), "values": [flt(v, 0) for v in per.values()]}],
		},
		"type": "bar",
		"fieldtype": "Float",
	}
	return columns, data, None, chart
