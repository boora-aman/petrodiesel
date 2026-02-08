// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.query_reports["Fuel Price History"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -3),
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
			"fieldname": "fuel_item",
			"label": __("Fuel Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "notification_source",
			"label": __("Notification Source"),
			"fieldtype": "Data"
		}
	],
	
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		// Highlight price increases in red, decreases in green
		if (column.fieldname == "change_amount" && data) {
			if (data.change_amount > 0) {
				value = `<span style="color: red;">+${value}</span>`;
			} else if (data.change_amount < 0) {
				value = `<span style="color: green;">${value}</span>`;
			}
		}
		
		if (column.fieldname == "change_percentage" && data) {
			if (data.change_percentage > 0) {
				value = `<span style="color: red;">+${value}</span>`;
			} else if (data.change_percentage < 0) {
				value = `<span style="color: green;">${value}</span>`;
			}
		}
		
		return value;
	}
};
