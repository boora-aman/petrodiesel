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
	columns = [{"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 90}]
	for f in fuels:
		columns.append(
			{"label": f"{f} (L)", "fieldname": f"qty_{frappe.scrub(f)}", "fieldtype": "Float", "width": 110}
		)
	columns += [
		{"label": _("Fuel Sales"), "fieldname": "fuel", "fieldtype": "Currency", "width": 130},
		{"label": _("Lube / Shop"), "fieldname": "other", "fieldtype": "Currency", "width": 110},
		{"label": _("Gross Sales"), "fieldname": "gross", "fieldtype": "Currency", "width": 140},
		{"label": _("Credit"), "fieldname": "credit", "fieldtype": "Currency", "width": 120},
		{"label": _("Digital"), "fieldname": "digital", "fieldtype": "Currency", "width": 120},
		{"label": _("Short / Excess"), "fieldname": "short_excess", "fieldtype": "Currency", "width": 110},
		{"label": _("Growth %"), "fieldname": "growth", "fieldtype": "Percent", "width": 90},
	]
	cond = _station_cond(filters)
	data = frappe.db.sql(
		f"""
		select date_format(s.posting_date, '%%Y-%%m') month, sum(s.fuel_sales_amount) fuel,
			sum(s.other_sales_amount) other, sum(s.gross_sales) gross, sum(s.credit_sales_amount) credit,
			sum(s.digital_amount) digital, sum(s.short_excess) short_excess
		from `tabShift Sale Entry` s
		where s.docstatus = 1 and s.posting_date between %(from_date)s and %(to_date)s {cond}
		group by month order by month""",
		filters,
		as_dict=True,
	)
	qty = frappe.db.sql(
		f"""
		select date_format(s.posting_date, '%%Y-%%m') month, n.fuel_item, sum(n.sale_qty) qty
		from `tabShift Nozzle Reading` n join `tabShift Sale Entry` s on s.name = n.parent
		where s.docstatus = 1 and s.posting_date between %(from_date)s and %(to_date)s {cond}
		group by month, n.fuel_item""",
		filters,
		as_dict=True,
	)
	qmap = {(q.month, q.fuel_item): q.qty for q in qty}
	prev = None
	for r in data:
		for f in fuels:
			r[f"qty_{frappe.scrub(f)}"] = flt(qmap.get((r.month, f)), 2)
		r["growth"] = (flt(r.gross) - prev) * 100 / prev if prev else None
		prev = flt(r.gross)
	chart = {
		"data": {
			"labels": [r.month for r in data],
			"datasets": [{"name": f, "values": [r[f"qty_{frappe.scrub(f)}"] for r in data]} for f in fuels],
		},
		"type": "bar",
		"barOptions": {"stacked": 1},
		"fieldtype": "Float",
	}
	return columns, data, None, chart
