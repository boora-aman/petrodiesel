# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Number card and dashboard chart sources for the Petrol Pump workspace."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import add_days, flt, get_first_day, today


def _station(filters):
	if isinstance(filters, str):
		filters = json.loads(filters or "{}")
	if isinstance(filters, list):
		filters = {f[1]: f[3] for f in filters if len(f) >= 4}
	return (filters or {}).get("station") or frappe.db.get_single_value(
		"Petrodiesel Settings", "default_station"
	)


def _sse_sum(field, filters, date_from, date_to=None):
	station = _station(filters)
	cond = " and station = %(station)s" if station else ""
	return flt(
		frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
			f"""select coalesce(sum({field}), 0) from `tabShift Sale Entry`
		where docstatus = 1 and posting_date between %(f)s and %(t)s {cond}""",
			{"f": date_from, "t": date_to or date_from, "station": station},
		)[0][0]
	)


def _litres(value):
	return {"value": flt(value, 0), "fieldtype": "Float"}


def _signed(value, fieldtype, *_labels):
	return {"value": flt(value, 2), "fieldtype": fieldtype}


def _card(value, fieldtype="Currency", route=None, route_options=None):
	out = {"value": value, "fieldtype": fieldtype}
	if route:
		out["route"] = route
		out["route_options"] = route_options or {}
	return out


@frappe.whitelist()
def todays_fuel_litres(filters: str | dict | None = None):
	return _litres(_sse_sum("total_sale_qty", filters, today()))


@frappe.whitelist()
def todays_gross_sales(filters: str | dict | None = None):
	return _card(_sse_sum("gross_sales", filters, today()))


@frappe.whitelist()
def todays_credit_sales(filters: str | dict | None = None):
	return _card(_sse_sum("credit_sales_amount", filters, today()))


@frappe.whitelist()
def todays_digital(filters: str | dict | None = None):
	return _card(_sse_sum("digital_amount", filters, today()))


@frappe.whitelist()
def todays_short_excess(filters: str | dict | None = None):
	return _signed(_sse_sum("short_excess", filters, today()), "Currency", _("excess"), _("short"))


@frappe.whitelist()
def month_gross_sales(filters: str | dict | None = None):
	return _card(_sse_sum("gross_sales", filters, get_first_day(today()), today()))


@frappe.whitelist()
def month_fuel_litres(filters: str | dict | None = None):
	return _litres(_sse_sum("total_sale_qty", filters, get_first_day(today()), today()))


@frappe.whitelist()
def fuel_stock_litres(filters: str | dict | None = None):
	station = _station(filters)
	f = {"status": ["!=", "Inactive"]}
	if station:
		f["station"] = station
	total = 0.0
	for t in frappe.get_all("Fuel Tank Master", f, ["warehouse", "fuel_item"]):
		total += flt(
			frappe.db.get_value("Bin", {"warehouse": t.warehouse, "item_code": t.fuel_item}, "actual_qty")
		)
	return _litres(total)


@frappe.whitelist()
def credit_outstanding(filters: str | dict | None = None):
	station = _station(filters)
	walk_in = frappe.db.get_value("Fuel Station", station, "walk_in_customer") if station else None
	val = frappe.db.sql(
		"""select coalesce(sum(debit - credit), 0) from `tabGL Entry`
		where is_cancelled = 0 and party_type = 'Customer' and party != %s""",
		(walk_in or "",),
	)[0][0]
	return _card(flt(val))


@frappe.whitelist()
def month_stock_variance(filters: str | dict | None = None):
	station = _station(filters)
	cond = " and d.station = %(station)s" if station else ""
	val = frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
		f"""select coalesce(sum(i.variance), 0) from `tabDaily Stock Register Item` i
		join `tabDaily Stock Register` d on d.name = i.parent
		where d.docstatus = 1 and d.posting_date >= %(f)s {cond}""",
		{"f": get_first_day(today()), "station": station},
	)[0][0]
	return _signed(val, "Float", _("gain"), _("loss"))


# ---------------------------------------------------------------- chart sources
def _labels(days):
	return [add_days(today(), -i) for i in range(days - 1, -1, -1)]


