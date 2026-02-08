# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	return columns, data, None, chart


def get_columns():
	return [
		{
			"fieldname": "tank_name",
			"label": _("Tank Name"),
			"fieldtype": "Link",
			"options": "Fuel Tank Master",
			"width": 150
		},
		{
			"fieldname": "tank_id",
			"label": _("Tank ID"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "fuel_item",
			"label": _("Fuel Type"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 120
		},
		{
			"fieldname": "capacity_kl",
			"label": _("Capacity (KL)"),
			"fieldtype": "Float",
			"width": 110,
			"precision": 2
		},
		{
			"fieldname": "current_stock_level",
			"label": _("Current Stock (KL)"),
			"fieldtype": "Float",
			"width": 130,
			"precision": 2
		},
		{
			"fieldname": "available_space",
			"label": _("Available Space (KL)"),
			"fieldtype": "Float",
			"width": 140,
			"precision": 2
		},
		{
			"fieldname": "fill_percentage",
			"label": _("Fill %"),
			"fieldtype": "Percent",
			"width": 100
		},
		{
			"fieldname": "stock_status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "last_updated_on",
			"label": _("Last Updated"),
			"fieldtype": "Date",
			"width": 110
		},
		{
			"fieldname": "last_receipt_date",
			"label": _("Last Receipt"),
			"fieldtype": "Date",
			"width": 110
		},
		{
			"fieldname": "status",
			"label": _("Tank Status"),
			"fieldtype": "Data",
			"width": 100
		}
	]


def get_data(filters):
	"""Get current tank stock status"""
	
	conditions = "WHERE 1=1"
	
	if filters.get("fuel_item"):
		conditions += " AND fuel_item = %(fuel_item)s"
	
	if filters.get("status"):
		conditions += " AND status = %(status)s"
	
	data = frappe.db.sql("""
		SELECT 
			name as tank_name,
			tank_id,
			fuel_item,
			capacity_in_liters / 1000 as capacity_kl,
			current_stock_level,
			last_updated_on,
			last_receipt_date,
			status
		FROM `tabFuel Tank Master`
		{conditions}
		ORDER BY fuel_item, tank_id
	""".format(conditions=conditions), filters, as_dict=1)
	
	# Calculate derived fields
	for row in data:
		capacity_kl = flt(row.capacity_kl)
		current_stock = flt(row.current_stock_level)
		
		# Available space
		row.available_space = capacity_kl - current_stock
		
		# Fill percentage
		if capacity_kl > 0:
			row.fill_percentage = (current_stock / capacity_kl) * 100
		else:
			row.fill_percentage = 0
		
		# Stock status indicator
		if row.fill_percentage >= 80:
			row.stock_status = "🟢 Good"
		elif row.fill_percentage >= 50:
			row.stock_status = "🟡 Medium"
		elif row.fill_percentage >= 20:
			row.stock_status = "🟠 Low"
		else:
			row.stock_status = "🔴 Critical"
	
	return data


def get_chart_data(data):
	"""Generate chart for tank fill levels"""
	
	labels = []
	fill_percentages = []
	
	for row in data:
		labels.append(f"{row.tank_id} ({row.fuel_item})")
		fill_percentages.append(row.fill_percentage)
	
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Fill Percentage",
					"values": fill_percentages
				}
			]
		},
		"type": "bar",
		"colors": ["#28a745"]
	}
