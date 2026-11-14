// Copyright (c) 2026, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tanker Receipt", {
	setup(frm) {
		frm.set_query("tank", "items", () => ({ filters: { station: frm.doc.station, status: "Active" } }));
	},
	async onload(frm) {
		if (frm.is_new() && !frm.doc.station) {
			const station = await frappe.db.get_single_value("Petrodiesel Settings", "default_station");
			if (station) frm.set_value("station", station);
		}
	},
	refresh(frm) {
		if (frm.doc.docstatus === 1) {
			if (frm.doc.purchase_invoice) {
				frm.add_custom_button(__("Purchase Invoice"), () =>
					frappe.set_route("Form", "Purchase Invoice", frm.doc.purchase_invoice), __("View"));
			}
			frm.add_custom_button(__("Stock Entries"), () =>
				frappe.set_route("List", "Stock Entry", { tanker_receipt: frm.doc.name }), __("View"));
		}
		const short = flt(frm.doc.total_shortage_qty);
		if (frm.doc.items && frm.doc.items.length) {
			frm.dashboard.clear_headline();
			frm.dashboard.set_headline(
				`${__("Invoiced")}: <b>${format_number(frm.doc.total_invoice_qty || 0, null, 2)} L</b> &nbsp;
				 ${__("Received")}: <b>${format_number(frm.doc.total_received_qty || 0, null, 2)} L</b> &nbsp;
				 <span class="indicator ${short > 0 ? "red" : "green"}">${short > 0 ? __("Short") : __("Excess")}
				 ${format_number(Math.abs(short), null, 2)} L</span>`
			);
		}
	},
});

frappe.ui.form.on("Tanker Receipt Item", {
	async tank(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.tank) return;
		const t = await frappe.db.get_value("Fuel Tank Master", row.tank, "fuel_item");
		const item = t.message.fuel_item;
		if (row.fuel_item !== item) await frappe.model.set_value(cdt, cdn, "fuel_item", item);
		const r = await frappe.db.get_value("Item", item, "last_purchase_rate");
		if (!row.rate && r.message.last_purchase_rate) {
			frappe.model.set_value(cdt, cdn, "rate", r.message.last_purchase_rate);
		}
	},
	invoice_qty: (frm, cdt, cdn) => petro_tr.calc(frm, cdt, cdn),
	rate: (frm, cdt, cdn) => petro_tr.calc(frm, cdt, cdn),
	dip_before_mm: (frm, cdt, cdn) => petro_tr.calc(frm, cdt, cdn),
	dip_after_mm: (frm, cdt, cdn) => petro_tr.calc(frm, cdt, cdn),
	sales_during_decantation: (frm, cdt, cdn) => petro_tr.calc(frm, cdt, cdn),
	challan_density: (frm, cdt, cdn) => petro_tr.calc(frm, cdt, cdn),
	density_at_15: (frm, cdt, cdn) => petro_tr.calc(frm, cdt, cdn),
});

const petro_tr = {
	async vol(tank, mm) {
		if (!tank || !flt(mm)) return 0;
		const r = await frappe.call("petrodiesel.petrodiesel.utils.get_dip_volume", { tank, dip_mm: mm });
		return r.message.net;
	},
	async calc(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		row.amount = flt(flt(row.invoice_qty) * flt(row.rate), 2);
		if (flt(row.dip_before_mm) || flt(row.dip_after_mm)) {
			row.stock_before = await petro_tr.vol(row.tank, row.dip_before_mm);
			row.stock_after = await petro_tr.vol(row.tank, row.dip_after_mm);
			row.received_qty = flt(row.stock_after - row.stock_before + flt(row.sales_during_decantation), 2);
		}
		row.shortage_qty = flt(flt(row.invoice_qty) - flt(row.received_qty), 2);
		if (flt(row.challan_density) && flt(row.density_at_15)) {
			const tol = flt(await frappe.db.get_single_value("Petrodiesel Settings", "density_tolerance")) || 3;
			row.density_variance = flt(row.density_at_15 - row.challan_density, 1);
			row.density_ok = Math.abs(row.density_variance) <= tol ? 1 : 0;
			if (!row.density_ok) {
				frappe.show_alert({ message: __("Density variance {0} kg/m³ exceeds ±{1}", [row.density_variance, tol]), indicator: "red" });
			}
		}
		const sum = (f) => (frm.doc.items || []).reduce((a, r) => a + flt(r[f]), 0);
		frm.doc.total_invoice_qty = flt(sum("invoice_qty"), 2);
		frm.doc.total_received_qty = flt(sum("received_qty"), 2);
		frm.doc.total_shortage_qty = flt(sum("shortage_qty"), 2);
		frm.doc.total_amount = flt(sum("amount"), 2);
		frm.refresh_fields();
	},
};
