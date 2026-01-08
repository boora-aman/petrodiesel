// Copyright (c) 2025, AlfaStack and contributors
// For license information, please see license.txt

frappe.query_reports["Cashier Performance Report"] = {
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
	],
	
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		// Highlight negative variance in red, positive in orange
		if (column.fieldname == "cash_variance" && data) {
			if (data.cash_variance < 0) {
				value = `<span style="color: red;">${value}</span>`;
			} else if (data.cash_variance > 0) {
				value = `<span style="color: orange;">${value}</span>`;
			}
		}
		
		// Highlight accuracy below 95% in red
		if (column.fieldname == "accuracy_percentage" && data) {
			if (data.accuracy_percentage < 95) {
				value = `<span style="color: red;">${value}</span>`;
			} else if (data.accuracy_percentage >= 99) {
				value = `<span style="color: green;">${value}</span>`;
			}
		}
		
		return value;
	}
};
