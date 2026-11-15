// Copyright (c) 2026, Aman Boora and contributors
// For license information, please see license.txt

frappe.query_reports["Comprehensive Daily Operations"] = {
	filters: [
		{
			fieldname: "station",
			label: "Fuel Station",
			fieldtype: "Link",
			options: "Fuel Station",
		},
		{
			fieldname: "posting_date",
			label: "Date",
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
	],
};
