// Copyright (c) 2026, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fuel Price Update", {
	setup(frm) {
		frm.set_query("fuel_item", "items", () => ({ filters: { petro_product_type: "Fuel" } }));
	},
	async onload(frm) {
		if (frm.is_new() && !frm.doc.price_list) {
			frm.set_value("price_list", await frappe.db.get_single_value("Petrodiesel Settings", "fuel_price_list"));
		}
	},
	async get_items(frm) {
		const r = await frappe.call("petrodiesel.petrodiesel.doctype.fuel_price_update.fuel_price_update.get_fuel_items",
			{ effective_date: frm.doc.effective_date, price_list: frm.doc.price_list });
		frm.clear_table("items");
		(r.message || []).forEach((i) => frm.add_child("items", i));
		frm.refresh_field("items");
	},
});

frappe.ui.form.on("Fuel Price Update Item", {
	new_price(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		row.change_amount = flt(row.new_price - row.old_price, 2);
		row.change_percent = row.old_price ? flt((row.change_amount * 100) / row.old_price, 2) : 0;
		frm.refresh_field("items");
	},
});
