# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 95},
		{
			"label": _("Voucher"),
			"fieldname": "voucher",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 160,
		},
		{
			"label": _("Voucher Type"),
			"fieldname": "voucher_type",
			"fieldtype": "Data",
			"width": 110,
			"hidden": 1,
		},
		{
			"label": _("Vehicle"),
			"fieldname": "vehicle",
			"fieldtype": "Link",
			"options": "Customer Vehicle",
			"width": 110,
		},
		{"label": _("Slip No"), "fieldname": "slip_no", "fieldtype": "Data", "width": 80},
		{"label": _("Item"), "fieldname": "item_code", "fieldtype": "Data", "width": 70},
		{"label": _("Qty (L)"), "fieldname": "qty", "fieldtype": "Float", "width": 80},
		{"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 80},
		{"label": _("Debit"), "fieldname": "debit", "fieldtype": "Currency", "width": 110},
		{"label": _("Credit"), "fieldname": "credit", "fieldtype": "Currency", "width": 110},
		{"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 120},
	]
	opening = frappe.db.sql(
		"""select coalesce(sum(debit - credit), 0) from `tabGL Entry`
		where is_cancelled = 0 and company=%(company)s and party_type='Customer' and party=%(customer)s
		and posting_date < %(from_date)s""",
		filters,
	)[0][0]
	rows = []
	vcond = " and i.petro_vehicle = %(vehicle)s" if filters.vehicle else ""
	for r in frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
		f"""
		select si.posting_date date, si.name voucher, 'Sales Invoice' voucher_type, i.petro_vehicle vehicle,
			i.petro_slip_no slip_no, i.item_code, i.qty, i.rate, i.amount debit, 0 credit, si.creation
		from `tabSales Invoice Item` i join `tabSales Invoice` si on si.name = i.parent
		where si.docstatus = 1 and si.company=%(company)s and si.customer=%(customer)s
		and si.posting_date between %(from_date)s and %(to_date)s {vcond}""",
		filters,
		as_dict=True,
	):
		rows.append(r)
	if not filters.vehicle:
		# non-invoice debits/credits: payments, driver cash journals, taxes rounding
		for r in frappe.db.sql(
			"""
			select posting_date date, voucher_no voucher, voucher_type, sum(debit) debit, sum(credit) credit,
				min(creation) creation
			from `tabGL Entry` where is_cancelled = 0 and company=%(company)s and party_type='Customer'
			and party=%(customer)s and posting_date between %(from_date)s and %(to_date)s
			and voucher_type != 'Sales Invoice'
			group by voucher_type, voucher_no, posting_date""",
			filters,
			as_dict=True,
		):
			rows.append(r)
		# invoice-level difference (e.g. rounding) so the balance ties to the ledger
		gl = dict(
			frappe.db.sql(
				"""select voucher_no, sum(debit - credit) from `tabGL Entry`
			where is_cancelled = 0 and company=%(company)s and party_type='Customer' and party=%(customer)s
			and voucher_type='Sales Invoice' and posting_date between %(from_date)s and %(to_date)s
			group by voucher_no""",
				filters,
			)
		)
		items = defaultdict(float)
		for r in rows:
			if r.get("voucher_type") == "Sales Invoice":
				items[r["voucher"]] += flt(r.get("debit"))
		for voucher, amount in gl.items():
			diff = flt(amount) - items.get(voucher, 0)
			if abs(diff) >= 0.01:
				inv = frappe.db.get_value(
					"Sales Invoice", voucher, ["posting_date", "creation"], as_dict=True
				)
				rows.append(
					{
						"date": inv.posting_date,
						"voucher": voucher,
						"voucher_type": "Sales Invoice",
						"item_code": _("Adj."),
						"debit": diff if diff > 0 else 0,
						"credit": -diff if diff < 0 else 0,
						"creation": inv.creation,
					}
				)
	rows.sort(key=lambda r: (r["date"], str(r.get("creation"))))
	bal = flt(opening)
	data = [
		{
			"item_code": _("Opening"),
			"balance": bal,
			"debit": bal if bal > 0 else 0,
			"credit": -bal if bal < 0 else 0,
		}
	]
	for r in rows:
		bal += flt(r.get("debit")) - flt(r.get("credit"))
		r["balance"] = bal
		data.append(r)
	return columns, data
