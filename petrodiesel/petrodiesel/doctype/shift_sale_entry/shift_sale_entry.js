// Copyright (c) 2026, Aman Boora and contributors
// For license information, please see license.txt

const SSE_METHOD = "petrodiesel.petrodiesel.doctype.shift_sale_entry.shift_sale_entry";

frappe.ui.form.on("Shift Sale Entry", {
	setup(frm) {
		frm.set_query("nozzle", "nozzle_readings", () => ({
			filters: { station: frm.doc.station, status: "Active" },
		}));
		frm.set_query("vehicle", "credit_sales", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			return { filters: { customer: row.customer, is_active: 1 } };
		});
		frm.set_query("vehicle", "driver_cash", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			return { filters: { customer: row.customer, is_active: 1 } };
		});
		frm.set_query("fuel_item", "credit_sales", () => ({
			filters: { petro_product_type: "Fuel" },
		}));
		frm.set_query("item_code", "other_sales", () => ({
			filters: { petro_product_type: ["in", ["Lubricant", "Accessory", "Other"]], is_sales_item: 1 },
		}));
		frm.set_query("expense_account", "expenses", () => ({
			filters: { company: frm.doc.company, root_type: "Expense", is_group: 0 },
		}));
		frm.set_query("shift", () => ({ filters: { is_active: 1 } }));
	},

	async onload(frm) {
		if (frm.is_new() && !frm.doc.station) {
			const station = await frappe.db.get_single_value("Petrodiesel Settings", "default_station");
			if (station) frm.set_value("station", station);
		}
		if (frm.is_new() && !frm.doc.cashier) {
			const emp = await frappe.db.get_value("Employee", { user_id: frappe.session.user, status: "Active" }, "name");
			if (emp.message && emp.message.name) frm.set_value("cashier", emp.message.name);
		}
		if (frm.is_new() && !(frm.doc.denominations || []).length) {
			const r = await frappe.call(`${SSE_METHOD}.get_default_denominations`);
			(r.message || []).forEach((d) => frm.add_child("denominations", { denomination: d, count: 0 }));
			frm.refresh_field("denominations");
		}
	},

	refresh(frm) {
		if (frm.doc.docstatus === 1) {
			["retail_fuel_invoice", "lube_invoice", "settlement_journal"].forEach((f) => {
				if (frm.doc[f]) {
					const dt = f === "settlement_journal" ? "Journal Entry" : "Sales Invoice";
					frm.add_custom_button(__(frappe.meta.get_label(frm.doctype, f)), () =>
						frappe.set_route("Form", dt, frm.doc[f]), __("View"));
				}
			});
			frm.add_custom_button(__("All Invoices"), () =>
				frappe.set_route("List", "Sales Invoice", { shift_sale_entry: frm.doc.name }), __("View"));
			frm.add_custom_button(__("General Ledger"), () =>
				frappe.set_route("query-report", "General Ledger", {
					company: frm.doc.company, from_date: frm.doc.posting_date, to_date: frm.doc.posting_date,
				}), __("View"));
		}
		petro_sse.show_cash_indicator(frm);
	},

	station(frm) {
		frm.set_value("nozzle_readings", []);
	},

	async get_nozzles(frm) {
		if (!frm.doc.station) {
			frappe.msgprint(__("Select a Fuel Station first."));
			return;
		}
		const r = await frappe.call({
			method: `${SSE_METHOD}.get_nozzles`,
			args: { station: frm.doc.station, posting_date: frm.doc.posting_date },
			freeze: true,
		});
		frm.clear_table("nozzle_readings");
		(r.message || []).forEach((n) => frm.add_child("nozzle_readings", n));
		frm.refresh_field("nozzle_readings");
		petro_sse.recalc(frm);
	},
});

frappe.ui.form.on("Shift Nozzle Reading", {
	async nozzle(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.nozzle) return;
		const r = await frappe.call({
			method: `${SSE_METHOD}.get_nozzles`,
			args: { station: frm.doc.station, posting_date: frm.doc.posting_date },
		});
		const n = (r.message || []).find((x) => x.nozzle === row.nozzle);
		if (n) {
			// a second row for the same nozzle (price change) continues from the previous closing
			const prev = (frm.doc.nozzle_readings || []).filter((x) => x.nozzle === row.nozzle && x.name !== row.name);
			const opening = prev.length ? Math.max(...prev.map((x) => flt(x.closing_reading))) : n.opening_reading;
			await frappe.model.set_value(cdt, cdn, { opening_reading: opening, rate: n.rate });
		}
	},
	opening_reading: (frm) => petro_sse.recalc(frm),
	closing_reading: (frm) => petro_sse.recalc(frm),
	test_qty: (frm) => petro_sse.recalc(frm),
	rate: (frm) => petro_sse.recalc(frm),
	nozzle_readings_remove: (frm) => petro_sse.recalc(frm),
});

frappe.ui.form.on("Shift Credit Sale", {
	async vehicle(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.vehicle) return;
		const v = await frappe.db.get_value("Customer Vehicle", row.vehicle, ["fuel_item", "driver_name"]);
		const vals = {};
		if (v.message.fuel_item && !row.fuel_item) vals.fuel_item = v.message.fuel_item;
		if (v.message.driver_name && !row.driver_name) vals.driver_name = v.message.driver_name;
		if (Object.keys(vals).length) await frappe.model.set_value(cdt, cdn, vals);
	},
	async fuel_item(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.fuel_item) return;
		const nz = (frm.doc.nozzle_readings || []).find((x) => x.fuel_item === row.fuel_item && x.rate);
		let rate = nz ? nz.rate : 0;
		if (!rate) {
			const r = await frappe.call("petrodiesel.petrodiesel.utils.get_rate", {
				item_code: row.fuel_item, posting_date: frm.doc.posting_date,
			});
			rate = r.message;
		}
		await frappe.model.set_value(cdt, cdn, "rate", rate);
	},
	qty: (frm) => petro_sse.recalc(frm),
	rate: (frm) => petro_sse.recalc(frm),
	credit_sales_remove: (frm) => petro_sse.recalc(frm),
});

