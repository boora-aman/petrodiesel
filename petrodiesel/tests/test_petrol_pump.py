# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""End-to-end tests for the fuel retail workflow.

Run:  bench --site <site> run-tests --app petrodiesel
Uses the demo masters (petrodiesel.demo) and rolls back its own transactions.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, flt, today

from petrodiesel import demo
from petrodiesel.petrodiesel.doctype.shift_sale_entry.shift_sale_entry import get_nozzles
from petrodiesel.petrodiesel.utils import dip_to_volume, get_fuel_rate, get_tank_book_stock

STATION = demo.STATION
COMPANY = demo.COMPANY


def ensure_demo_masters():
	if frappe.db.exists("Fuel Station", STATION):
		clear_pending_shifts()
		return
	demo.ensure_setup_complete()
	demo.ensure_company()
	acc = demo.ensure_accounts(COMPANY)
	demo.ensure_masters(COMPANY, acc)
	demo.opening_stock(COMPANY, add_days(today(), -3))
	demo.price_update(add_days(today(), -3), {k: v[1] for k, v in demo.FUELS.items()})
	frappe.db.commit()


def clear_pending_shifts():
	"""Demo data leaves the latest shift waiting for approval. Shifts must be approved in order,
	so remove such drafts before the tests post their own shifts."""
	for name in frappe.get_all("Shift Sale Entry", {"station": STATION, "docstatus": 0}, pluck="name"):
		frappe.delete_doc("Shift Sale Entry", name, force=True, ignore_permissions=True)
	frappe.db.commit()


