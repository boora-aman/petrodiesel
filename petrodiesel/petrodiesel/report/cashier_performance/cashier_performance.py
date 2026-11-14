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
			"label": _("Cashier"),
			"fieldname": "cashier",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 110,
		},
		{"label": _("Cashier Name"), "fieldname": "cashier_name", "fieldtype": "Data", "width": 150},
		{"label": _("Shifts"), "fieldname": "shifts", "fieldtype": "Int", "width": 70},
		{"label": _("Litres"), "fieldname": "litres", "fieldtype": "Float", "width": 110},
		{"label": _("Gross Sales"), "fieldname": "gross", "fieldtype": "Currency", "width": 130},
		{"label": _("Digital"), "fieldname": "digital", "fieldtype": "Currency", "width": 120},
		{"label": _("Cash Counted"), "fieldname": "cash", "fieldtype": "Currency", "width": 130},
		{"label": _("Total Short"), "fieldname": "total_short", "fieldtype": "Currency", "width": 110},
		{"label": _("Total Excess"), "fieldname": "total_excess", "fieldtype": "Currency", "width": 110},
		{
			"label": _("Net Short / Excess"),
			"fieldname": "net_short_excess",
			"fieldtype": "Currency",
			"width": 130,
		},
		{"label": _("Avg Short / Shift"), "fieldname": "avg_short", "fieldtype": "Currency", "width": 120},
		{
			"label": _("Worst Shift"),
			"fieldname": "worst_shift",
			"fieldtype": "Link",
			"options": "Shift Sale Entry",
			"width": 150,
		},
	]
	cond = _station_cond(filters)
	data = frappe.db.sql(
		f"""
		select s.cashier, max(s.cashier_name) cashier_name, count(*) shifts, sum(s.total_sale_qty) litres,
			sum(s.gross_sales) gross, sum(s.digital_amount) digital, sum(s.cash_counted) cash,
			sum(case when s.short_excess < 0 then s.short_excess else 0 end) total_short,
			sum(case when s.short_excess > 0 then s.short_excess else 0 end) total_excess,
			sum(s.short_excess) net_short_excess
		from `tabShift Sale Entry` s
		where s.docstatus = 1 and s.posting_date between %(from_date)s and %(to_date)s {cond}
		group by s.cashier order by sum(s.short_excess)""",
		filters,
		as_dict=True,
	)
	worst = {}
	for r in frappe.db.sql(
		f"""
		select s.cashier, s.name, s.short_excess from `tabShift Sale Entry` s
		where s.docstatus = 1 and s.short_excess < 0 and s.posting_date between %(from_date)s and %(to_date)s {cond}
		order by s.short_excess desc""",
		filters,
		as_dict=True,
	):
		worst[r.cashier] = r.name
	for d in data:
		d["avg_short"] = flt(d.total_short) / d.shifts if d.shifts else 0
		d["worst_shift"] = worst.get(d.cashier)
	chart = {
		"data": {
			"labels": [d.cashier_name or d.cashier or _("Not Set") for d in data],
			"datasets": [
				{"name": _("Net Short / Excess"), "values": [flt(d.net_short_excess, 2) for d in data]}
			],
		},
		"type": "bar",
		"fieldtype": "Currency",
	}
	return columns, data, None, chart
