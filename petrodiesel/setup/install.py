# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Idempotent setup: roles, custom fields, workflows, settings defaults.

Runs after install and after every migrate.
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

ROLES = {
	"Pump Owner": "Dealer / owner: full access, approvals, prices, settings",
	"Pump Manager": "Outlet manager: approves shifts, receipts, DSR; manages masters",
	"Pump Cashier": "Shift in-charge: enters shift closings, credit slips, collections",
	"Pump Stock Keeper": "Receives tankers, records dips and the Daily Stock Register",
}

CUSTOM_FIELDS = {
	"Item": [
		{
			"fieldname": "petro_section",
			"fieldtype": "Section Break",
			"label": "Petrol Pump",
			"insert_after": "description",
			"collapsible": 1,
		},
		{
			"fieldname": "petro_product_type",
			"fieldtype": "Select",
			"label": "Petrol Pump Product Type",
			"options": "\nFuel\nLubricant\nAccessory\nOther",
			"insert_after": "petro_section",
			"in_standard_filter": 1,
		},
		{"fieldname": "petro_cb", "fieldtype": "Column Break", "insert_after": "petro_product_type"},
		{
			"fieldname": "permissible_loss_percent",
			"fieldtype": "Percent",
			"label": "Permissible Stock Loss %",
			"insert_after": "petro_cb",
			"depends_on": "eval:doc.petro_product_type=='Fuel'",
			"description": "Evaporation / handling loss allowed as % of sales (e.g. MS 0.6, HSD 0.25).",
		},
	],
	"Sales Invoice": [
		{
			"fieldname": "fuel_station",
			"fieldtype": "Link",
			"label": "Fuel Station",
			"options": "Fuel Station",
			"insert_after": "customer_name",
			"read_only": 1,
			"in_standard_filter": 1,
		},
		{
			"fieldname": "shift_sale_entry",
			"fieldtype": "Link",
			"label": "Shift Sale Entry",
			"options": "Shift Sale Entry",
			"insert_after": "fuel_station",
			"read_only": 1,
			"no_copy": 1,
			"search_index": 1,
		},
	],
	"Sales Invoice Item": [
		{
			"fieldname": "petro_vehicle",
			"fieldtype": "Link",
			"label": "Vehicle",
			"options": "Customer Vehicle",
			"insert_after": "description",
			"read_only": 1,
			"in_list_view": 0,
		},
		{
			"fieldname": "petro_slip_no",
			"fieldtype": "Data",
			"label": "Indent / Slip No",
			"insert_after": "petro_vehicle",
			"read_only": 1,
		},
	],
	"Journal Entry": [
		{
			"fieldname": "shift_sale_entry",
			"fieldtype": "Link",
			"label": "Shift Sale Entry",
			"options": "Shift Sale Entry",
			"insert_after": "voucher_type",
			"read_only": 1,
			"no_copy": 1,
			"search_index": 1,
		},
	],
	"Purchase Invoice": [
		{
			"fieldname": "tanker_receipt",
			"fieldtype": "Link",
			"label": "Tanker Receipt",
			"options": "Tanker Receipt",
			"insert_after": "supplier_name",
			"read_only": 1,
			"no_copy": 1,
			"search_index": 1,
		},
	],
	"Stock Entry": [
		{
			"fieldname": "tanker_receipt",
			"fieldtype": "Link",
			"label": "Tanker Receipt",
			"options": "Tanker Receipt",
			"insert_after": "stock_entry_type",
			"read_only": 1,
			"no_copy": 1,
			"search_index": 1,
		},
	],
	"Stock Reconciliation": [
		{
			"fieldname": "daily_stock_register",
			"fieldtype": "Link",
			"label": "Daily Stock Register",
			"options": "Daily Stock Register",
			"insert_after": "purpose",
			"read_only": 1,
			"no_copy": 1,
		},
	],
}

