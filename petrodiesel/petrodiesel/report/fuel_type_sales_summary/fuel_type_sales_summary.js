// Copyright (c) 2025, Your Name and contributors
// For license information, please see license.txt

frappe.query_reports["Fuel Type Sales Summary"] = {
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
            "fieldname": "fuel_item",
            "label": __("Fuel Type"),
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
            "fieldname": "group_by",
            "label": __("Group By"),
            "fieldtype": "Select",
            "options": ["Fuel Type", "Date"],
            "default": "Fuel Type"
        }
    ]
};
