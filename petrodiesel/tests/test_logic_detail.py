# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Detailed tests: auto-fetch, auto-calculation, ERPNext postings, chaining,
cancellation, permissions, workflow, DSR maths, dashboards and reports."""

import frappe
from frappe.model.workflow import apply_workflow
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, flt, today

from petrodiesel import demo
from petrodiesel.petrodiesel.doctype.shift_sale_entry.shift_sale_entry import get_nozzles
from petrodiesel.petrodiesel.utils import dip_to_volume, get_fuel_rate, get_tank_book_stock
from petrodiesel.tests.test_petrol_pump import ensure_demo_masters

STATION = demo.STATION
COMPANY = demo.COMPANY
TEST_SHIFTS = [f"Logic Shift {c}" for c in "ABCDEF"]


class TestLogicDetail(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		ensure_demo_masters()
		for i, name in enumerate(TEST_SHIFTS, start=81):
			if not frappe.db.exists("Shift Master", name):
				frappe.get_doc({"doctype": "Shift Master", "shift_name": name, "sequence": i,
					"start_time": "00:00:00", "end_time": "23:00:00", "is_active": 0}).insert()

	def setUp(self):
		frappe.set_user("Administrator")
		for wf in ("Shift Sale Entry Approval", "Tanker Receipt Approval"):
			frappe.db.set_value("Workflow", wf, "is_active", 0)
		frappe.clear_cache()
		self._used = set(frappe.get_all("Shift Sale Entry",
			{"posting_date": today(), "docstatus": ["<", 2], "shift": ["in", TEST_SHIFTS]}, pluck="shift"))

	def tearDown(self):
		frappe.set_user("Administrator")

	# ---------------------------------------------------------------- helpers
	def free_shift(self):
		for s in TEST_SHIFTS:
			if s not in self._used:
				self._used.add(s)
				return s
		self.skipTest("no free test shift")

	def new_shift(self, nozzles=None, sale=50.0, shift=None):
		doc = frappe.new_doc("Shift Sale Entry")
		doc.update({"station": STATION, "posting_date": today(), "shift": shift or self.free_shift()})
		for n in get_nozzles(STATION, today()):
			if nozzles and n["nozzle"] not in nozzles:
				continue
			doc.append("nozzle_readings", {**n, "closing_reading": n["opening_reading"] + sale})
		return doc

	# ---------------------------------------------------------------- auto-fetch
	def test_get_nozzles_fetches_opening_and_rate(self):
		rows = get_nozzles(STATION, today())
		self.assertEqual(len(rows), frappe.db.count("Fuel Nozzle Master", {"station": STATION, "status": "Active"}))
		for r in rows:
			last = frappe.db.get_value("Fuel Nozzle Master", r["nozzle"], "last_reading")
			self.assertEqual(flt(r["opening_reading"]), flt(last))
			self.assertEqual(r["rate"], get_fuel_rate(r["fuel_item"], today()))
			self.assertEqual(r["tank"], frappe.db.get_value("Fuel Nozzle Master", r["nozzle"], "tank"))

	def test_missing_rate_and_item_are_filled_on_validate(self):
		doc = self.new_shift(nozzles=["DU1-N1"])
		row = doc.nozzle_readings[0]
		row.rate = 0
		row.fuel_item = None
		doc.run_method("validate")
		self.assertEqual(row.fuel_item, "MS")
		self.assertEqual(row.rate, get_fuel_rate("MS", today()))

	# ---------------------------------------------------------------- auto-calc
	def test_all_shift_calculations(self):
		ms = get_fuel_rate("MS", today())
		hsd = get_fuel_rate("HSD", today())
		doc = self.new_shift(nozzles=["DU1-N1", "DU1-N2"], sale=200)
		doc.nozzle_readings[0].test_qty = 5  # MS nozzle: 200 metered, 195 sold
		doc.append("credit_sales", {"customer": "Gupta Transport Co.", "vehicle": "HR38AB4521", "fuel_item": "HSD",
			"qty": 50, "rate": hsd, "slip_no": "S1"})
		doc.append("other_sales", {"item_code": "COOLANT-1L", "qty": 2, "rate": 260})
		doc.append("driver_cash", {"customer": "Gupta Transport Co.", "vehicle": "HR38AB4521", "amount": 500})
		doc.append("payments", {"mode_of_payment": "UPI", "amount": 3000})
		doc.append("expenses", {"expense_account": f"Staff Tea and Refreshment - {demo.ABBR}", "amount": 150})
		emp = frappe.db.get_value("Employee", {"company": COMPANY})
		doc.append("employee_advances", {"employee": emp, "amount": 400})
		doc.append("denominations", {"denomination": 500, "count": 10})
		doc.append("denominations", {"denomination": 100, "count": 3})
		doc.run_method("validate")

		ms_row, hsd_row = doc.nozzle_readings
		self.assertEqual(ms_row.meter_qty, 200)
		self.assertEqual(ms_row.sale_qty, 195)
		self.assertAlmostEqual(ms_row.amount, flt(195 * ms, 2))
		self.assertEqual(hsd_row.sale_qty, 200)

		summary = {r.fuel_item: r for r in doc.fuel_summary}
		self.assertEqual(summary["MS"].test_qty, 5)
		self.assertEqual(summary["HSD"].credit_qty, 50)
		self.assertEqual(summary["HSD"].retail_qty, 150)

		retail_fuel = flt(195 * ms + 150 * hsd, 2)
		self.assertAlmostEqual(doc.credit_sales_amount, flt(50 * hsd, 2))
		self.assertAlmostEqual(doc.fuel_sales_amount, flt(retail_fuel + 50 * hsd, 2), places=1)
		self.assertEqual(doc.other_sales_amount, 520)
		self.assertAlmostEqual(doc.gross_sales, doc.fuel_sales_amount + 520, places=1)
		self.assertEqual(doc.total_meter_qty, 400)
		self.assertEqual(doc.total_test_qty, 5)
		self.assertEqual(doc.total_sale_qty, 395)
		expected = flt(retail_fuel + 520 - 3000 - 150 - 400 - 500 + flt(doc.opening_float), 2)
		self.assertAlmostEqual(doc.expected_cash, expected, places=1)
		self.assertEqual(doc.cash_counted, 5300)
		self.assertAlmostEqual(doc.short_excess, flt(5300 - expected, 2), places=1)
		self.assertEqual(doc.denominations[0].amount, 5000)

	def test_price_change_mid_shift_two_rows(self):
		ms = get_fuel_rate("MS", today())
		n = next(r for r in get_nozzles(STATION, today()) if r["nozzle"] == "DU1-N1")
		doc = frappe.new_doc("Shift Sale Entry")
		doc.update({"station": STATION, "posting_date": today(), "shift": self.free_shift()})
		o = n["opening_reading"]
		doc.append("nozzle_readings", {**n, "closing_reading": o + 100, "rate": ms})
		doc.append("nozzle_readings", {**n, "opening_reading": o + 100, "closing_reading": o + 160, "rate": ms + 1})
		demo.count_cash(doc, 0)
		doc.run_method("validate")
		demo.count_cash(doc, doc.expected_cash)
		doc.insert()
		doc.submit()
		si = frappe.get_doc("Sales Invoice", doc.retail_fuel_invoice)
		rates = sorted((round(i.rate, 2), i.qty) for i in si.items)
		self.assertEqual(rates, [(round(ms, 2), 100), (round(ms + 1, 2), 60)])
		self.assertEqual(frappe.db.get_value("Fuel Nozzle Master", "DU1-N1", "last_reading"), o + 160)

	def test_broken_chain_between_rows_rejected(self):
		n = next(r for r in get_nozzles(STATION, today()) if r["nozzle"] == "DU1-N1")
		doc = frappe.new_doc("Shift Sale Entry")
		doc.update({"station": STATION, "posting_date": today(), "shift": self.free_shift()})
		o = n["opening_reading"]
		doc.append("nozzle_readings", {**n, "closing_reading": o + 100})
		doc.append("nozzle_readings", {**n, "opening_reading": o + 90, "closing_reading": o + 150})
		self.assertRaises(frappe.ValidationError, doc.run_method, "validate")

	def test_closing_below_opening_and_bad_test_qty(self):
		doc = self.new_shift(nozzles=["DU1-N1"], sale=-1)
		self.assertRaises(frappe.ValidationError, doc.run_method, "validate")
		doc = self.new_shift(nozzles=["DU1-N1"], sale=4)
		doc.nozzle_readings[0].test_qty = 5
		self.assertRaises(frappe.ValidationError, doc.run_method, "validate")

	def test_duplicate_nozzle_same_shift_rejected(self):
		shift = self.free_shift()
		a = self.new_shift(nozzles=["DU1-N1"], shift=shift)
		a.insert()
		b = self.new_shift(nozzles=["DU1-N1"], shift=shift)
		self.assertRaises(frappe.ValidationError, b.insert)
		a.delete()

	# ---------------------------------------------------------------- postings
	def test_settlement_journal_lines(self):
		hsd = get_fuel_rate("HSD", today())
		doc = self.new_shift(nozzles=["DU1-N2"], sale=300)
		doc.append("credit_sales", {"customer": "Sharma Logistics", "vehicle": "HR26CX9081", "fuel_item": "HSD",
			"qty": 40, "rate": hsd})
		doc.append("driver_cash", {"customer": "Sharma Logistics", "amount": 1000})
		doc.append("payments", {"mode_of_payment": "UPI", "amount": 4000})
		doc.append("payments", {"mode_of_payment": "IOCL Fleet Card", "amount": 1500})
		doc.append("expenses", {"expense_account": f"Outlet Sundry Expenses - {demo.ABBR}", "amount": 200})
		doc.run_method("validate")
		demo.count_cash(doc, doc.expected_cash - 75)
		doc.insert()
		doc.submit()
		je = frappe.get_doc("Journal Entry", doc.settlement_journal)
		self.assertAlmostEqual(je.total_debit, je.total_credit, places=2)
		by_acc = {}
		for a in je.accounts:
			by_acc.setdefault(a.account, [0, 0])
			by_acc[a.account][0] += a.debit
			by_acc[a.account][1] += a.credit
		self.assertAlmostEqual(by_acc[f"HDFC Bank Current A/c - {demo.ABBR}"][0], 4000)
		self.assertAlmostEqual(by_acc[f"IOCL Fleet Card Clearing - {demo.ABBR}"][0], 1500)
		self.assertAlmostEqual(by_acc[f"Outlet Sundry Expenses - {demo.ABBR}"][0], 200)
		self.assertAlmostEqual(by_acc[f"Cash Short and Excess - {demo.ABBR}"][0], 75, places=0)
		cust_line = [a for a in je.accounts if a.party == "Sharma Logistics"]
		self.assertEqual(cust_line[0].debit, 1000)
		cash = frappe.db.get_value("Fuel Station", STATION, "cash_account")
		self.assertAlmostEqual(by_acc[cash][0], doc.cash_counted)
		# credit invoice carries vehicle and slip
		si = frappe.get_all("Sales Invoice", {"shift_sale_entry": doc.name, "customer": "Sharma Logistics"}, pluck="name")
		item = frappe.get_doc("Sales Invoice", si[0]).items[0]
		self.assertEqual(item.petro_vehicle, "HR26CX9081")
		self.assertEqual(frappe.db.get_value("Shift Credit Sale", doc.credit_sales[0].name, "sales_invoice"), si[0])
		# VAT posted on retail fuel invoice, GST template not applied to fuel
		taxes = frappe.get_doc("Sales Invoice", doc.retail_fuel_invoice).taxes
		self.assertTrue(any("VAT" in t.account_head for t in taxes))

	def test_lube_invoice_gst_inclusive(self):
		doc = self.new_shift(nozzles=["DU1-N1"], sale=10)
		doc.append("other_sales", {"item_code": "SERVO-4T-1L", "qty": 1, "rate": 420})
		doc.run_method("validate")
		demo.count_cash(doc, doc.expected_cash)
		doc.insert()
		doc.submit()
		si = frappe.get_doc("Sales Invoice", doc.lube_invoice)
		self.assertAlmostEqual(si.grand_total, 420, places=1)
		self.assertAlmostEqual(si.net_total, 420 / 1.18, places=1)
		self.assertEqual(len(si.taxes), 2)

	def test_next_shift_opening_and_cancel_order(self):
		first = self.new_shift(nozzles=["DU2-N1"], sale=30)
		first.run_method("validate")
		demo.count_cash(first, first.expected_cash)
		first.insert()
		first.submit()
		closing = first.nozzle_readings[0].closing_reading
		n = next(r for r in get_nozzles(STATION, today()) if r["nozzle"] == "DU2-N1")
		self.assertEqual(n["opening_reading"], closing)
		second = self.new_shift(nozzles=["DU2-N1"], sale=20)
		second.run_method("validate")
		demo.count_cash(second, second.expected_cash)
		second.insert()
		second.submit()
		first.reload()
		self.assertRaises(frappe.ValidationError, first.cancel)
		second.cancel()
		self.assertEqual(frappe.db.get_value("Fuel Nozzle Master", "DU2-N1", "last_reading"), closing)
		first.reload()
		first.cancel()
		self.assertEqual(frappe.db.get_value("Fuel Nozzle Master", "DU2-N1", "last_reading"),
			first.nozzle_readings[0].opening_reading)

	def test_credit_limit_stops_shift(self):
		frappe.db.set_value("Customer Credit Limit", {"parent": "Kisan Agro Services", "company": COMPANY},
			"credit_limit", 1)
		doc = self.new_shift(nozzles=["DU1-N2"], sale=100)
		doc.append("credit_sales", {"customer": "Kisan Agro Services", "vehicle": "HR30T1199", "fuel_item": "HSD",
			"qty": 20, "rate": get_fuel_rate("HSD", today())})
		self.assertRaises(frappe.ValidationError, doc.run_method, "validate")

	# ---------------------------------------------------------------- meter change
	def test_meter_change(self):
		last = frappe.db.get_value("Fuel Nozzle Master", "DU2-N3", "last_reading")
		bad = frappe.get_doc({"doctype": "Nozzle Meter Change", "nozzle": "DU2-N3", "posting_date": today(),
			"old_meter_final_reading": last + 5, "new_meter_start_reading": 0})
		self.assertRaises(frappe.ValidationError, bad.insert)
		mc = frappe.get_doc({"doctype": "Nozzle Meter Change", "nozzle": "DU2-N3", "posting_date": today(),
			"old_meter_final_reading": last, "new_meter_start_reading": 10}).insert()
		mc.submit()
		n = next(r for r in get_nozzles(STATION, today()) if r["nozzle"] == "DU2-N3")
		self.assertEqual(n["opening_reading"], 10)
		shift = self.new_shift(nozzles=["DU2-N3"], sale=25)
		shift.run_method("validate")
		demo.count_cash(shift, shift.expected_cash)
		shift.insert()
		shift.submit()
		self.assertRaises(frappe.ValidationError, mc.cancel)
		shift.cancel()
		mc.reload()
		mc.cancel()
		self.assertEqual(frappe.db.get_value("Fuel Nozzle Master", "DU2-N3", "last_reading"), last)

	# ---------------------------------------------------------------- tanker
	def test_tanker_excess_and_checks(self):
		before = get_tank_book_stock("T1-MS", today(), "09:00:00")
		dip_b = demo.volume_to_dip("T1-MS", before)
		dip_a = demo.volume_to_dip("T1-MS", before + 1000 + 20)
		doc = frappe.get_doc({"doctype": "Tanker Receipt", "station": STATION, "posting_date": today(),
			"posting_time": "09:00:00", "supplier": "Indian Oil Corporation Ltd", "supplier_invoice_no": "X-1",
			"truck_no": "HR67Z0001", "seals_intact": 0,
			"items": [{"tank": "T1-MS", "invoice_qty": 1000, "rate": 91, "challan_density": 745,
				"density_at_15": 746, "dip_before_mm": dip_b, "dip_after_mm": dip_a}]})
		self.assertRaises(frappe.ValidationError, doc.insert)  # seals broken without remarks
		doc.remarks = "Seal 2 broken, informed IOCL"
		doc.insert()
		row = doc.items[0]
		self.assertAlmostEqual(row.stock_before, dip_to_volume("T1-MS", dip_b), places=1)
		self.assertAlmostEqual(row.received_qty, row.stock_after - row.stock_before, places=1)
		self.assertLess(row.shortage_qty, 0)
		self.assertEqual(row.density_variance, 1.0)
		self.assertTrue(row.density_ok)
		self.assertEqual(row.amount, 91000)
		doc.submit()
		se = frappe.get_doc("Stock Entry", doc.adjustment_entry)
		self.assertEqual(se.purpose, "Material Receipt")
		self.assertEqual(frappe.db.get_value("Fuel Tank Master", "T1-MS", "last_dip_mm"), dip_a)

	def test_density_override_needs_remarks(self):
		doc = frappe.get_doc({"doctype": "Tanker Receipt", "station": STATION, "posting_date": today(),
			"supplier": "Indian Oil Corporation Ltd", "supplier_invoice_no": "X-2", "truck_no": "HR67Z0002",
			"override_density_check": 1,
			"items": [{"tank": "T2-HSD", "invoice_qty": 500, "rate": 85, "challan_density": 832,
				"density_at_15": 837, "received_qty": 500}]})
		self.assertRaises(frappe.ValidationError, doc.insert)
		doc.remarks = "Accepted under protest"
		doc.insert()
		self.assertFalse(doc.items[0].density_ok)

	# ---------------------------------------------------------------- price update
	def test_price_update_old_price_and_change(self):
		future = add_days(today(), 40)
		old = get_fuel_rate("HSD", add_days(future, -1))
		doc = frappe.get_doc({"doctype": "Fuel Price Update", "effective_date": future,
			"price_list": "Standard Selling", "items": [{"fuel_item": "HSD", "new_price": old - 0.5}]}).insert()
		self.assertEqual(doc.items[0].old_price, old)
		self.assertEqual(doc.items[0].change_amount, -0.5)
		self.assertAlmostEqual(doc.items[0].change_percent, round(-0.5 * 100 / old, 2))
		doc.submit()
		dup = frappe.get_doc({"doctype": "Fuel Price Update", "effective_date": future,
			"price_list": "Standard Selling", "items": [{"fuel_item": "HSD", "new_price": old}]}).insert()
		self.assertRaises(frappe.ValidationError, dup.submit)

	# ---------------------------------------------------------------- dip / DSR
	def test_dip_with_water(self):
		dip = frappe.get_doc({"doctype": "Tank Dip Reading", "station": STATION, "posting_date": today(),
			"posting_time": "10:00:00", "reading_type": "Surprise Check",
			"readings": [{"tank": "T2-HSD", "dip_mm": 1000, "water_dip_mm": 20}]}).insert()
		r = dip.readings[0]
		self.assertAlmostEqual(r.water_volume, dip_to_volume("T2-HSD", 20), places=1)
		self.assertAlmostEqual(r.dip_stock, dip_to_volume("T2-HSD", 1000) - r.water_volume, places=1)
		self.assertAlmostEqual(r.book_stock, get_tank_book_stock("T2-HSD", today(), "10:00:00"), places=1)
		self.assertAlmostEqual(r.variance, r.dip_stock - r.book_stock, places=1)

	def test_dsr_fetch_matches_operations(self):
		date = frappe.db.get_value("Daily Stock Register", {"station": STATION, "docstatus": 1}, "posting_date",
			order_by="posting_date desc")
		if not date:
			self.skipTest("no submitted DSR in demo data")
		existing = frappe.get_doc("Daily Stock Register", {"station": STATION, "posting_date": date, "docstatus": 1})
		fresh = frappe.new_doc("Daily Stock Register")
		fresh.update({"station": STATION, "posting_date": date})
		fresh.set_data()
		fresh.calculate()
		for row in fresh.items:
			sold = frappe.db.sql("""select coalesce(sum(n.meter_qty),0), coalesce(sum(n.test_qty),0)
				from `tabShift Nozzle Reading` n join `tabShift Sale Entry` s on s.name=n.parent
				where s.docstatus=1 and s.posting_date=%s and n.tank=%s""", (date, row.tank))[0]
			self.assertAlmostEqual(row.meter_sales, flt(sold[0]), places=1)
			self.assertAlmostEqual(row.test_qty, flt(sold[1]), places=1)
			rec = frappe.db.sql("""select coalesce(sum(i.received_qty),0) from `tabTanker Receipt Item` i
				join `tabTanker Receipt` t on t.name=i.parent where t.docstatus=1 and t.posting_date=%s
				and i.tank=%s""", (date, row.tank))[0][0]
			self.assertAlmostEqual(row.receipts, flt(rec), places=1)
			prev = frappe.db.sql("""select i.closing_stock from `tabDaily Stock Register Item` i
				join `tabDaily Stock Register` d on d.name=i.parent where d.docstatus=1 and d.posting_date=%s
				and i.tank=%s""", (add_days(date, -1), row.tank))
			if prev:
				self.assertAlmostEqual(row.opening_stock, flt(prev[0][0]), places=1)
			self.assertAlmostEqual(row.net_sales, row.meter_sales - row.test_qty, places=2)
			loss_pct = flt(frappe.db.get_value("Item", row.fuel_item, "permissible_loss_percent"))
			self.assertEqual(flt(row.permissible_percent), loss_pct)
			allowed = loss_pct * row.net_sales / 100
			self.assertEqual(row.within_limit, 1 if row.variance >= -allowed - 0.01 else 0)
		old = {r.tank: r.variance for r in existing.items}
		for row in fresh.items:
			self.assertAlmostEqual(row.variance, old[row.tank], places=1)

	def test_dsr_duplicate_blocked(self):
		date = frappe.db.get_value("Daily Stock Register", {"station": STATION, "docstatus": 1}, "posting_date")
		if not date:
			self.skipTest("no DSR")
		doc = frappe.get_doc({"doctype": "Daily Stock Register", "station": STATION, "posting_date": date})
		self.assertRaises(frappe.ValidationError, doc.insert)

	# ---------------------------------------------------------------- pump test
	def test_failed_pump_test_puts_nozzle_under_maintenance(self):
		doc = frappe.get_doc({"doctype": "Pump Test Log", "station": STATION, "posting_date": today(),
			"tests": [{"nozzle": "DU2-N2", "measure_liters": 5, "error_ml": -30}]}).insert()
		doc.submit()
		self.assertEqual(frappe.db.get_value("Fuel Nozzle Master", "DU2-N2", "status"), "Under Maintenance")
		self.assertNotIn("DU2-N2", [r["nozzle"] for r in get_nozzles(STATION, today())])

	# ---------------------------------------------------------------- masters
	def test_vehicle_number_normalised(self):
		v = frappe.get_doc({"doctype": "Customer Vehicle", "vehicle_no": "hr 10-ab 0001",
			"customer": "Kisan Agro Services"}).insert()
		self.assertEqual(v.name, "HR10AB0001")

	def test_tank_master_validations(self):
		t = frappe.get_doc("Fuel Tank Master", "T1-MS")
		self.assertAlmostEqual(t.current_stock, get_tank_book_stock("T1-MS"), places=1)
		other = frappe.get_doc({"doctype": "Fuel Tank Master", "tank_id": "TX-1", "station": STATION,
			"fuel_item": "MS", "warehouse": t.warehouse, "capacity_liters": 1000})
		self.assertRaises(frappe.ValidationError, other.insert)  # warehouse reused
		lube = frappe.get_doc({"doctype": "Fuel Tank Master", "tank_id": "TX-2", "station": STATION,
			"fuel_item": "COOLANT-1L", "warehouse": f"Lube Store - {demo.ABBR}", "capacity_liters": 1000})
		self.assertRaises(frappe.ValidationError, lube.insert)  # not a fuel

	# ---------------------------------------------------------------- roles & workflow
	def test_role_permissions(self):
		frappe.set_user("cashier@petro.demo")
		self.assertTrue(frappe.has_permission("Shift Sale Entry", "create"))
		self.assertFalse(frappe.has_permission("Shift Sale Entry", "submit"))
		self.assertFalse(frappe.has_permission("Fuel Price Update", "create"))
		self.assertFalse(frappe.has_permission("Petrodiesel Settings", "write"))
		frappe.set_user("stock@petro.demo")
		self.assertTrue(frappe.has_permission("Tanker Receipt", "create"))
		self.assertTrue(frappe.has_permission("Daily Stock Register", "create"))
		self.assertFalse(frappe.has_permission("Shift Sale Entry", "create"))
		frappe.set_user("manager@petro.demo")
		self.assertTrue(frappe.has_permission("Shift Sale Entry", "submit"))
		self.assertTrue(frappe.has_permission("Fuel Price Update", "submit"))
		frappe.set_user("owner@petro.demo")
		self.assertTrue(frappe.has_permission("Petrodiesel Settings", "write"))

	def test_workflow_cashier_cannot_approve(self):
		frappe.db.set_value("Workflow", "Shift Sale Entry Approval", "is_active", 1)
		frappe.clear_cache(doctype="Shift Sale Entry")
		doc = self.new_shift(nozzles=["DU1-N3"], sale=15)
		doc.run_method("validate")
		demo.count_cash(doc, doc.expected_cash)
		doc.insert()
		frappe.set_user("cashier@petro.demo")
		doc = frappe.get_doc("Shift Sale Entry", doc.name)
		doc = apply_workflow(doc, "Submit for Approval")
		self.assertEqual(doc.workflow_state, "Pending Approval")
		self.assertRaises(frappe.ValidationError, apply_workflow, frappe.get_doc("Shift Sale Entry", doc.name), "Approve")
		frappe.set_user("manager@petro.demo")
		doc = apply_workflow(frappe.get_doc("Shift Sale Entry", doc.name), "Approve")
		self.assertEqual(doc.docstatus, 1)
		self.assertTrue(doc.retail_fuel_invoice)

	# ---------------------------------------------------------------- dashboards, reports, jobs
	def test_dashboard_methods(self):
		from petrodiesel import dashboard

		for m in ("todays_fuel_litres", "todays_gross_sales", "todays_credit_sales", "todays_digital",
				"todays_short_excess", "month_gross_sales", "month_fuel_litres", "fuel_stock_litres",
				"credit_outstanding", "month_stock_variance"):
			out = getattr(dashboard, m)()
			self.assertIsInstance(out["value"], (int, float))
		stock = dashboard.fuel_stock_litres()["value"]
		self.assertAlmostEqual(stock, sum(get_tank_book_stock(t[0]) for t in demo.TANKS), places=0)
		for m in ("daily_fuel_sales", "collection_mix", "tank_levels", "daily_stock_variance"):
			out = getattr(dashboard, m)()
			self.assertIn("labels", out)
			self.assertTrue(out["datasets"])

	def test_all_reports_run(self):
		from frappe.desk.query_report import run

		base = {"from_date": add_days(today(), -30), "to_date": today()}
		for name, extra in [("Daily Sales Summary", {}), ("Nozzle Sales Register", {}),
				("Shift Cash Reconciliation", {}), ("Payment Mode Collection", {}), ("Attendant Sales", {}),
				("Tank Stock Status", {}), ("Stock Variance Register", {}), ("Tanker Receipt Register", {}),
				("Fuel Price History", {}), ("Compliance Expiry", {"days": 400}),
				("Credit Customer Statement", {"company": COMPANY, "customer": "Gupta Transport Co."})]:
			res = run(name, filters={**base, **extra})
			self.assertIsInstance(res["result"], list, name)

	def test_daily_job_creates_alerts(self):
		from petrodiesel import tasks

		items = tasks.get_expiring_items(30)
		self.assertTrue(any(i["doctype"] == "Fuel Station" for i in items))
		before = frappe.db.count("Notification Log")
		tasks.daily()
		self.assertGreater(frappe.db.count("Notification Log"), before)

	def test_dsr_closing_only_from_night_dip(self):
		if frappe.db.exists("Daily Stock Register", {"station": STATION, "posting_date": today(), "docstatus": ["<", 2]}):
			self.skipTest("DSR exists for today")
		if frappe.db.exists("Tank Dip Reading", {"posting_date": today(), "reading_type": "Night (Closing)", "docstatus": 1}):
			self.skipTest("night dip exists today")
		dsr = frappe.new_doc("Daily Stock Register")
		dsr.update({"station": STATION, "posting_date": today()})
		dsr.set_data()
		for row in dsr.items:
			self.assertEqual(flt(row.closing_stock), 0)
		dsr.calculate()
		self.assertRaises(frappe.ValidationError, dsr.run_method, "before_submit")
