frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Petro Daily Stock Variance"] = {
	method: "petrodiesel.petrodiesel.dashboard_chart_source.petro_daily_stock_variance.petro_daily_stock_variance.get",
	filters: [
		{
			fieldname: "station",
			label: __("Fuel Station"),
			fieldtype: "Link",
			options: "Fuel Station",
		},
	],
};
