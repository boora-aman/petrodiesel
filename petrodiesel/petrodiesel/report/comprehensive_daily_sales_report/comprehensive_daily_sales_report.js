// Copyright (c) 2025, Aman Boora and contributors
// For license information, please see license.txt

frappe.query_reports["Comprehensive Daily Sales Report"] = {
    "filters": [
        {
            "fieldname": "shift",
            "label": __("Shift Sale Entry"),
            "fieldtype": "Link",
            "options": "Shift Sale Entry",
            "reqd": 1,
            "get_query": function() {
                return {
                    "filters": {
                        "docstatus": 1
                    }
                };
            }
        }
    ]
};
