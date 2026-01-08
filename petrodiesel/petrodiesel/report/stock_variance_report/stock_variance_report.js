// Copyright (c) 2025, AlfaStack and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Variance Report"] = {
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
			"fieldname": "tank",
			"label": __("Tank"),
			"fieldtype": "Link",
			"options": "Fuel Tank Master"
		},
		{
			"fieldname": "fuel_item",
			"label": __("Fuel Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "shift",
			"label": __("Shift"),
			"fieldtype": "Link",
			"options": "Shift Master"
		},
		{
			"fieldname": "show_variance_only",
			"label": __("Show Variance Only"),
			"fieldtype": "Check",
			"default": 0
		},
		{
			"fieldname": "variance_threshold",
			"label": __("Variance Threshold (L)"),
			"fieldtype": "Float",
			"description": __("Show only variances above this threshold")
		}
	],
	
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		// Highlight negative variance in red
		if (column.fieldname == "variance" && data && data.variance < 0) {
			value = `<span style="color: red;">${value}</span>`;
		}
		
		// Highlight positive variance in orange
		if (column.fieldname == "variance" && data && data.variance > 0) {
			value = `<span style="color: orange;">${value}</span>`;
		}
		
		return value;
	}
};
