// Copyright (c) 2025, AlfaStack and contributors
// For license information, please see license.txt

frappe.query_reports["Payment Mode Analysis"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "payment_method",
			"label": __("Payment Method"),
			"fieldtype": "Select",
			"options": "\nCash\nUPI\nCard\nCheque\nNEFT\nRTGS\nPaytm\nPhonePe\nGoogle Pay"
		},
		{
			"fieldname": "shift",
			"label": __("Shift"),
			"fieldtype": "Link",
			"options": "Shift Master"
		}
	]
};