@frappe.whitelist()
@frappe.read_only()
def daily_fuel_sales(
	chart_name: str | None = None,
	chart: str | dict | None = None,
	no_cache: int | str | bool | None = None,
	filters: str | dict | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	timespan: str | None = None,
	time_interval: str | None = None,
	heatmap_year: int | str | None = None,
):
	station = _station(filters)
	dates = _labels(30)
	cond = " and s.station = %(station)s" if station else ""
	rows = frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
		f"""select s.posting_date d, n.fuel_item f, sum(n.sale_qty) q
		from `tabShift Nozzle Reading` n join `tabShift Sale Entry` s on s.name = n.parent
		where s.docstatus = 1 and s.posting_date >= %(f)s {cond} group by s.posting_date, n.fuel_item""",
		{"f": dates[0], "station": station},
		as_dict=True,
	)
	fuels = sorted({r.f for r in rows})
	m = {(str(r.d), r.f): flt(r.q, 0) for r in rows}
	return {
		"labels": [frappe.format(d, "Date")[:5] for d in dates],
		"datasets": [{"name": f, "values": [m.get((str(d), f), 0) for d in dates]} for f in fuels],
	}


@frappe.whitelist()
@frappe.read_only()
def collection_mix(
	chart_name: str | None = None,
	chart: str | dict | None = None,
	no_cache: int | str | bool | None = None,
	filters: str | dict | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	timespan: str | None = None,
	time_interval: str | None = None,
	heatmap_year: int | str | None = None,
):
	station = _station(filters)
	cond = " and s.station = %(station)s" if station else ""
	args = {"f": add_days(today(), -30), "station": station}
	base = frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
		f"""select coalesce(sum(cash_counted),0), coalesce(sum(credit_sales_amount),0)
		from `tabShift Sale Entry` s where docstatus=1 and posting_date >= %(f)s {cond}""",
		args,
	)[0]
	modes = frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
		f"""select p.mode_of_payment, sum(p.amount) from `tabShift Payment` p
		join `tabShift Sale Entry` s on s.name = p.parent where s.docstatus=1 and s.posting_date >= %(f)s {cond}
		group by p.mode_of_payment""",
		args,
	)
	labels = [_("Cash"), _("Credit")] + [m[0] for m in modes]
	values = [flt(base[0]), flt(base[1])] + [flt(m[1]) for m in modes]
	return {"labels": labels, "datasets": [{"name": _("Collection"), "values": values}]}


@frappe.whitelist()
@frappe.read_only()
def tank_levels(
	chart_name: str | None = None,
	chart: str | dict | None = None,
	no_cache: int | str | bool | None = None,
	filters: str | dict | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	timespan: str | None = None,
	time_interval: str | None = None,
	heatmap_year: int | str | None = None,
):
	station = _station(filters)
	f = {"status": ["!=", "Inactive"]}
	if station:
		f["station"] = station
	labels, stock, ullage = [], [], []
	for t in frappe.get_all(
		"Fuel Tank Master", f, ["name", "warehouse", "fuel_item", "capacity_liters"], order_by="name"
	):
		s = flt(
			frappe.db.get_value("Bin", {"warehouse": t.warehouse, "item_code": t.fuel_item}, "actual_qty")
		)
		labels.append(f"{t.name}")
		stock.append(flt(s, 0))
		ullage.append(max(flt(t.capacity_liters - s, 0), 0))
	return {
		"labels": labels,
		"datasets": [{"name": _("Stock (L)"), "values": stock}, {"name": _("Empty (L)"), "values": ullage}],
	}


@frappe.whitelist()
@frappe.read_only()
def daily_stock_variance(
	chart_name: str | None = None,
	chart: str | dict | None = None,
	no_cache: int | str | bool | None = None,
	filters: str | dict | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	timespan: str | None = None,
	time_interval: str | None = None,
	heatmap_year: int | str | None = None,
):
	station = _station(filters)
	dates = _labels(30)
	cond = " and d.station = %(station)s" if station else ""
	rows = frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
		f"""select d.posting_date dt, i.fuel_item f, sum(i.variance) v
		from `tabDaily Stock Register Item` i join `tabDaily Stock Register` d on d.name = i.parent
		where d.docstatus = 1 and d.posting_date >= %(f)s {cond} group by d.posting_date, i.fuel_item""",
		{"f": dates[0], "station": station},
		as_dict=True,
	)
	fuels = sorted({r.f for r in rows})
	m = {(str(r.dt), r.f): flt(r.v, 1) for r in rows}
	return {
		"labels": [frappe.format(d, "Date")[:5] for d in dates],
		"datasets": [{"name": f, "values": [m.get((str(d), f), 0) for d in dates]} for f in fuels],
	}
