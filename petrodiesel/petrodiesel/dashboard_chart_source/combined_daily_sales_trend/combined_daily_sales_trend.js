frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Combined Daily Sales Trend"] = {
	method: "petrodiesel.petrodiesel.dashboard_chart_source.combined_daily_sales_trend.combined_daily_sales_trend.get",
};
