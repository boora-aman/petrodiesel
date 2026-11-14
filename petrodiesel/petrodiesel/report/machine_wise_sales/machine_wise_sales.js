frappe.query_reports["Machine-wise Sales"] = {
	filters: [
		{ fieldname: "station", label: __("Fuel Station"), fieldtype: "Link", options: "Fuel Station" },
		{ fieldname: "from_date", label: __("From Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.add_days(frappe.datetime.get_today(), -30) },
		{ fieldname: "to_date", label: __("To Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
		{ fieldname: "dispensing_unit", label: __("Machine"), fieldtype: "Link", options: "Dispensing Unit" },
	],
};
