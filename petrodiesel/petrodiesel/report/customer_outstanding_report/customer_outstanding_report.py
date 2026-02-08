# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "customer",
			"label": _("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150
		},
		{
			"fieldname": "customer_name",
			"label": _("Customer Name"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "total_credit_sales",
			"label": _("Total Credit Sales"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "total_payments",
			"label": _("Total Payments"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "outstanding_amount",
			"label": _("Outstanding Amount"),
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"fieldname": "credit_limit",
			"label": _("Credit Limit"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "credit_utilization",
			"label": _("Utilization %"),
			"fieldtype": "Percent",
			"width": 100
		},
		{
			"fieldname": "last_credit_date",
			"label": _("Last Credit Date"),
			"fieldtype": "Date",
			"width": 110
		},
		{
			"fieldname": "last_payment_date",
			"label": _("Last Payment Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "days_outstanding",
			"label": _("Days Outstanding"),
			"fieldtype": "Int",
			"width": 120
		}
	]


def get_data(filters):
	"""
	Get customer outstanding summary.
	Uses SINGLE SOURCE OF TRUTH: Credit Sale documents only.
	Payments are tracked via Customer Payment Entry and reflected in Credit Sale.paid_amount
	"""
	
	conditions = ""
	if filters.get("customer"):
		conditions += " AND cs.customer = %(customer)s"
	
	if filters.get("from_date"):
		conditions += " AND cs.posting_date >= %(from_date)s"
	
	if filters.get("to_date"):
		conditions += " AND cs.posting_date <= %(to_date)s"
	
	# Get customer-wise outstanding from Credit Sale documents
	# This aggregates all credit sales and their payment status
	data = frappe.db.sql("""
		SELECT 
			cs.customer,
			c.customer_name,
			SUM(cs.total_amount) as total_credit_sales,
			SUM(cs.paid_amount) as total_payments,
			SUM(cs.outstanding_amount) as outstanding_amount,
			c.credit_limit,
			MAX(cs.posting_date) as last_credit_date,
			DATEDIFF(CURDATE(), MAX(cs.posting_date)) as days_outstanding
		FROM `tabCredit Sale` cs
		LEFT JOIN `tabCustomer` c ON c.name = cs.customer
		WHERE cs.docstatus = 1
		{conditions}
		GROUP BY cs.customer
		HAVING outstanding_amount > 0
		ORDER BY outstanding_amount DESC
	""".format(conditions=conditions), filters, as_dict=1)
	
	# Get last payment date for each customer from Customer Payment Entry
	for row in data:
		last_payment = frappe.db.sql("""
			SELECT MAX(posting_date) as last_payment_date
			FROM `tabCustomer Payment Entry`
			WHERE customer = %s
			AND docstatus = 1
		""", row.customer)
		
		row.last_payment_date = last_payment[0][0] if last_payment and last_payment[0][0] else None
		
		# Calculate credit utilization percentage
		if row.credit_limit and flt(row.credit_limit) > 0:
			row.credit_utilization = (flt(row.outstanding_amount) / flt(row.credit_limit)) * 100
		else:
			row.credit_utilization = 0
	
	return data
