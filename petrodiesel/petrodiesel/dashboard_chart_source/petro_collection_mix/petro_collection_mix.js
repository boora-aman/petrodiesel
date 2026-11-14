frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Petro Collection Mix"] = {
	method: "petrodiesel.petrodiesel.dashboard_chart_source.petro_collection_mix.petro_collection_mix.get",
	filters: [
		{
			fieldname: "station",
			label: __("Fuel Station"),
			fieldtype: "Link",
			options: "Fuel Station",
		},
	],
};
