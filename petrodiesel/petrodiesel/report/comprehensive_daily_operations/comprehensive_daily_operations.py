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
		{"label": _("Section"), "fieldname": "section", "fieldtype": "Data", "width": 180},
		{"label": _("Particular"), "fieldname": "particular", "fieldtype": "Data", "width": 260},
		{"label": _("Litres"), "fieldname": "litres", "fieldtype": "Float", "width": 120},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 140},
	]
	cond = _station_cond(filters)
	where = f"s.docstatus = 1 and s.posting_date = %(posting_date)s {cond}"
	data = []

	def section(title, rows):
		data.append({"section": title, "particular": None, "litres": None, "amount": None, "bold": 1})
		for r in rows:
			data.append({"section": None, "particular": r[0], "litres": r[1], "amount": r[2], "indent": 1})

	def child(table, label, litres, amount):
		return frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
			f"""
			select {label}, {litres}, sum({amount}) from `tab{table}` c
			join `tabShift Sale Entry` s on s.name = c.parent
			where {where} group by 1 order by 1""",
			filters,
		)

	section(_("Fuel Sales"), child("Shift Nozzle Reading", "c.fuel_item", "sum(c.sale_qty)", "c.amount"))
	section(_("Lube / Shop Sales"), child("Shift Other Sales", "c.item_code", "sum(c.qty)", "c.amount"))
	section(_("Credit Sales"), child("Shift Credit Sale", "c.customer", "sum(c.qty)", "c.amount"))
	section(_("Digital Payments"), child("Shift Payment", "c.mode_of_payment", "null", "c.amount"))
	section(_("Expenses"), child("Shift Expense Detail", "c.expense_account", "null", "c.amount"))

	t = frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
		f"""
		select count(*) shifts, sum(s.advance_amount) advance, sum(s.driver_cash_amount) driver_cash,
			sum(s.expected_cash) expected, sum(s.cash_counted) counted, sum(s.short_excess) short_excess
		from `tabShift Sale Entry` s where {where}""",
		filters,
		as_dict=True,
	)[0]
	section(
		_("Cash Summary"),
		[
			(_("Shifts Submitted: {0}").format(t.shifts or 0), None, None),
			(_("Employee Advances"), None, flt(t.advance)),
			(_("Driver Cash"), None, flt(t.driver_cash)),
			(_("Expected Cash"), None, flt(t.expected)),
			(_("Cash Counted"), None, flt(t.counted)),
			(_("Short / Excess"), None, flt(t.short_excess)),
		],
	)

	tcond = _station_cond(filters, "t")
	section(
		_("Tanker Receipts"),
		frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
			f"""
		select concat(i.tank, ' (', i.fuel_item, ') - Received'), sum(i.received_qty), null
		from `tabTanker Receipt Item` i join `tabTanker Receipt` t on t.name = i.parent
		where t.docstatus = 1 and t.posting_date = %(posting_date)s {tcond}
		group by i.tank, i.fuel_item
		union all
		select concat(i.tank, ' (', i.fuel_item, ') - Shortage'), sum(i.shortage_qty), null
		from `tabTanker Receipt Item` i join `tabTanker Receipt` t on t.name = i.parent
		where t.docstatus = 1 and t.posting_date = %(posting_date)s {tcond}
		group by i.tank, i.fuel_item
		order by 1""",
			filters,
		),
	)

	dcond = _station_cond(filters, "d")
	section(
		_("Stock Gain / Loss"),
		frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
			f"""
		select concat(i.tank, ' (', i.fuel_item, ')'), sum(i.variance), null
		from `tabDaily Stock Register Item` i join `tabDaily Stock Register` d on d.name = i.parent
		where d.docstatus = 1 and d.posting_date = %(posting_date)s {dcond}
		group by i.tank, i.fuel_item order by 1""",
			filters,
		),
	)
	return columns, data
