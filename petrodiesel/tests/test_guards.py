# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Guards added after the logic audit: dates, duplicates, rates, cancellation from the desk."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from petrodiesel import demo
from petrodiesel.tests.test_petrol_pump import ensure_demo_masters

STATION = demo.STATION


class TestGuards(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		ensure_demo_masters()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_future_dates_rejected(self):
		tank = demo.TANKS[0][0]
		dip = frappe.get_doc(
			{
				"doctype": "Tank Dip Reading",
				"station": STATION,
				"posting_date": add_days(today(), 2),
				"posting_time": "06:00:00",
				"reading_type": "Morning (Opening)",
				"readings": [{"tank": tank, "dip_mm": 900}],
			}
		)
		self.assertRaises(frappe.ValidationError, dip.insert)

	def test_water_dip_above_product_dip(self):
		dip = frappe.get_doc(
			{
				"doctype": "Tank Dip Reading",
				"station": STATION,
				"posting_date": today(),
				"posting_time": "06:00:00",
				"reading_type": "Morning (Opening)",
				"readings": [{"tank": demo.TANKS[0][0], "dip_mm": 100, "water_dip_mm": 150}],
			}
		)
		self.assertRaises(frappe.ValidationError, dip.insert)

	def test_second_entry_for_same_shift_rejected(self):
		existing = frappe.get_all(
			"Shift Sale Entry",
			{"station": STATION, "docstatus": 1},
			["posting_date", "shift"],
			order_by="posting_date desc",
			limit=1,
		)
		if not existing:
			self.skipTest("no submitted shift")
		dup = frappe.get_doc(
			{
				"doctype": "Shift Sale Entry",
				"station": STATION,
				"posting_date": existing[0].posting_date,
				"shift": existing[0].shift,
				"nozzle_readings": [],
			}
		)
		self.assertRaisesRegex(frappe.ValidationError, "already entered", dup.insert)

	def test_posted_invoice_cannot_be_cancelled_from_desk(self):
		name = frappe.db.get_value(
			"Shift Sale Entry", {"station": STATION, "docstatus": 1}, "retail_fuel_invoice"
		)
		if not name:
			self.skipTest("no posted shift")
		si = frappe.get_doc("Sales Invoice", name)
		self.assertRaisesRegex(frappe.ValidationError, "Cancel .* in PetroDesk", si.cancel)

	def test_dsr_draft_follows_its_date(self):
		day1 = add_days(today(), -40)
		dsr = frappe.get_doc(
			{"doctype": "Daily Stock Register", "station": STATION, "posting_date": day1}
		).insert()
		before = {r.tank: r.meter_sales for r in dsr.items}
		last = frappe.db.get_value(
			"Daily Stock Register",
			{"station": STATION, "docstatus": 1},
			"posting_date",
			order_by="posting_date desc",
		)
		if not last:
			self.skipTest("no DSR to compare with")
		# move the draft onto a day that has sales: figures must be refetched for that day
		frappe.db.delete("Daily Stock Register", {"name": dsr.name})
		dsr2 = frappe.get_doc(
			{
				"doctype": "Daily Stock Register",
				"station": STATION,
				"posting_date": add_days(last, -1) if last else day1,
				"items": [{"tank": t, "meter_sales": v} for t, v in before.items()],
			}
		)
		if frappe.db.exists(
			"Daily Stock Register",
			{"station": STATION, "posting_date": dsr2.posting_date, "docstatus": ["<", 2]},
		):
			# that day already has a register; use a day without one
			dsr2.posting_date = add_days(today(), -41)
		dsr2.insert()
		fresh = frappe.get_doc(
			{"doctype": "Daily Stock Register", "station": STATION, "posting_date": dsr2.posting_date}
		)
		fresh.set_data()
		self.assertEqual(
			{r.tank: r.meter_sales for r in dsr2.items}, {r.tank: r.meter_sales for r in fresh.items}
		)

	def test_cashier_cannot_change_rate(self):
		if not frappe.db.exists("User", "cashier@petro.demo"):
			self.skipTest("demo cashier missing")
		nozzle = frappe.get_all("Fuel Nozzle Master", {"station": STATION, "status": "Active"}, limit=1)[
			0
		].name
		n = frappe.get_doc("Fuel Nozzle Master", nozzle)
		frappe.set_user("cashier@petro.demo")
		doc = frappe.get_doc(
			{
				"doctype": "Shift Sale Entry",
				"station": STATION,
				"posting_date": add_days(today(), -60),
				"shift": frappe.get_all("Shift Master", limit=1)[0].name,
				"nozzle_readings": [
					{
						"nozzle": nozzle,
						"opening_reading": n.last_reading,
						"closing_reading": n.last_reading + 10,
						"rate": 1.23,
					}
				],
			}
		)
		self.assertRaisesRegex(frappe.ValidationError, "does not match the price list", doc.validate)
