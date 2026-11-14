// Copyright (c) 2026, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pump Test Log", {
	setup(frm) {
		frm.set_query("nozzle", "tests", () => ({ filters: { station: frm.doc.station } }));
	},
	async onload(frm) {
		if (frm.is_new() && !frm.doc.station) {
			const station = await frappe.db.get_single_value("Petrodiesel Settings", "default_station");
			if (station) frm.set_value("station", station);
		}
	},
});
