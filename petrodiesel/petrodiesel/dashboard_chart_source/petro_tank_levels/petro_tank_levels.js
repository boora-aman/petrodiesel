frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Petro Tank Levels"] = {
	method: "petrodiesel.petrodiesel.dashboard_chart_source.petro_tank_levels.petro_tank_levels.get",
	filters: [
		{
			fieldname: "station",
			label: __("Fuel Station"),
			fieldtype: "Link",
			options: "Fuel Station",
		},
	],
};
