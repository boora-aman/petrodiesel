// Copyright (c) 2026, Aman Boora and contributors
// For license information, please see license.txt

frappe.query_reports["Tank Stock Status"] = {
	filters: [
		{"fieldname": "station", "label": "Fuel Station", "fieldtype": "Link", "options": "Fuel Station"}
	],
};
