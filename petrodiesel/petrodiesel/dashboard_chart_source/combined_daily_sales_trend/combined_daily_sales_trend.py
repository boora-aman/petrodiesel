import frappe
from frappe.utils import formatdate, getdate, nowdate
from frappe.utils.dashboard import cache_source


@frappe.whitelist()
@cache_source
def get(
	chart_name=None,
	chart=None,
	no_cache=None,
	filters=None,
	from_date=None,
	to_date=None,
	timespan=None,
	time_interval=None,
	heatmap_year=None,
):
	if chart_name:
		chart = frappe.get_doc("Dashboard Chart", chart_name)
	else:
		chart = frappe._dict(frappe.parse_json(chart))

	filters = frappe.parse_json(filters) or frappe.parse_json(chart.filters_json)

	to_date = to_date or chart.to_date or nowdate()
	from_date = from_date or chart.from_date

	data = frappe.db.sql(
		"""
		SELECT posting_date, SUM(total_sales) AS value
		FROM (
			SELECT posting_date, SUM(total_sales) AS total_sales
			FROM `tabShift Sale Entry`
			WHERE docstatus = 1
				AND posting_date BETWEEN %(from_date)s AND %(to_date)s
			GROUP BY posting_date
			UNION ALL
			SELECT posting_date, SUM(total_sales) AS total_sales
			FROM `tabCashier Wise Shift Sale Entry`
			WHERE docstatus = 1
				AND posting_date BETWEEN %(from_date)s AND %(to_date)s
			GROUP BY posting_date
		) combined
		GROUP BY posting_date
		ORDER BY posting_date
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=1,
	)

	labels = [formatdate(getdate(r.posting_date).strftime("%Y-%m-%d")) for r in data]
	values = [float(r.value or 0) for r in data]

	return {
		"labels": labels,
		"datasets": [{"name": "Total Sales", "values": values}],
	}
