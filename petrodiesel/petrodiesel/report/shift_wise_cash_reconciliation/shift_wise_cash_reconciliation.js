// Copyright (c) 2025, AlfaStack and contributors
// For license information, please see license.txt

frappe.query_reports["Shift-wise Cash Reconciliation"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_days(frappe.datetime.get_today(), -7),
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
		},
		{
			"fieldname": "cashier",
			"label": __("Cashier"),
			"fieldtype": "Link",
			"options": "Employee"
		}
	],
	
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		// Highlight negative variance in red, positive in orange
		if (column.fieldname == "cash_variance" && data) {
			if (data.cash_variance < 0) {
				value = `<span style="color: red; font-weight: bold;">${value}</span>`;
			} else if (data.cash_variance > 0) {
				value = `<span style="color: orange; font-weight: bold;">${value}</span>`;
			} else {
				value = `<span style="color: green;">${value}</span>`;
			}
		}
		
		// Color code status
		if (column.fieldname == "status" && data) {
			if (data.status == "Perfect ✓") {
				value = `<span style="color: green; font-weight: bold;">${value}</span>`;
			} else if (data.status == "Review Required") {
				value = `<span style="color: red; font-weight: bold;">${value}</span>`;
			} else if (data.status == "Good") {
				value = `<span style="color: #29CD42;">${value}</span>`;
			}
		}
		
		// Highlight variance percentage
		if (column.fieldname == "variance_percentage" && data) {
			let pct = Math.abs(data.variance_percentage);
			if (pct > 1) {
				value = `<span style="color: red;">${value}</span>`;
			} else if (pct > 0.5) {
				value = `<span style="color: orange;">${value}</span>`;
			}
		}
		
		return value;
	}
};
