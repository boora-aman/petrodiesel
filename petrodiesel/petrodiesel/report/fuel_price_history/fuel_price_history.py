# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = [
		{"label": _("Effective Date"), "fieldname": "effective_date", "fieldtype": "Date", "width": 110},
		{
			"label": _("Update"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Fuel Price Update",
			"width": 140,
		},
		{"label": _("Fuel"), "fieldname": "fuel_item", "fieldtype": "Link", "options": "Item", "width": 90},
		{"label": _("Old Price"), "fieldname": "old_price", "fieldtype": "Currency", "width": 100},
		{"label": _("New Price"), "fieldname": "new_price", "fieldtype": "Currency", "width": 100},
		{"label": _("Change"), "fieldname": "change_amount", "fieldtype": "Currency", "width": 90},
		{"label": _("Change %"), "fieldname": "change_percent", "fieldtype": "Percent", "width": 90},
		{"label": _("Source"), "fieldname": "source", "fieldtype": "Data", "width": 110},
	]
	cond = " and i.fuel_item = %(fuel_item)s" if filters.fuel_item else ""
	data = frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
		f"""select u.effective_date, u.name, i.fuel_item, i.old_price, i.new_price,
		i.change_amount, i.change_percent, u.source
		from `tabFuel Price Update Item` i join `tabFuel Price Update` u on u.name = i.parent
		where u.docstatus = 1 and u.effective_date between %(from_date)s and %(to_date)s {cond}
		order by u.effective_date, i.fuel_item""",
		filters,
		as_dict=True,
	)
	fuels = sorted({d.fuel_item for d in data})
	dates = sorted({d.effective_date for d in data})
	m = {(d.effective_date, d.fuel_item): d.new_price for d in data}
	chart = {
		"data": {
			"labels": [frappe.format(d, "Date") for d in dates],
			"datasets": [{"name": f, "values": [m.get((d, f)) or 0 for d in dates]} for f in fuels],
		},
		"type": "line",
		"fieldtype": "Currency",
	}
	return columns, data, None, chart
