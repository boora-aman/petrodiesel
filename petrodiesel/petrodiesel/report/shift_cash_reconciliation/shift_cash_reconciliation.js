// Copyright (c) 2026, Aman Boora and contributors
// For license information, please see license.txt

frappe.query_reports["Shift Cash Reconciliation"] = {
	filters: [
		{
			fieldname: "station",
			label: "Fuel Station",
			fieldtype: "Link",
			options: "Fuel Station",
		},
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -30),
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
		{ fieldname: "cashier", label: "Cashier", fieldtype: "Link", options: "Employee" },
		{ fieldname: "only_variance", label: "Only Short / Excess", fieldtype: "Check" },
	],
};
