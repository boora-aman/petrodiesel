// Copyright (c) 2026, Aman Boora and contributors
// For license information, please see license.txt

frappe.ui.form.on("Daily Stock Register", {
	setup(frm) {
		frm.set_query("tank", "items", () => ({ filters: { station: frm.doc.station } }));
	},
	async onload(frm) {
		if (frm.is_new() && !frm.doc.station) {
			const station = await frappe.db.get_single_value("Petrodiesel Settings", "default_station");
			if (station) frm.set_value("station", station);
		}
	},
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.stock_reconciliation) {
			frm.add_custom_button(__("Stock Reconciliation"), () =>
				frappe.set_route("Form", "Stock Reconciliation", frm.doc.stock_reconciliation), __("View"));
		}
		if (frm.doc.items && frm.doc.items.length) {
			const ok = frm.doc.all_within_limit;
			frm.dashboard.clear_headline();
			frm.dashboard.set_headline(`<span class="indicator ${ok ? "green" : "red"}">
				${ok ? __("All tanks within permissible loss") : __("Loss beyond permissible limit")}</span>
				&nbsp; ${__("Net Sales")}: <b>${format_number(frm.doc.total_sales || 0, null, 2)} L</b>
				&nbsp; ${__("Gain/Loss")}: <b>${format_number(frm.doc.total_variance || 0, null, 2)} L</b>`);
		}
	},
	fetch_data(frm) {
		if (!frm.doc.station || !frm.doc.posting_date) return frappe.msgprint(__("Select station and date."));
		frm.call({ doc: frm.doc, method: "fetch_data", freeze: true }).then(() => frm.refresh());
	},
});

frappe.ui.form.on("Daily Stock Register Item", {
	async closing_dip_mm(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.tank || !flt(row.closing_dip_mm)) return;
		const r = await frappe.call("petrodiesel.petrodiesel.utils.get_dip_volume", { tank: row.tank, dip_mm: row.closing_dip_mm });
		await frappe.model.set_value(cdt, cdn, "closing_stock", r.message.gross);
	},
	closing_stock: (frm, cdt, cdn) => petro_dsr.calc(frm, cdt, cdn),
	opening_stock: (frm, cdt, cdn) => petro_dsr.calc(frm, cdt, cdn),
	receipts: (frm, cdt, cdn) => petro_dsr.calc(frm, cdt, cdn),
	meter_sales: (frm, cdt, cdn) => petro_dsr.calc(frm, cdt, cdn),
	test_qty: (frm, cdt, cdn) => petro_dsr.calc(frm, cdt, cdn),
	permissible_percent: (frm, cdt, cdn) => petro_dsr.calc(frm, cdt, cdn),
});

const petro_dsr = {
	calc(frm, cdt, cdn) {
		const r = locals[cdt][cdn];
		r.net_sales = flt(flt(r.meter_sales) - flt(r.test_qty), 2);
		r.book_closing = flt(flt(r.opening_stock) + flt(r.receipts) - r.net_sales, 2);
		r.variance = flt(flt(r.closing_stock) - r.book_closing, 2);
		r.variance_percent = r.net_sales ? flt((r.variance * 100) / r.net_sales, 3) : 0;
		r.within_limit = r.variance >= -(flt(r.permissible_percent) * Math.max(r.net_sales, 0)) / 100 - 0.01 ? 1 : 0;
		const items = frm.doc.items || [];
		frm.doc.total_receipts = flt(items.reduce((a, x) => a + flt(x.receipts), 0), 2);
		frm.doc.total_sales = flt(items.reduce((a, x) => a + flt(x.net_sales), 0), 2);
		frm.doc.total_variance = flt(items.reduce((a, x) => a + flt(x.variance), 0), 2);
		frm.doc.all_within_limit = items.every((x) => x.within_limit) ? 1 : 0;
		frm.refresh_fields();
	},
};
