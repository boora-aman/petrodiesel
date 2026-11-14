import frappe


def execute():
	"""Build machine-wise rows for shift entries saved before the feature existed."""
	frappe.reload_doc("petrodiesel", "doctype", "shift_machine_summary")
	frappe.reload_doc("petrodiesel", "doctype", "shift_sale_entry")
	done = set(frappe.get_all("Shift Machine Summary", pluck="parent", distinct=True))
	for name in frappe.get_all("Shift Sale Entry", {"docstatus": ["<", 2]}, pluck="name"):
		if name in done:
			continue
		doc = frappe.get_doc("Shift Sale Entry", name)
		doc.calculate_machine_summary()
		for i, row in enumerate(doc.machine_summary, 1):
			row.parent, row.parenttype, row.parentfield, row.idx = doc.name, doc.doctype, "machine_summary", i
			row.docstatus = doc.docstatus
			row.db_insert()
