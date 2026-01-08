// Copyright (c) 2025, AlfaStack and contributors
// For license information, please see license.txt

frappe.query_reports["Monthly Sales Analysis"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -12),
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
			"fieldname": "shift",
			"label": __("Shift"),
			"fieldtype": "Link",
			"options": "Shift Master"
		}
	],
	
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		// Highlight positive growth in green, negative in red
		if (column.fieldname == "growth_percentage" && data) {
			if (data.growth_percentage > 0) {
				value = `<span style="color: green;">+${value}</span>`;
			} else if (data.growth_percentage < 0) {
				value = `<span style="color: red;">${value}</span>`;
			}
		}
		
		return value;
	}
};
