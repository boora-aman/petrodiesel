# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def _station_cond(filters, alias="s"):
	return f" and {alias}.station = %(station)s" if filters.get("station") else ""


def execute(filters=None):
	filters = frappe._dict(filters or {})
	fuels = frappe.get_all("Item", {"petro_product_type": "Fuel"}, pluck="name", order_by="name")
	columns = [{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100}]
	for f in fuels:
		columns.append(
			{"label": f"{f} (L)", "fieldname": f"qty_{frappe.scrub(f)}", "fieldtype": "Float", "width": 110}
		)
	columns += [
		{"label": _("Fuel Sales"), "fieldname": "fuel", "fieldtype": "Currency", "width": 130},
		{"label": _("Lube / Shop"), "fieldname": "other", "fieldtype": "Currency", "width": 110},
		{"label": _("Gross Sales"), "fieldname": "gross", "fieldtype": "Currency", "width": 130},
		{"label": _("Credit"), "fieldname": "credit", "fieldtype": "Currency", "width": 120},
		{"label": _("Digital"), "fieldname": "digital", "fieldtype": "Currency", "width": 120},
		{"label": _("Expenses + Advances"), "fieldname": "outflow", "fieldtype": "Currency", "width": 120},
		{"label": _("Cash Counted"), "fieldname": "cash", "fieldtype": "Currency", "width": 130},
		{"label": _("Short / Excess"), "fieldname": "short_excess", "fieldtype": "Currency", "width": 110},
		{"label": _("Shifts"), "fieldname": "shifts", "fieldtype": "Int", "width": 70},
	]
	cond = _station_cond(filters)
	rows = frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
		f"""
		select s.posting_date, sum(s.fuel_sales_amount) fuel, sum(s.other_sales_amount) other,
			sum(s.gross_sales) gross, sum(s.credit_sales_amount) credit, sum(s.digital_amount) digital,
			sum(s.expense_amount + s.advance_amount + s.driver_cash_amount) outflow, sum(s.cash_counted) cash,
			sum(s.short_excess) short_excess, count(*) shifts
		from `tabShift Sale Entry` s
		where s.docstatus = 1 and s.posting_date between %(from_date)s and %(to_date)s {cond}
		group by s.posting_date order by s.posting_date""",
		filters,
		as_dict=True,
	)
	qty = frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
		f"""
		select s.posting_date, n.fuel_item, sum(n.sale_qty) qty
		from `tabShift Nozzle Reading` n join `tabShift Sale Entry` s on s.name = n.parent
		where s.docstatus = 1 and s.posting_date between %(from_date)s and %(to_date)s {cond}
		group by s.posting_date, n.fuel_item""",
		filters,
		as_dict=True,
	)
	qmap = {(str(q.posting_date), q.fuel_item): q.qty for q in qty}
	for r in rows:
		for f in fuels:
			r[f"qty_{frappe.scrub(f)}"] = flt(qmap.get((str(r.posting_date), f)), 2)
	chart = {
		"data": {
			"labels": [frappe.format(r.posting_date, "Date") for r in rows],
			"datasets": [{"name": f, "values": [r[f"qty_{frappe.scrub(f)}"] for r in rows]} for f in fuels],
		},
		"type": "bar",
		"barOptions": {"stacked": 1},
		"fieldtype": "Float",
	}
	return columns, rows, None, chart
