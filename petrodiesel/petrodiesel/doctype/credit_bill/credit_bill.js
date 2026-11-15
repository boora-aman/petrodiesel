// Copyright (c) 2026, Aman Boora and contributors
frappe.ui.form.on("Credit Bill", {
	async onload(frm) {
		if (frm.is_new() && !frm.doc.station)
			frm.set_value(
				"station",
				await frappe.db.get_single_value("Petrodiesel Settings", "default_station")
			);
	},
	fetch_entries(frm) {
		if (!frm.doc.customer || !frm.doc.from_date || !frm.doc.to_date)
			return frappe.msgprint(__("Select customer and period."));
		frm.call({ doc: frm.doc, method: "fetch_entries", freeze: true }).then(() =>
			frm.refresh()
		);
	},
});
