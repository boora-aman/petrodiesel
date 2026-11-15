# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Stop ERPNext documents posted by PetroDesk from being cancelled on their own.

Cancelling, say, the retail Sales Invoice of an approved shift in the desk would leave the
shift Approved with its nozzle readings advanced but its sales gone. Cancel the PetroDesk
document instead; it cancels its postings itself (it is already cancelled by then, so this
guard lets those through).
"""

import frappe
from frappe import _

# ERPNext doctype -> [(PetroDesk doctype, field on it that holds the ERPNext document)]
OWNERS = {
	"Journal Entry": [
		("Shift Sale Entry", "settlement_journal"),
		("Staff Advance", "journal_entry"),
		("Staff Advance Recovery", "journal_entry"),
	],
	"Purchase Invoice": [("Tanker Receipt", "purchase_invoice"), ("Shop Purchase", "purchase_invoice")],
	"Stock Entry": [("Internal Stock Transfer", "stock_entry")],
	"Stock Reconciliation": [("Daily Stock Register", "stock_reconciliation")],
}
# ERPNext doctype -> [(custom link field on the ERPNext doc, PetroDesk doctype)]
BACK_LINKS = {
	"Sales Invoice": [("shift_sale_entry", "Shift Sale Entry")],
	"Stock Entry": [("tanker_receipt", "Tanker Receipt")],
}


def before_cancel(doc, method=None):
	owners = []
	for dt, field in OWNERS.get(doc.doctype, []):
		if frappe.get_meta(dt).has_field(field):
			owners += [(dt, n) for n in frappe.get_all(dt, {field: doc.name, "docstatus": 1}, pluck="name")]
	for field, dt in BACK_LINKS.get(doc.doctype, []):
		name = doc.get(field)
		if name and frappe.db.get_value(dt, name, "docstatus") == 1:
			owners.append((dt, name))
	if owners:
		dt, name = owners[0]
		frappe.throw(
			_("{0} {1} was posted by {2} {3}. Cancel {3} in PetroDesk instead.").format(
				_(doc.doctype), doc.name, _(dt), frappe.bold(name)
			),
			title=_("Cancel from PetroDesk"),
		)
