# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def _station_cond(filters, alias="s"):
	return f" and {alias}.station = %(station)s" if filters.get("station") else ""


def execute(filters=None):
	filters = frappe._dict(filters or {})
	cond = _station_cond(filters)
	modes = [
		m[0]
		for m in frappe.db.sql(
			f"""select distinct p.mode_of_payment from `tabShift Payment` p
		join `tabShift Sale Entry` s on s.name = p.parent where s.docstatus = 1
		and s.posting_date between %(from_date)s and %(to_date)s {cond} order by 1""",
			filters,
		)
	]
	columns = [
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": _("Cash"), "fieldname": "cash", "fieldtype": "Currency", "width": 130},
	]
	columns += [
		{"label": m, "fieldname": frappe.scrub(m), "fieldtype": "Currency", "width": 130} for m in modes
	]
	columns += [
		{"label": _("Credit Sales"), "fieldname": "credit", "fieldtype": "Currency", "width": 130},
		{"label": _("Total"), "fieldname": "total", "fieldtype": "Currency", "width": 140},
	]
	base = {
		str(r.posting_date): r
		for r in frappe.db.sql(
			f"""
		select s.posting_date, sum(s.cash_counted) cash, sum(s.credit_sales_amount) credit
		from `tabShift Sale Entry` s where s.docstatus = 1 and s.posting_date between %(from_date)s and %(to_date)s {cond}
		group by s.posting_date order by s.posting_date""",
			filters,
			as_dict=True,
		)
	}
	for r in frappe.db.sql(
		f"""select s.posting_date, p.mode_of_payment, sum(p.amount) amt from `tabShift Payment` p
		join `tabShift Sale Entry` s on s.name = p.parent where s.docstatus = 1
		and s.posting_date between %(from_date)s and %(to_date)s {cond}
		group by s.posting_date, p.mode_of_payment""",
		filters,
		as_dict=True,
	):
		base[str(r.posting_date)][frappe.scrub(r.mode_of_payment)] = r.amt
	data = list(base.values())
	for d in data:
		d["total"] = flt(d.cash) + flt(d.credit) + sum(flt(d.get(frappe.scrub(m))) for m in modes)
	totals = {"Cash": sum(flt(d.cash) for d in data), "Credit": sum(flt(d.credit) for d in data)}
	for m in modes:
		totals[m] = sum(flt(d.get(frappe.scrub(m))) for d in data)
	chart = {
		"data": {"labels": list(totals), "datasets": [{"values": list(totals.values())}]},
		"type": "donut",
		"fieldtype": "Currency",
	}
	return columns, data, None, chart
