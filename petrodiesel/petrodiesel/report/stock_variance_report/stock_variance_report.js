frappe.query_reports["Stock Variance Report"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -30),
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
            "label": __("Fuel Type"),
            "fieldtype": "Link",
            "options": "Item"
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "status" && data) {
            if (data.status == "High Variance") {
                value = `<span style="color: red; font-weight: bold;">${data.status}</span>`;
            } else if (data.status == "Medium Variance") {
                value = `<span style="color: orange; font-weight: bold;">${data.status}</span>`;
            } else {
                value = `<span style="color: green;">${data.status}</span>`;
            }
        }
        
        return value;
    }
};
