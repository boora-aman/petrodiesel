# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = [
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{"label": _("Shift"), "fieldname": "shift", "fieldtype": "Data", "width": 80},
		{
			"label": _("Entry"),
			"fieldname": "entry",
			"fieldtype": "Link",
			"options": "Shift Sale Entry",
			"width": 150,
		},
		{"label": _("Attendant"), "fieldname": "attendant_name", "fieldtype": "Data", "width": 140},
		{"label": _("Nozzles"), "fieldname": "nozzles", "fieldtype": "Data", "width": 140},
		{"label": _("Sale (L)"), "fieldname": "sale_qty", "fieldtype": "Float", "width": 90},
		{"label": _("Sale Value"), "fieldname": "sale_amount", "fieldtype": "Currency", "width": 120},
		{"label": _("Credit Slips"), "fieldname": "credit_amount", "fieldtype": "Currency", "width": 110},
		{
			"label": _("UPI / Card / Fleet"),
			"fieldname": "digital_amount",
			"fieldtype": "Currency",
			"width": 120,
		},
		{"label": _("Cash Due"), "fieldname": "expected_cash", "fieldtype": "Currency", "width": 120},
		{"label": _("Cash Handed"), "fieldname": "cash_handed", "fieldtype": "Currency", "width": 120},
		{"label": _("Short / Excess"), "fieldname": "short_excess", "fieldtype": "Currency", "width": 110},
	]
	cond = " and s.station = %(station)s" if filters.station else ""
	if filters.attendant:
		cond += " and a.attendant = %(attendant)s"
	data = frappe.db.sql(
		f"""select s.posting_date, s.shift, s.name entry, a.attendant_name, a.nozzles, a.sale_qty, a.sale_amount,
			a.credit_amount, a.digital_amount, a.expected_cash, a.cash_handed, a.short_excess
		from `tabShift Attendant Collection` a join `tabShift Sale Entry` s on s.name = a.parent
		left join `tabShift Master` sm on sm.name = s.shift
		where s.docstatus = 1 and s.posting_date between %(from_date)s and %(to_date)s {cond}
		order by s.posting_date, sm.sequence, a.attendant_name""",
		filters,
		as_dict=True,
	)
	per = {}
	for d in data:
		per[d.attendant_name] = per.get(d.attendant_name, 0) + flt(d.short_excess)
	chart = {
		"data": {
			"labels": list(per),
			"datasets": [{"name": _("Net short / excess"), "values": [flt(v, 2) for v in per.values()]}],
		},
		"type": "bar",
		"fieldtype": "Currency",
	}
	return columns, data, None, chart