# role -> list of (doctype, perms) for ERPNext doctypes the pump roles need
ERP_PERMS = {
	"Pump Owner": {
		"read": [
			"Item",
			"Customer",
			"Supplier",
			"Employee",
			"Warehouse",
			"Account",
			"Cost Center",
			"Company",
			"Mode of Payment",
			"Price List",
			"Item Price",
			"Sales Invoice",
			"Purchase Invoice",
			"Journal Entry",
			"Payment Entry",
			"Stock Entry",
			"Stock Reconciliation",
			"Item Group",
			"UOM",
			"GL Entry",
			"Stock Ledger Entry",
			"Sales Taxes and Charges Template",
			"Fiscal Year",
			"Currency",
		],
		"write": ["Customer", "Item", "Item Price", "Payment Entry", "Employee"],
	},
	"Pump Manager": {
		"read": [
			"Item",
			"Customer",
			"Supplier",
			"Employee",
			"Warehouse",
			"Account",
			"Cost Center",
			"Company",
			"Mode of Payment",
			"Price List",
			"Item Price",
			"Sales Invoice",
			"Purchase Invoice",
			"Journal Entry",
			"Payment Entry",
			"Stock Entry",
			"Stock Reconciliation",
			"Item Group",
			"UOM",
			"GL Entry",
			"Stock Ledger Entry",
			"Sales Taxes and Charges Template",
			"Fiscal Year",
			"Currency",
		],
		"write": ["Customer", "Payment Entry"],
	},
	"Pump Cashier": {
		"read": [
			"Item",
			"Customer",
			"Employee",
			"Warehouse",
			"Account",
			"Company",
			"Mode of Payment",
			"Price List",
			"Item Price",
			"Sales Invoice",
			"Item Group",
			"UOM",
			"Cost Center",
			"Fiscal Year",
			"Currency",
		],
		"write": [],
	},
	"Pump Stock Keeper": {
		"read": [
			"Item",
			"Supplier",
			"Employee",
			"Warehouse",
			"Company",
			"Purchase Invoice",
			"Stock Entry",
			"Stock Reconciliation",
			"Item Group",
			"UOM",
			"Stock Ledger Entry",
			"Cost Center",
			"Fiscal Year",
			"Currency",
		],
		"write": [],
	},
}

WORKFLOWS = [
	{
		"name": "Shift Sale Entry Approval",
		"document_type": "Shift Sale Entry",
		"states": [
			("Draft", 0, "Pump Cashier", "Warning"),
			("Pending Approval", 0, "Pump Manager", "Primary"),
			("Rejected", 0, "Pump Cashier", "Danger"),
			("Approved", 1, "Pump Manager", "Success"),
			("Cancelled", 2, "Pump Manager", "Inverse"),
		],
		"transitions": [
			(
				"Draft",
				"Submit for Approval",
				"Pending Approval",
				["Pump Cashier", "Pump Manager", "Pump Owner"],
			),
			("Pending Approval", "Approve", "Approved", ["Pump Manager", "Pump Owner"]),
			("Pending Approval", "Reject", "Rejected", ["Pump Manager", "Pump Owner"]),
			("Rejected", "Revise", "Draft", ["Pump Cashier", "Pump Manager", "Pump Owner"]),
			("Approved", "Cancel", "Cancelled", ["Pump Manager", "Pump Owner"]),
		],
	},
	{
		"name": "Tanker Receipt Approval",
		"document_type": "Tanker Receipt",
		"states": [
			("Draft", 0, "Pump Stock Keeper", "Warning"),
			("Pending Verification", 0, "Pump Manager", "Primary"),
			("Rejected", 0, "Pump Stock Keeper", "Danger"),
			("Accepted", 1, "Pump Manager", "Success"),
			("Cancelled", 2, "Pump Manager", "Inverse"),
		],
		"transitions": [
			(
				"Draft",
				"Send for Verification",
				"Pending Verification",
				["Pump Stock Keeper", "Pump Manager", "Pump Owner"],
			),
			("Pending Verification", "Accept", "Accepted", ["Pump Manager", "Pump Owner"]),
			("Pending Verification", "Reject", "Rejected", ["Pump Manager", "Pump Owner"]),
			("Rejected", "Revise", "Draft", ["Pump Stock Keeper", "Pump Manager", "Pump Owner"]),
			("Accepted", "Cancel", "Cancelled", ["Pump Manager", "Pump Owner"]),
		],
	},
]


