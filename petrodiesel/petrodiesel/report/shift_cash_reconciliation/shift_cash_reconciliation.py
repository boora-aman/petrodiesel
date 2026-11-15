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
			"label": _("Entry"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Shift Sale Entry",
			"width": 150,
		},
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{"label": _("Shift"), "fieldname": "shift", "fieldtype": "Data", "width": 80},
		{"label": _("Cashier"), "fieldname": "cashier_name", "fieldtype": "Data", "width": 120},
		{"label": _("Retail Sales"), "fieldname": "retail", "fieldtype": "Currency", "width": 120},
		{"label": _("Digital"), "fieldname": "digital_amount", "fieldtype": "Currency", "width": 110},
		{"label": _("Expenses"), "fieldname": "expense_amount", "fieldtype": "Currency", "width": 90},
		{"label": _("Advances"), "fieldname": "advance_amount", "fieldtype": "Currency", "width": 90},
		{"label": _("Driver Cash"), "fieldname": "driver_cash_amount", "fieldtype": "Currency", "width": 90},
		{"label": _("Expected Cash"), "fieldname": "expected_cash", "fieldtype": "Currency", "width": 120},
		{"label": _("Cash Counted"), "fieldname": "cash_counted", "fieldtype": "Currency", "width": 120},
		{"label": _("Short / Excess"), "fieldname": "short_excess", "fieldtype": "Currency", "width": 110},
		{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 200},
	]
	cond = _station_cond(filters)
	if filters.cashier:
		cond += " and s.cashier = %(cashier)s"
	if filters.only_variance:
		cond += " and abs(s.short_excess) >= 1"
	data = frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
		f"""
		select s.name, s.posting_date, s.shift, s.cashier_name,
			s.gross_sales - s.credit_sales_amount retail, s.digital_amount, s.expense_amount, s.advance_amount,
			s.driver_cash_amount, s.expected_cash, s.cash_counted, s.short_excess, s.remarks
		from `tabShift Sale Entry` s left join `tabShift Master` sm on sm.name = s.shift
		where s.docstatus = 1 and s.posting_date between %(from_date)s and %(to_date)s {cond}
		order by s.posting_date, sm.sequence""",
		filters,
		as_dict=True,
	)
	return columns, data
