# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Scheduled jobs."""

import frappe
from frappe import _
from frappe.utils import add_days, getdate, today


def daily():
	alert_expiring_compliance()
	alert_missing_dsr()


def _recipients():
	users = frappe.get_all(
		"Has Role",
		{"role": ["in", ["Pump Owner", "Pump Manager"]], "parenttype": "User"},
		pluck="parent",
		distinct=True,
	)
	return [
		u for u in users if u not in ("Administrator", "Guest") and frappe.db.get_value("User", u, "enabled")
	]


def _notify(subject, message, doctype, name):
	for user in _recipients():
		frappe.get_doc(
			{
				"doctype": "Notification Log",
				"for_user": user,
				"type": "Alert",
				"subject": subject,
				"email_content": message,
				"document_type": doctype,
				"document_name": name,
			}
		).insert(ignore_permissions=True)


def get_expiring_items(days=None):
	days = days or frappe.db.get_single_value("Petrodiesel Settings", "expiry_alert_days") or 30
	upto = add_days(today(), days)
	out = []
	for r in frappe.get_all(
		"Station Licence",
		{"valid_till": ["<=", upto], "parenttype": "Fuel Station"},
		["parent", "licence_type", "licence_no", "valid_till"],
	):
		out.append(
			{
				"doctype": "Fuel Station",
				"name": r.parent,
				"what": f"{r.licence_type} {r.licence_no or ''}".strip(),
				"valid_till": r.valid_till,
			}
		)
	for r in frappe.get_all(
		"Dispensing Unit",
		{"wm_valid_till": ["<=", upto], "status": ["!=", "Inactive"]},
		["name", "wm_valid_till"],
	):
		out.append(
			{
				"doctype": "Dispensing Unit",
				"name": r.name,
				"what": _("W&M stamping"),
				"valid_till": r.wm_valid_till,
			}
		)
	for r in frappe.get_all(
		"Fuel Tank Master",
		{"next_calibration_due": ["<=", upto], "status": ["!=", "Inactive"]},
		["name", "next_calibration_due"],
	):
		out.append(
			{
				"doctype": "Fuel Tank Master",
				"name": r.name,
				"what": _("Tank calibration"),
				"valid_till": r.next_calibration_due,
			}
		)
	return out


def alert_expiring_compliance():
	for item in get_expiring_items():
		expired = getdate(item["valid_till"]) < getdate(today())
		subject = _("{0} {1} for {2} on {3}").format(
			item["what"],
			_("expired") if expired else _("expires"),
			item["name"],
			frappe.format(item["valid_till"], "Date"),
		)
		_notify(subject, subject, item["doctype"], item["name"])


def alert_missing_dsr():
	yesterday = add_days(today(), -1)
	for station in frappe.get_all("Fuel Station", {"is_active": 1}, pluck="name"):
		if not frappe.db.exists(
			"Daily Stock Register", {"station": station, "posting_date": yesterday, "docstatus": 1}
		):
			if frappe.db.exists(
				"Shift Sale Entry", {"station": station, "posting_date": yesterday, "docstatus": 1}
			):
				_notify(
					_("Daily Stock Register for {0} on {1} is not submitted").format(station, yesterday),
					"",
					"Fuel Station",
					station,
				)
