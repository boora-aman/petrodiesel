frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Petro Daily Fuel Sales"] = {
	method: "petrodiesel.petrodiesel.dashboard_chart_source.petro_daily_fuel_sales.petro_daily_fuel_sales.get",
	filters: [
		{ fieldname: "station", label: __("Fuel Station"), fieldtype: "Link", options: "Fuel Station" },
	],
};
