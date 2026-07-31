frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Combined Daily Fuel Sales"] = {
	method: "petrodiesel.petrodiesel.dashboard_chart_source.combined_daily_fuel_sales.combined_daily_fuel_sales.get",
};
