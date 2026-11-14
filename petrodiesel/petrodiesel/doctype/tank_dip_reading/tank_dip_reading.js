// Copyright (c) 2026, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tank Dip Reading", {
	setup(frm) {
		frm.set_query("tank", "readings", () => ({
			filters: { station: frm.doc.station, status: "Active" },
		}));
	},
	async onload(frm) {
		if (frm.is_new() && !frm.doc.station) {
			const station = await frappe.db.get_single_value(
				"Petrodiesel Settings",
				"default_station"
			);
			if (station) frm.set_value("station", station);
		}
	},
	async get_tanks(frm) {
		if (!frm.doc.station) return frappe.msgprint(__("Select a Fuel Station first."));
		const r = await frappe.call(
			"petrodiesel.petrodiesel.doctype.tank_dip_reading.tank_dip_reading.get_tanks",
			{ station: frm.doc.station }
		);
		frm.clear_table("readings");
		(r.message || []).forEach((t) => frm.add_child("readings", t));
		frm.refresh_field("readings");
	},
});

frappe.ui.form.on("Tank Dip Detail", {
	dip_mm: (frm, cdt, cdn) => petro_dip.calc(frm, cdt, cdn),
	water_dip_mm: (frm, cdt, cdn) => petro_dip.calc(frm, cdt, cdn),
});

const petro_dip = {
	async calc(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.tank) return;
		const r = await frappe.call("petrodiesel.petrodiesel.utils.get_dip_volume", {
			tank: row.tank,
			dip_mm: row.dip_mm || 0,
			water_dip_mm: row.water_dip_mm || 0,
		});
		frappe.model.set_value(cdt, cdn, {
			dip_stock: r.message.net,
			water_volume: r.message.water,
		});
	},
};
