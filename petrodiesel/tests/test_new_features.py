# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Machine-wise collection, cash handover, staff advances, credit bills, shop purchase, stock transfer."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, flt, today

from petrodiesel import demo
from petrodiesel.petrodiesel.advances import advance_outstanding
from petrodiesel.petrodiesel.doctype.shift_sale_entry.shift_sale_entry import get_nozzles
from petrodiesel.petrodiesel.utils import get_fuel_rate, get_tank_book_stock
from petrodiesel.tests.test_petrol_pump import ensure_demo_masters

STATION = demo.STATION
COMPANY = demo.COMPANY
SHIFTS = [f"Feature Shift {c}" for c in "ABCD"]


class TestNewFeatures(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		ensure_demo_masters()
		for i, name in enumerate(SHIFTS, start=71):
			if not frappe.db.exists("Shift Master", name):
				frappe.get_doc({"doctype": "Shift Master", "shift_name": name, "sequence": i, "start_time": "00:00:00",
					"end_time": "23:00:00", "is_active": 0}).insert()
		cls.emp = frappe.db.get_value("Employee", {"company": COMPANY, "designation": "Attendant"})

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_value("Workflow", "Shift Sale Entry Approval", "is_active", 0)
		frappe.clear_cache()

	def _shift(self, shift, nozzles, sale=50.0):
		doc = frappe.new_doc("Shift Sale Entry")
		doc.update({"station": STATION, "posting_date": today(), "shift": shift})
		for n in get_nozzles(STATION, today()):
			if n["nozzle"] in nozzles:
				doc.append("nozzle_readings", {**n, "closing_reading": n["opening_reading"] + sale, "attendant": self.emp})
		return doc

	# ---------------------------------------------------------------- machine-wise
	def test_attendant_reconciliation_and_machine_sales(self):
		hsd = get_fuel_rate("HSD", today())
		emps = frappe.get_all("Employee", {"company": COMPANY, "designation": "Attendant"}, pluck="name", order_by="name")
		a, b = emps[0], emps[1]
		doc = self._shift(SHIFTS[0], ["DU1-N1", "DU1-N2", "DU1-N3", "DU1-N4"], sale=100)
		for r in doc.nozzle_readings:  # side A (N1, N2) = a, side B (N3, N4) = b
			r.attendant = a if r.nozzle in ("DU1-N1", "DU1-N2") else b
		doc.append("credit_sales", {"customer": "Gupta Transport Co.", "vehicle": "HR38AB4521", "fuel_item": "HSD",
			"qty": 20, "rate": hsd, "attendant": b})
		doc.append("payments", {"mode_of_payment": "UPI", "amount": 1000, "attendant": a})
		doc.append("payments", {"mode_of_payment": "UPI", "amount": 500, "attendant": b})
		doc.append("payments", {"mode_of_payment": "UPI", "amount": 200})  # counter, nobody's
		doc.run_method("validate")

		m = {(r.dispensing_unit, r.side): r for r in doc.machine_summary}
		self.assertEqual(set(m), {("DU-1", "A"), ("DU-1", "B")})
		self.assertEqual(m[("DU-1", "A")].sale_qty, 200)
		self.assertEqual(m[("DU-1", "A")].nozzles, "DU1-N1, DU1-N2")

		col = {r.attendant: r for r in doc.attendant_collection}
		self.assertEqual(set(col), {a, b})
		val_a = sum(r.amount for r in doc.nozzle_readings if r.attendant == a)
		val_b = sum(r.amount for r in doc.nozzle_readings if r.attendant == b)
		self.assertAlmostEqual(col[a].expected_cash, flt(val_a - 1000, 2), places=2)
		self.assertAlmostEqual(col[b].credit_amount, flt(20 * hsd, 2))
		self.assertAlmostEqual(col[b].expected_cash, flt(val_b - 20 * hsd - 500, 2), places=2)
		self.assertEqual(col[a].short_excess, 0)  # nothing handed yet → not judged
		col[a].cash_handed = col[a].expected_cash - 50
		col[b].cash_handed = col[b].expected_cash
		doc.run_method("validate")
		col = {r.attendant: r for r in doc.attendant_collection}
		self.assertAlmostEqual(col[a].short_excess, -50, places=2)  # kept across recalculation
		self.assertEqual(col[b].short_excess, 0)
		# drawer: both hand over, counter UPI is not cash → drawer short equals a's short
		demo.count_cash(doc, col[a].cash_handed + col[b].cash_handed)
		doc.run_method("validate")
		# drawer: a is 50 short; counter UPI 200 reduced the cash the drawer should hold → net +150 (before opening cash)
		self.assertAlmostEqual(doc.short_excess, 150 - flt(doc.opening_float), delta=1)

	def test_opening_float_carried_and_posted(self):
		first = self._shift(SHIFTS[1], ["DU1-N3"], sale=30)
		first.run_method("validate")
		demo.count_cash(first, first.expected_cash)
		first.cash_to_next_shift = 1000
		first.insert()
		first.submit()
		self.assertEqual(first.cash_to_safe, flt(first.cash_counted - 1000, 2))

		second = self._shift(SHIFTS[2], ["DU1-N3"], sale=20)
		second.run_method("validate")
		self.assertEqual(second.previous_entry, first.name)
		self.assertEqual(second.opening_float, 1000)
		retail = second.expected_cash - 1000
		demo.count_cash(second, second.expected_cash)  # counted includes the float
		second.insert()
		second.submit()
		self.assertAlmostEqual(second.short_excess, 0, delta=1)
		je = frappe.get_doc("Journal Entry", second.settlement_journal)
		cash = frappe.db.get_value("Fuel Station", STATION, "cash_account")
		cash_dr = sum(a.debit for a in je.accounts if a.account == cash)
		self.assertAlmostEqual(cash_dr, second.cash_counted - 1000, places=2)
		self.assertAlmostEqual(cash_dr, retail, delta=1)
		self.assertAlmostEqual(je.total_debit, je.total_credit, places=2)

	def test_float_cannot_exceed_cash(self):
		doc = self._shift(SHIFTS[3], ["DU2-N1"], sale=5)
		doc.run_method("validate")
		demo.count_cash(doc, 100)
		doc.cash_to_next_shift = 5000
		self.assertRaises(frappe.ValidationError, doc.run_method, "validate")

	# ---------------------------------------------------------------- advances
	def test_staff_advance_give_and_recover(self):
		before = advance_outstanding(self.emp)
		adv = frappe.get_doc({"doctype": "Staff Advance", "employee": self.emp, "station": STATION, "amount": 3000,
			"mode_of_payment": "Cash", "purpose": "Medical", "recovery_method": "Cash Return"}).insert()
		adv.submit()
		self.assertTrue(adv.journal_entry)
		self.assertAlmostEqual(advance_outstanding(self.emp), before + 3000)

		over = frappe.get_doc({"doctype": "Staff Advance Recovery", "employee": self.emp, "station": STATION,
			"amount": before + 5000, "method": "Cash Return"})
		self.assertRaises(frappe.ValidationError, over.insert)

		rec = frappe.get_doc({"doctype": "Staff Advance Recovery", "employee": self.emp, "station": STATION,
			"amount": 1000, "method": "Cash Return", "mode_of_payment": "Cash"}).insert()
		self.assertAlmostEqual(rec.outstanding, before + 3000)
		rec.submit()
		self.assertTrue(rec.journal_entry)
		self.assertAlmostEqual(advance_outstanding(self.emp), before + 2000)

		sal = frappe.get_doc({"doctype": "Staff Advance Recovery", "employee": self.emp, "station": STATION,
			"amount": 500, "method": "Salary Deduction"}).insert()
		sal.submit()
		ads = frappe.get_doc("Additional Salary", sal.additional_salary)
		self.assertEqual(ads.type, "Deduction")
		self.assertEqual(ads.amount, 500)
		self.assertAlmostEqual(advance_outstanding(self.emp), before + 1500)
		sal.cancel()
		self.assertEqual(frappe.db.get_value("Additional Salary", ads.name, "docstatus"), 2)
		self.assertAlmostEqual(advance_outstanding(self.emp), before + 2000)

	# ---------------------------------------------------------------- credit bill
	def test_credit_bill_ties_to_ledger(self):
		frm, to = add_days(today(), -10), today()
		bill = frappe.get_doc({"doctype": "Credit Bill", "customer": "Gupta Transport Co.", "station": STATION,
			"from_date": frm, "to_date": to}).insert()
		self.assertTrue(bill.items)
		gl = frappe.db.sql("""select coalesce(sum(debit-credit),0) from `tabGL Entry` where is_cancelled=0
			and party_type='Customer' and party='Gupta Transport Co.' and posting_date <= %s""", to)[0][0]
		self.assertAlmostEqual(bill.closing_balance, flt(gl), places=1)
		self.assertAlmostEqual(bill.total_billed, sum(r.amount for r in bill.items), places=2)
		bill.submit()

	# ---------------------------------------------------------------- shop purchase & transfer
	def test_shop_purchase_books_stock(self):
		wh = frappe.db.get_value("Fuel Station", STATION, "lube_warehouse")
		before = flt(frappe.db.get_value("Bin", {"item_code": "COOLANT-1L", "warehouse": wh}, "actual_qty"))
		sp = frappe.get_doc({"doctype": "Shop Purchase", "supplier": "Servo Lubricants Distributor", "bill_no": "SV-1",
			"station": STATION, "items": [{"item_code": "COOLANT-1L", "qty": 24, "rate": 190}]}).insert()
		self.assertEqual(sp.warehouse, wh)
		self.assertEqual(sp.total_amount, 4560)
		sp.submit()
		self.assertTrue(sp.purchase_invoice)
		self.assertEqual(flt(frappe.db.get_value("Bin", {"item_code": "COOLANT-1L", "warehouse": wh}, "actual_qty")), before + 24)
		bad = frappe.get_doc({"doctype": "Shop Purchase", "supplier": "Servo Lubricants Distributor", "bill_no": "SV-2",
			"station": STATION, "items": [{"item_code": "HSD", "qty": 10, "rate": 85}]})
		self.assertRaises(frappe.ValidationError, bad.insert)

	def test_tank_to_tank_transfer(self):
		src, dst = "T2-HSD", "T3-HSD"
		a, b = get_tank_book_stock(src), get_tank_book_stock(dst)
		ist = frappe.get_doc({"doctype": "Internal Stock Transfer", "station": STATION, "transfer_type": "Fuel Tank to Tank",
			"from_warehouse": frappe.db.get_value("Fuel Tank Master", src, "warehouse"),
			"to_warehouse": frappe.db.get_value("Fuel Tank Master", dst, "warehouse"),
			"items": [{"item_code": "HSD", "qty": 100}]}).insert()
		ist.submit()
		self.assertAlmostEqual(get_tank_book_stock(src), a - 100, places=1)
		self.assertAlmostEqual(get_tank_book_stock(dst), b + 100, places=1)
		wh = lambda t: frappe.db.get_value("Fuel Tank Master", t, "warehouse")
		lube = frappe.db.get_value("Fuel Station", STATION, "lube_warehouse")
		bad_cases = [
			# MS tank into an HSD tank, whatever item is named
			{"transfer_type": "Fuel Tank to Tank", "from_warehouse": wh("T1-MS"), "to_warehouse": wh(dst), "items": [{"item_code": "MS", "qty": 1}]},
			{"transfer_type": "Fuel Tank to Tank", "from_warehouse": wh("T1-MS"), "to_warehouse": wh(dst), "items": [{"item_code": "HSD", "qty": 1}]},
			# naming a different fuel than the tanks hold
			{"transfer_type": "Fuel Tank to Tank", "from_warehouse": wh(src), "to_warehouse": wh(dst), "items": [{"item_code": "MS", "qty": 1}]},
			# shop-stock type used to pull fuel out of a tank
			{"transfer_type": "Lube / Shop Stock", "from_warehouse": wh(src), "to_warehouse": lube, "items": [{"item_code": "HSD", "qty": 1}]},
			{"transfer_type": "Lube / Shop Stock", "from_warehouse": wh(src), "to_warehouse": wh(dst), "items": [{"item_code": "HSD", "qty": 1}]},
		]
		for case in bad_cases:
			doc = frappe.get_doc({"doctype": "Internal Stock Transfer", "station": STATION, **case})
			self.assertRaises(frappe.ValidationError, doc.insert)
		# item left blank on a tank transfer is filled with the tank's fuel
		auto = frappe.get_doc({"doctype": "Internal Stock Transfer", "station": STATION, "transfer_type": "Fuel Tank to Tank",
			"from_warehouse": wh(src), "to_warehouse": wh(dst), "items": [{"qty": 5}]})
		auto.run_method("validate")
		self.assertEqual(auto.items[0].item_code, "HSD")

	# ---------------------------------------------------------------- reports
	def test_new_reports_run(self):
		from frappe.desk.query_report import run

		base = {"station": STATION, "from_date": add_days(today(), -30), "to_date": today()}
		for name, extra in [("Machine-wise Sales", {}), ("Attendant Collection", {}), ("Staff Advance Balance", {}),
				("Staff Advance Balance", {"employee": self.emp}), ("Cashier Performance", {}),
				("Expense Category Analysis", {}), ("Monthly Sales Analysis", {}), ("Tank Stock Movement", {}),
				("Comprehensive Daily Operations", {"posting_date": add_days(today(), -1)})]:
			res = run(name, filters={**base, **extra})
			self.assertIsInstance(res["result"], list, name)