frappe.ui.form.on("Shift Other Sales", {
	async item_code(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.item_code) return;
		const r = await frappe.call("petrodiesel.petrodiesel.utils.get_rate", {
			item_code: row.item_code, posting_date: frm.doc.posting_date,
		});
		await frappe.model.set_value(cdt, cdn, { rate: r.message, qty: row.qty || 1 });
	},
	qty: (frm) => petro_sse.recalc(frm),
	rate: (frm) => petro_sse.recalc(frm),
	other_sales_remove: (frm) => petro_sse.recalc(frm),
});

["Shift Payment", "Shift Expense Detail", "Shift Employee Advance", "Shift Driver Cash"].forEach((dt) => {
	const table = {
		"Shift Payment": "payments", "Shift Expense Detail": "expenses",
		"Shift Employee Advance": "employee_advances", "Shift Driver Cash": "driver_cash",
	}[dt];
	frappe.ui.form.on(dt, {
		amount: (frm) => petro_sse.recalc(frm),
		[`${table}_remove`]: (frm) => petro_sse.recalc(frm),
	});
});

frappe.ui.form.on("Shift Cash Denomination", {
	denomination: (frm) => petro_sse.recalc(frm),
	count: (frm) => petro_sse.recalc(frm),
});

const petro_sse = {
	recalc(frm) {
		const d = frm.doc;
		const sum = (rows, f) => (rows || []).reduce((a, r) => a + flt(r[f]), 0);
		(d.nozzle_readings || []).forEach((r) => {
			r.meter_qty = flt(flt(r.closing_reading) - flt(r.opening_reading), 2);
			r.sale_qty = flt(r.meter_qty - flt(r.test_qty), 2);
			r.amount = flt(r.sale_qty * flt(r.rate), 2);
		});
		(d.credit_sales || []).forEach((r) => (r.amount = flt(flt(r.qty) * flt(r.rate), 2)));
		(d.other_sales || []).forEach((r) => (r.amount = flt(flt(r.qty) * flt(r.rate), 2)));
		(d.denominations || []).forEach((r) => (r.amount = flt(cint(r.denomination) * cint(r.count), 2)));

		// retail fuel = metered value minus credit litres at meter rate (server re-allocates exactly)
		const meterValue = sum(d.nozzle_readings, "amount");
		let creditAtMeter = 0;
		(d.credit_sales || []).forEach((c) => {
			const nz = (d.nozzle_readings || []).find((n) => n.fuel_item === c.fuel_item);
			creditAtMeter += flt(c.qty) * flt(nz ? nz.rate : c.rate);
		});
		const retailFuel = meterValue - creditAtMeter;

		d.total_meter_qty = flt(sum(d.nozzle_readings, "meter_qty"), 2);
		d.total_test_qty = flt(sum(d.nozzle_readings, "test_qty"), 2);
		d.total_sale_qty = flt(sum(d.nozzle_readings, "sale_qty"), 2);
		d.credit_sales_amount = flt(sum(d.credit_sales, "amount"), 2);
		d.fuel_sales_amount = flt(retailFuel + d.credit_sales_amount, 2);
		d.other_sales_amount = flt(sum(d.other_sales, "amount"), 2);
		d.gross_sales = flt(d.fuel_sales_amount + d.other_sales_amount, 2);
		d.digital_amount = flt(sum(d.payments, "amount"), 2);
		d.expense_amount = flt(sum(d.expenses, "amount"), 2);
		d.advance_amount = flt(sum(d.employee_advances, "amount"), 2);
		d.driver_cash_amount = flt(sum(d.driver_cash, "amount"), 2);
		d.expected_cash = flt(retailFuel + d.other_sales_amount - d.digital_amount - d.expense_amount
			- d.advance_amount - d.driver_cash_amount, 2);
		d.cash_counted = flt(sum(d.denominations, "amount"), 2);
		d.short_excess = flt(d.cash_counted - d.expected_cash, 2);

		frm.refresh_fields();
		petro_sse.show_cash_indicator(frm);
	},

	show_cash_indicator(frm) {
		if (!frm.doc.nozzle_readings || !frm.doc.nozzle_readings.length) return;
		const se = flt(frm.doc.short_excess);
		const color = Math.abs(se) < 1 ? "green" : se < 0 ? "red" : "orange";
		const label = Math.abs(se) < 1 ? __("Cash Tallied") : se < 0 ? __("Short {0}", [format_currency(-se)])
			: __("Excess {0}", [format_currency(se)]);
		frm.dashboard.clear_headline();
		frm.dashboard.set_headline(
			`<span class="indicator ${color}">${label}</span> &nbsp; ${__("Sale")}: <b>${format_number(frm.doc.total_sale_qty || 0, null, 2)} L</b>
			 &nbsp; ${__("Gross")}: <b>${format_currency(frm.doc.gross_sales || 0)}</b>
			 &nbsp; ${__("Expected Cash")}: <b>${format_currency(frm.doc.expected_cash || 0)}</b>`
		);
	},
};