class TestPetrolPump(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		ensure_demo_masters()
		cls.date = today()
		for i, name in enumerate(("Test Shift A", "Test Shift B", "Test Shift C", "Test Shift D"), start=91):
			if not frappe.db.exists("Shift Master", name):
				frappe.get_doc(
					{
						"doctype": "Shift Master",
						"shift_name": name,
						"sequence": i,
						"start_time": "00:00:00",
						"end_time": "23:00:00",
						"is_active": 0,
					}
				).insert()

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("Petrodiesel Settings", "require_shift_approval", 0)
		frappe.db.set_value("Workflow", "Shift Sale Entry Approval", "is_active", 0)
		frappe.db.set_value("Workflow", "Tanker Receipt Approval", "is_active", 0)
		frappe.clear_cache()

	# ---------------------------------------------------------------- helpers
	def make_shift(
		self,
		sale_per_nozzle=100.0,
		credit=None,
		lube=None,
		payments=None,
		variance=0.0,
		shift=None,
		date=None,
		submit=True,
	):
		date = date or self.date
		shift = shift or self._free_shift(date)
		doc = frappe.new_doc("Shift Sale Entry")
		doc.update({"station": STATION, "posting_date": date, "shift": shift})
		for n in get_nozzles(STATION, date):
			doc.append("nozzle_readings", {**n, "closing_reading": n["opening_reading"] + sale_per_nozzle})
		for c in credit or []:
			doc.append("credit_sales", c)
		for item, qty in lube or []:
			doc.append("other_sales", {"item_code": item, "qty": qty, "rate": demo.LUBES[item][2]})
		for mop, amt in payments or []:
			doc.append("payments", {"mode_of_payment": mop, "amount": amt})
		doc.run_method("validate")
		demo.count_cash(doc, doc.expected_cash + variance)
		if abs(variance) > 100:
			doc.remarks = "test variance"
		doc.insert()
		if submit:
			doc.submit()
		return doc

	def _free_shift(self, date):
		used = frappe.get_all(
			"Shift Sale Entry",
			{"station": STATION, "posting_date": date, "docstatus": ["<", 2]},
			pluck="shift",
		)
		for s in frappe.get_all(
			"Shift Master", {"shift_name": ["like", "Test Shift%"]}, pluck="name", order_by="sequence"
		):
			if s not in used:
				return s
		self.skipTest("all shifts used for today on this site")

	# ---------------------------------------------------------------- tests
	def test_calibration_interpolation(self):
		chart = frappe.get_all(
			"Tank Calibration Chart",
			{"parent": "T1-MS"},
			["dip_mm", "volume_liters"],
			order_by="dip_mm",
			limit=3,
		)
		mid = (chart[1].dip_mm + chart[2].dip_mm) / 2
		expected = (chart[1].volume_liters + chart[2].volume_liters) / 2
		self.assertAlmostEqual(dip_to_volume("T1-MS", mid), expected, places=1)
		self.assertEqual(dip_to_volume("T1-MS", 0), 0)

	def test_fuel_rate_from_dated_price(self):
		self.assertGreater(get_fuel_rate("MS", self.date), 0)

	def test_shift_posts_invoices_and_settlement(self):
		before = get_tank_book_stock("T2-HSD")
		hsd_rate = get_fuel_rate("HSD", self.date)
		doc = self.make_shift(
			sale_per_nozzle=150,
			credit=[
				{
					"customer": "Gupta Transport Co.",
					"vehicle": "HR38AB4521",
					"slip_no": "T1001",
					"fuel_item": "HSD",
					"qty": 60,
					"rate": hsd_rate,
				}
			],
			lube=[("SERVO-4T-1L", 2)],
			payments=[("UPI", 5000), ("Credit / Debit Card", 1000)],
			variance=-30,
		)
		doc.reload()
		self.assertEqual(doc.docstatus, 1)
		self.assertTrue(doc.retail_fuel_invoice)
		self.assertTrue(doc.lube_invoice)
		self.assertTrue(doc.settlement_journal)
		self.assertAlmostEqual(doc.short_excess, -30, places=0)

		credit_si = frappe.get_all(
			"Sales Invoice",
			{"shift_sale_entry": doc.name, "customer": "Gupta Transport Co.", "docstatus": 1},
			["name", "grand_total", "outstanding_amount"],
		)
		self.assertEqual(len(credit_si), 1)
		self.assertAlmostEqual(credit_si[0].outstanding_amount, flt(60 * hsd_rate, 2), places=0)

		# walk-in invoices fully settled by the journal
		for inv in (doc.retail_fuel_invoice, doc.lube_invoice):
			self.assertAlmostEqual(
				frappe.db.get_value("Sales Invoice", inv, "outstanding_amount"), 0, places=1
			)

		# stock: HSD tank T2 has two nozzles x 150 L
		self.assertAlmostEqual(get_tank_book_stock("T2-HSD"), before - 300, places=1)

		# nozzle totalizer advanced
		row = doc.nozzle_readings[0]
		self.assertEqual(
			frappe.db.get_value("Fuel Nozzle Master", row.nozzle, "last_reading"), row.closing_reading
		)
		self.assertEqual(frappe.db.get_value("Fuel Nozzle Master", row.nozzle, "last_shift_entry"), doc.name)

		# cancel reverts everything
		doc.cancel()
		self.assertEqual(frappe.db.get_value("Sales Invoice", doc.retail_fuel_invoice, "docstatus"), 2)
		self.assertEqual(frappe.db.get_value("Journal Entry", doc.settlement_journal, "docstatus"), 2)
		self.assertEqual(
			frappe.db.get_value("Fuel Nozzle Master", row.nozzle, "last_reading"), row.opening_reading
		)
		self.assertAlmostEqual(get_tank_book_stock("T2-HSD"), before, places=1)

	def test_opening_must_match_last_closing(self):
		doc = self.make_shift(sale_per_nozzle=10, submit=False)
		doc.nozzle_readings[0].opening_reading += 5
		doc.nozzle_readings[0].closing_reading += 5
		doc.save()
		self.assertRaises(frappe.ValidationError, doc.submit)
		doc.delete()

	def test_credit_cannot_exceed_meter_sales(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_shift(
				sale_per_nozzle=10,
				credit=[
					{
						"customer": "Kisan Agro Services",
						"vehicle": "HR30T1199",
						"fuel_item": "HSD",
						"qty": 500,
						"rate": get_fuel_rate("HSD", self.date),
					}
				],
				submit=False,
			)

	def test_vehicle_must_belong_to_customer(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_shift(
				sale_per_nozzle=50,
				credit=[
					{
						"customer": "Kisan Agro Services",
						"vehicle": "HR38AB4521",
						"fuel_item": "HSD",
						"qty": 10,
						"rate": 90,
					}
				],
				submit=False,
			)

	def test_large_cash_shortage_needs_remarks(self):
		doc = self.make_shift(sale_per_nozzle=20, submit=False)
		demo.count_cash(doc, doc.expected_cash - 5000)
		doc.remarks = None
		doc.save()
		self.assertRaises(frappe.ValidationError, doc.submit)
		doc.delete()

	def test_tanker_receipt_books_purchase_and_shortage(self):
		before = get_tank_book_stock("T4-XP95")
		dip_before = demo.volume_to_dip("T4-XP95", before)
		after_qty = before + 2000 - 12
		doc = frappe.get_doc(
			{
				"doctype": "Tanker Receipt",
				"station": STATION,
				"posting_date": self.date,
				"posting_time": "08:00:00",
				"supplier": "Indian Oil Corporation Ltd",
				"supplier_invoice_no": "TEST-INV-1",
				"truck_no": "HR67X0001",
				"items": [
					{
						"tank": "T4-XP95",
						"invoice_qty": 2000,
						"rate": 97.6,
						"challan_density": 748.0,
						"density_at_15": 749.1,
						"dip_before_mm": dip_before,
						"dip_after_mm": demo.volume_to_dip("T4-XP95", after_qty),
					}
				],
			}
		).insert()
		doc.submit()
		doc.reload()
		self.assertTrue(doc.purchase_invoice)
		self.assertAlmostEqual(
			frappe.db.get_value("Purchase Invoice", doc.purchase_invoice, "grand_total"),
			2000 * 97.6,
			places=2,
		)
		self.assertAlmostEqual(doc.items[0].shortage_qty, 12, delta=3)
		self.assertTrue(doc.adjustment_entry)
		self.assertAlmostEqual(
			get_tank_book_stock("T4-XP95"), before + 2000 - doc.items[0].shortage_qty, places=1
		)
		doc.cancel()
		self.assertAlmostEqual(get_tank_book_stock("T4-XP95"), before, places=1)

	def test_density_out_of_tolerance_blocks_receipt(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tanker Receipt",
				"station": STATION,
				"posting_date": self.date,
				"supplier": "Indian Oil Corporation Ltd",
				"supplier_invoice_no": "TEST-INV-2",
				"truck_no": "HR67X0002",
				"items": [
					{
						"tank": "T1-MS",
						"invoice_qty": 1000,
						"rate": 91,
						"challan_density": 745.0,
						"density_at_15": 750.5,
						"received_qty": 1000,
					}
				],
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_price_update_creates_dated_item_price(self):
		future = add_days(today(), 30)
		old = get_fuel_rate("MS", future)
		doc = frappe.get_doc(
			{
				"doctype": "Fuel Price Update",
				"effective_date": future,
				"price_list": "Standard Selling",
				"items": [{"fuel_item": "MS", "new_price": old + 1.5}],
			}
		).insert()
		doc.submit()
		self.assertAlmostEqual(get_fuel_rate("MS", future), old + 1.5)
		self.assertAlmostEqual(get_fuel_rate("MS", add_days(future, -1)), old)
		doc.cancel()
		self.assertAlmostEqual(get_fuel_rate("MS", future), old)

	def test_pump_test_tolerance(self):
		doc = frappe.get_doc(
			{
				"doctype": "Pump Test Log",
				"station": STATION,
				"posting_date": self.date,
				"tests": [
					{"nozzle": "DU1-N1", "measure_liters": 5, "error_ml": 10},
					{"nozzle": "DU1-N2", "measure_liters": 5, "error_ml": -20},
				],
			}
		)
		doc.insert()
		self.assertEqual(doc.tests[0].result, "Pass")
		self.assertEqual(doc.tests[1].result, "Fail")
		self.assertFalse(doc.all_passed)

	def test_dip_reading_and_dsr(self):
		date = today()
		if frappe.db.exists(
			"Daily Stock Register", {"station": STATION, "posting_date": date, "docstatus": ["<", 2]}
		):
			self.skipTest("DSR already exists for today")
		for t, *_ in demo.TANKS:
			self.assertTrue(frappe.db.exists("Fuel Tank Master", t))
		dip = frappe.get_doc(
			{
				"doctype": "Tank Dip Reading",
				"station": STATION,
				"posting_date": date,
				"posting_time": "23:50:00",
				"reading_type": "Night (Closing)",
				"readings": [
					{
						"tank": t,
						"dip_mm": demo.volume_to_dip(t, get_tank_book_stock(t, date, "23:50:00") - 10),
					}
					for t, *_ in demo.TANKS
				],
			}
		)
		dip.insert()
		dip.submit()
		for row in dip.readings:
			self.assertAlmostEqual(row.variance, -10, delta=2)

		dsr = frappe.get_doc(
			{"doctype": "Daily Stock Register", "station": STATION, "posting_date": date}
		).insert()
		self.assertEqual(len(dsr.items), len(demo.TANKS))
		for row in dsr.items:
			self.assertAlmostEqual(
				row.book_closing,
				row.opening_stock + row.receipts + row.transfers - row.net_sales,
				places=1,
			)
			self.assertAlmostEqual(row.variance, row.closing_stock - row.book_closing, places=1)
		dsr.submit()
		dsr.reload()
		self.assertTrue(dsr.stock_reconciliation)
		for row in dsr.items:
			self.assertAlmostEqual(
				get_tank_book_stock(row.tank, date, "23:59:59"), row.closing_stock, places=0
			)
		dsr.cancel()
		dip.cancel()
