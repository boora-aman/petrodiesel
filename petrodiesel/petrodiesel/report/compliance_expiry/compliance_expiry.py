# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, today

from petrodiesel.tasks import get_expiring_items


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = [
		{"label": _("Document"), "fieldname": "doctype", "fieldtype": "Data", "width": 140},
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Dynamic Link", "options": "doctype", "width": 180},
		{"label": _("Item"), "fieldname": "what", "fieldtype": "Data", "width": 260},
		{"label": _("Valid Till"), "fieldname": "valid_till", "fieldtype": "Date", "width": 110},
		{"label": _("Days Left"), "fieldname": "days_left", "fieldtype": "Int", "width": 90},
	]
	data = get_expiring_items(int(filters.days or 90))
	for d in data:
		d["days_left"] = date_diff(d["valid_till"], today())
	data.sort(key=lambda d: d["days_left"])
	return columns, data
