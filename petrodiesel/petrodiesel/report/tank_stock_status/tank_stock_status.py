# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, flt, today

from petrodiesel.petrodiesel.utils import get_tank_book_stock


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = [
		{
			"label": _("Tank"),
			"fieldname": "tank",
			"fieldtype": "Link",
			"options": "Fuel Tank Master",
			"width": 100,
		},
		{"label": _("Fuel"), "fieldname": "fuel_item", "fieldtype": "Link", "options": "Item", "width": 80},
		{"label": _("Capacity (L)"), "fieldname": "capacity", "fieldtype": "Float", "width": 110},
		{"label": _("Book Stock (L)"), "fieldname": "book", "fieldtype": "Float", "width": 120},
		{"label": _("Fill %"), "fieldname": "fill", "fieldtype": "Percent", "width": 80},
		{"label": _("Ullage (L)"), "fieldname": "ullage", "fieldtype": "Float", "width": 110},
		{"label": _("Last Dip Stock (L)"), "fieldname": "last_dip_stock", "fieldtype": "Float", "width": 130},
		{"label": _("Last Dip On"), "fieldname": "last_dip_on", "fieldtype": "Datetime", "width": 150},
		{"label": _("Avg Daily Sale (7d)"), "fieldname": "avg_sale", "fieldtype": "Float", "width": 130},
		{"label": _("Days of Cover"), "fieldname": "cover", "fieldtype": "Float", "width": 110},
		{"label": _("Reorder"), "fieldname": "reorder", "fieldtype": "Data", "width": 90},
	]
	f = {"status": ["!=", "Inactive"]}
	if filters.station:
		f["station"] = filters.station
	data = []
	for t in frappe.get_all(
		"Fuel Tank Master",
		f,
		[
			"name",
			"fuel_item",
			"capacity_liters",
			"safe_fill_percent",
			"last_dip_stock",
			"last_dip_on",
			"dead_stock_liters",
		],
		order_by="name",
	):
		book = flt(get_tank_book_stock(t.name), 2)
		sold = frappe.db.sql(
			"""select coalesce(sum(n.sale_qty), 0) from `tabShift Nozzle Reading` n
			join `tabShift Sale Entry` s on s.name = n.parent
			where s.docstatus = 1 and n.tank = %s and s.posting_date > %s""",
			(t.name, add_days(today(), -7)),
		)[0][0]
		avg = flt(sold) / 7
		usable = max(book - flt(t.dead_stock_liters), 0)
		cover = flt(usable / avg, 1) if avg else None
		data.append(
			{
				"tank": t.name,
				"fuel_item": t.fuel_item,
				"capacity": t.capacity_liters,
				"book": book,
				"fill": flt(book * 100 / t.capacity_liters, 1) if t.capacity_liters else 0,
				"ullage": flt(t.capacity_liters * flt(t.safe_fill_percent or 100) / 100 - book, 0),
				"last_dip_stock": t.last_dip_stock,
				"last_dip_on": t.last_dip_on,
				"avg_sale": flt(avg, 0),
				"cover": cover,
				"reorder": _("Order now") if cover is not None and cover < 2 else "",
			}
		)
	chart = {
		"data": {
			"labels": [d["tank"] for d in data],
			"datasets": [
				{"name": _("Book Stock"), "values": [d["book"] for d in data]},
				{"name": _("Ullage"), "values": [d["ullage"] for d in data]},
			],
		},
		"type": "bar",
		"barOptions": {"stacked": 1},
		"fieldtype": "Float",
	}
	return columns, data, None, chart
