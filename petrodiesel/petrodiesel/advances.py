# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Staff advance ledger: shift advances + office advances - recoveries."""

from __future__ import annotations

import frappe
from frappe.utils import flt, getdate


def advance_ledger(employee: str | None = None, to_date=None, company: str | None = None) -> list[dict]:
	"""Chronological ledger rows for one or all employees."""
	params = {
		"employee": employee,
		"to_date": getdate(to_date) if to_date else getdate("2999-12-31"),
		"company": company,
	}
	emp_cond = " and {col} = %(employee)s" if employee else ""
	co = " and {co} = %(company)s" if company else ""
	rows = frappe.db.sql(
		f"""
		select s.posting_date, 'Shift Sale Entry' voucher_type, s.name voucher_no, a.employee, a.employee_name,
			a.amount given, 0 recovered, a.remarks
		from `tabShift Employee Advance` a join `tabShift Sale Entry` s on s.name = a.parent
		where s.docstatus = 1 and s.posting_date <= %(to_date)s {emp_cond.format(col='a.employee')} {co.format(co='s.company')}
		union all
		select posting_date, 'Staff Advance', name, employee, employee_name, amount, 0, purpose
		from `tabStaff Advance` where docstatus = 1 and posting_date <= %(to_date)s
			{emp_cond.format(col='employee')} {co.format(co='company')}
		union all
		select posting_date, 'Staff Advance Recovery', name, employee, employee_name, 0, amount, concat(method, ifnull(concat(' - ', remarks), ''))
		from `tabStaff Advance Recovery` where docstatus = 1 and posting_date <= %(to_date)s
			{emp_cond.format(col='employee')} {co.format(co='company')}
		order by posting_date, voucher_no""",
		params,
		as_dict=True,
	)
	return rows


def advance_outstanding(employee: str, company: str | None = None, exclude: str | None = None) -> float:
	bal = 0.0
	for r in advance_ledger(employee, company=company):
		if r.voucher_no == exclude:
			continue
		bal += flt(r.given) - flt(r.recovered)
	return flt(bal, 2)


@frappe.whitelist()
def get_outstanding(employee: str) -> float:
	frappe.has_permission("Staff Advance", "read", throw=True)
	return advance_outstanding(employee)


@frappe.whitelist()
def get_balances() -> list[dict]:
	frappe.has_permission("Staff Advance", "read", throw=True)
	out = {}
	for r in advance_ledger():
		e = out.setdefault(
			r.employee,
			{
				"employee": r.employee,
				"employee_name": r.employee_name,
				"given": 0.0,
				"recovered": 0.0,
				"last_date": None,
			},
		)
		e["given"] += flt(r.given)
		e["recovered"] += flt(r.recovered)
		e["last_date"] = r.posting_date
	rows = []
	for e in out.values():
		e["balance"] = flt(e["given"] - e["recovered"], 2)
		rows.append(e)
	rows.sort(key=lambda x: -x["balance"])
	return rows


@frappe.whitelist()
def get_employee_ledger(employee: str) -> list[dict]:
	frappe.has_permission("Staff Advance", "read", throw=True)
	bal = 0.0
	rows = advance_ledger(employee)
	for r in rows:
		bal += flt(r.given) - flt(r.recovered)
		r["balance"] = flt(bal, 2)
	return rows
