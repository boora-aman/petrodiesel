import frappe


def execute():
	"""Rebuild machine-side sales and attendant collection rows for every shift entry."""
	frappe.reload_doc("petrodiesel", "doctype", "shift_machine_summary")
	frappe.reload_doc("petrodiesel", "doctype", "shift_attendant_collection")
	frappe.reload_doc("petrodiesel", "doctype", "shift_sale_entry")
	for name in frappe.get_all("Shift Sale Entry", {"docstatus": ["<", 2]}, pluck="name"):
		doc = frappe.get_doc("Shift Sale Entry", name)
		doc.calculate_machine_summary()
		for table in ("machine_summary", "attendant_collection"):
			frappe.db.delete(doc.meta.get_field(table).options, {"parent": name})
			for i, row in enumerate(doc.get(table), 1):
				row.parent, row.parenttype, row.parentfield, row.idx = doc.name, doc.doctype, table, i
				row.docstatus = doc.docstatus
				row.db_insert()