def after_install():
	setup()


def after_migrate():
	setup()


def setup():
	create_roles()
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True, update=True)
	grant_erpnext_permissions()
	create_workflows()
	set_settings_defaults()
	# Logged-in users opening /login or the apps screen go to PetroDesk by default
	if frappe.get_meta("System Settings").has_field("default_app") and not frappe.db.get_single_value(
		"System Settings", "default_app"
	):
		frappe.db.set_single_value("System Settings", "default_app", "petrodiesel")
	# Fuel items carry a VAT Item Tax Template for sales. ERPNext would otherwise auto-add those
	# VAT rows to purchase invoices too, where fuel has no input tax credit.
	if frappe.get_meta("Accounts Settings").has_field("add_taxes_from_item_tax_template"):
		frappe.db.set_single_value("Accounts Settings", "add_taxes_from_item_tax_template", 0)
	frappe.db.commit()  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.frappe-manual-commit -- intentional commit


def create_roles():
	for role, desc in ROLES.items():
		if not frappe.db.exists("Role", role):
			frappe.get_doc(
				{"doctype": "Role", "role_name": role, "desk_access": 1, "description": desc}
			).insert(ignore_permissions=True)


DESK_DOCTYPES = ["Number Card", "Dashboard Chart", "Dashboard Chart Source"]


def grant_erpnext_permissions():
	from frappe.permissions import add_permission, update_permission_property

	for role, spec in ERP_PERMS.items():
		for doctype in spec["read"] + DESK_DOCTYPES:
			if not frappe.db.exists("DocType", doctype):
				continue
			if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}):
				add_permission(doctype, role, 0)
		for doctype in spec["write"]:
			if frappe.db.exists("DocType", doctype):
				for ptype in ("write", "create"):
					update_permission_property(doctype, role, 0, ptype, 1, validate=False)


def create_workflows():
	for wf in WORKFLOWS:
		for state, _ds, _role, style in wf["states"]:
			if not frappe.db.exists("Workflow State", state):
				frappe.get_doc(
					{"doctype": "Workflow State", "workflow_state_name": state, "style": style}
				).insert(ignore_permissions=True)
		for _f, action, _t, _r in wf["transitions"]:
			if not frappe.db.exists("Workflow Action Master", action):
				frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
					ignore_permissions=True
				)
		if frappe.db.exists("Workflow", wf["name"]):
			continue
		doc = frappe.new_doc("Workflow")
		doc.update(
			{
				"workflow_name": wf["name"],
				"document_type": wf["document_type"],
				"workflow_state_field": "workflow_state",
				"is_active": 1,
				"send_email_alert": 0,
				"override_status": 0,
			}
		)
		for state, docstatus, role, _style in wf["states"]:
			doc.append("states", {"state": state, "doc_status": str(docstatus), "allow_edit": role})
		for frm, action, to, roles in wf["transitions"]:
			for role in roles:
				doc.append(
					"transitions",
					{
						"state": frm,
						"action": action,
						"next_state": to,
						"allowed": role,
						"allow_self_approval": 1,
					},
				)
		doc.insert(ignore_permissions=True)


def set_settings_defaults():
	s = frappe.get_single("Petrodiesel Settings")
	defaults = {
		"density_tolerance": 3,
		"pump_test_tolerance_ml": 15,
		"default_permissible_loss": 0.6,
		"cash_variance_tolerance": 100,
		"expiry_alert_days": 30,
	}
	changed = False
	for k, v in defaults.items():
		if not s.get(k):
			s.set(k, v)
			changed = True
	if not s.fuel_price_list and frappe.db.exists("Price List", "Standard Selling"):
		s.fuel_price_list = "Standard Selling"
		changed = True
	if changed:
		s.flags.ignore_permissions = True
		s.flags.ignore_mandatory = True
		s.flags.ignore_links = True
		s.save()
