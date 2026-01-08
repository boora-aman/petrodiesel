// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.query_reports["Credit Customer Outstanding"] = {
    "filters": [
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -6)
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "fuel_type",
            "label": __("Fuel Type"),
            "fieldtype": "Link",
            "options": "Item",
            "get_query": function() {
                return {
                    "filters": {
                        "item_group": ["in", ["Petrol", "Diesel", "Fuel"]]
                    }
                };
            }
        },
        {
            "fieldname": "min_outstanding",
            "label": __("Min Outstanding Amount"),
            "fieldtype": "Currency"
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "days_overdue" && data && data.days_overdue > 30) {
            value = '<span style="color: red; font-weight: bold;">' + data.days_overdue + '</span>';
        }
        
        if (column.fieldname == "outstanding_amount" && data && data.outstanding_amount > 50000) {
            value = '<span style="color: red; font-weight: bold;">' + value + '</span>';
        }
        
        return value;
    }
};
