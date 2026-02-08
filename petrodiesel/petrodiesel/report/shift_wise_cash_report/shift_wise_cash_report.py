# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "posting_date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "shift",
			"label": _("Shift"),
			"fieldtype": "Link",
			"options": "Shift Master",
			"width": 120
		},
		{
			"fieldname": "name",
			"label": _("Entry"),
			"fieldtype": "Link",
			"options": "Shift Sale Entry",
			"width": 180
		},
		{
			"fieldname": "supervisor",
			"label": _("Supervisor"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 140
		},
		{
			"fieldname": "previous_shift_cash",
			"label": _("Opening Cash"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "total_fuel_sales",
			"label": _("Fuel Sales"),
			"fieldtype": "Currency",
			"width": 110
		},
		{
			"fieldname": "total_other_sales",
			"label": _("Other Sales"),
			"fieldtype": "Currency",
			"width": 110
		},
		{
			"fieldname": "total_credit_fuel",
			"label": _("Credit Sales"),
			"fieldtype": "Currency",
			"width": 110
		},
		{
			"fieldname": "total_online",
			"label": _("Online"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "total_driver_cash",
			"label": _("Driver Cash"),
			"fieldtype": "Currency",
			"width": 110
		},
		{
			"fieldname": "total_emp_advances",
			"label": _("Emp Advances"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "total_expenses",
			"label": _("Expenses"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "expected_cash",
			"label": _("Expected Cash"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "cash_received",
			"label": _("Cash Received"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "cash_variance",
			"label": _("Variance"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "cash_given_to_next_shift",
			"label": _("Closing Cash"),
			"fieldtype": "Currency",
			"width": 120
		}
	]


def get_data(filters):
	"""Get shift-wise cash reconciliation report"""
	
	conditions = "WHERE sse.docstatus = 1"
	
	if filters.get("from_date"):
		conditions += " AND sse.posting_date >= %(from_date)s"
	
	if filters.get("to_date"):
		conditions += " AND sse.posting_date <= %(to_date)s"
	
	if filters.get("shift"):
		conditions += " AND sse.shift = %(shift)s"
	
	if filters.get("supervisor"):
		conditions += " AND sse.supervisor = %(supervisor)s"
	
	data = frappe.db.sql("""
		SELECT 
			sse.posting_date,
			sse.shift,
			sse.name,
			sse.supervisor,
			sse.previous_shift_cash,
			sse.total_fuel_sales,
			sse.total_other_sales,
			sse.total_credit_fuel,
			sse.total_online,
			sse.total_driver_cash,
			sse.total_emp_advances,
			sse.total_expenses,
			sse.expected_cash,
			sse.cash_received,
			sse.cash_variance,
			sse.cash_given_to_next_shift
		FROM `tabShift Sale Entry` sse
		{conditions}
		ORDER BY sse.posting_date DESC, sse.shift
	""".format(conditions=conditions), filters, as_dict=1)
	
	return data
