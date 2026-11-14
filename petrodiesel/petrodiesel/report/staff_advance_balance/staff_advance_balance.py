# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

from petrodiesel.petrodiesel.advances import advance_ledger


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if filters.employee:
		columns = [
			{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
			{"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 160},
			{"label": _("Voucher"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 170},
			{"label": _("Given"), "fieldname": "given", "fieldtype": "Currency", "width": 120},
			{"label": _("Recovered"), "fieldname": "recovered", "fieldtype": "Currency", "width": 120},
			{"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 130},
			{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 220},
		]
		bal = 0.0
		rows = advance_ledger(filters.employee, filters.to_date)
		for r in rows:
			bal += flt(r.given) - flt(r.recovered)
			r["balance"] = flt(bal, 2)
		return columns, rows
	columns = [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 170},
		{"label": _("Advances Given"), "fieldname": "given", "fieldtype": "Currency", "width": 140},
		{"label": _("Recovered"), "fieldname": "recovered", "fieldtype": "Currency", "width": 130},
		{"label": _("Balance Due"), "fieldname": "balance", "fieldtype": "Currency", "width": 140},
		{"label": _("Last Entry"), "fieldname": "last_date", "fieldtype": "Date", "width": 110},
	]
	out = {}
	for r in advance_ledger(None, filters.to_date):
		e = out.setdefault(r.employee, frappe._dict(employee=r.employee, employee_name=r.employee_name, given=0, recovered=0))
		e.given += flt(r.given)
		e.recovered += flt(r.recovered)
		e.last_date = r.posting_date
	data = sorted(out.values(), key=lambda x: -(x.given - x.recovered))
	for d in data:
		d.balance = flt(d.given - d.recovered, 2)
	chart = {"data": {"labels": [d.employee_name for d in data], "datasets": [{"name": _("Balance"), "values": [d.balance for d in data]}]},
		"type": "bar", "fieldtype": "Currency"}
	return columns, data, None, chart
