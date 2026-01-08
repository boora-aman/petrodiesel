// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.query_reports["Nozzle-wise Sales Report"] = {
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
			"fieldname": "nozzle",
			"label": __("Nozzle"),
			"fieldtype": "Link",
			"options": "Fuel Nozzle Master"
		},
		{
			"fieldname": "fuel_item",
			"label": __("Fuel Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "cashier",
			"label": __("Cashier"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname": "shift",
			"label": __("Shift"),
			"fieldtype": "Link",
			"options": "Shift Master"
		}
	]
};
