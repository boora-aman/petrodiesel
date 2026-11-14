// Copyright (c) 2026, Aman Boora and contributors
frappe.query_reports["Staff Advance Balance"] = {
	filters: [
		{ fieldname: "employee", label: __("Employee (shows ledger)"), fieldtype: "Link", options: "Employee" },
		{ fieldname: "to_date", label: __("As On"), fieldtype: "Date", default: frappe.datetime.get_today() },
	],
};
