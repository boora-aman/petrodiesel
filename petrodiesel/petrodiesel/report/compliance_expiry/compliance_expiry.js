// Copyright (c) 2026, Aman Boora and contributors
// For license information, please see license.txt

frappe.query_reports["Compliance Expiry"] = {
	filters: [
		{ fieldname: "days", label: "Expiring Within (days)", fieldtype: "Int", default: "90" },
	],
};
