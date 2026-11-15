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
			"label": _("Expense Account"),
			"fieldname": "expense_account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 220,
		},
		{"label": _("Entries"), "fieldname": "count", "fieldtype": "Int", "width": 80},
		{"label": _("Total"), "fieldname": "total", "fieldtype": "Currency", "width": 130},
		{"label": _("% of Total"), "fieldname": "percent", "fieldtype": "Percent", "width": 100},
		{"label": _("Average"), "fieldname": "average", "fieldtype": "Currency", "width": 120},
	]
	cond = _station_cond(filters)
	if filters.expense_account:
		cond += " and e.expense_account = %(expense_account)s"
	data = frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
		f"""
		select e.expense_account, count(*) count, sum(e.amount) total, avg(e.amount) average
		from `tabShift Expense Detail` e join `tabShift Sale Entry` s on s.name = e.parent
		where s.docstatus = 1 and e.parenttype = 'Shift Sale Entry'
			and s.posting_date between %(from_date)s and %(to_date)s {cond}
		group by e.expense_account order by sum(e.amount) desc""",
		filters,
		as_dict=True,
	)
	grand = sum(flt(d.total) for d in data)
	for d in data:
		d["percent"] = flt(d.total) * 100 / grand if grand else 0
	chart = {
		"data": {
			"labels": [d.expense_account for d in data],
			"datasets": [{"values": [flt(d.total, 2) for d in data]}],
		},
		"type": "donut",
		"fieldtype": "Currency",
	}
	return columns, data, None, chart
