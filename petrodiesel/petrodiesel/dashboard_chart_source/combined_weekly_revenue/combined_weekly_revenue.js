frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Combined Weekly Revenue"] = {
	method: "petrodiesel.petrodiesel.dashboard_chart_source.combined_weekly_revenue.combined_weekly_revenue.get",
};
