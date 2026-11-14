# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Shift Sale Entry: the shift-end closing of a fuel retail outlet.

Meter readings give litres dispensed per nozzle. Credit slips, lubricant
sales, digital collections, expenses, advances and the cash count are
recorded against them. On submit the shift is posted to ERPNext:

* Retail Sales Invoice (walk-in customer, fuel, VAT template, update_stock)
* Lubricant Sales Invoice (walk-in customer, GST template, update_stock)
* One credit Sales Invoice per credit customer (vehicle / slip on each line)
* Settlement Journal Entry that clears the walk-in invoices against cash,
  digital collections, expenses, staff advances, driver cash and short/excess.
"""

from __future__ import annotations

from collections import OrderedDict, defaultdict

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate

from petrodiesel.petrodiesel.utils import (
	get_fuel_rate,
	get_mode_of_payment_account,
	get_settings,
)

QTY_PRECISION = 2
READING_TOLERANCE = 0.01


class ShiftSaleEntry(Document):
	ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Payment Ledger Entry",
		"Sales Invoice", "Journal Entry", "Repost Item Valuation", "Serial and Batch Bundle")

	# ------------------------------------------------------------------ validate
	def validate(self):
		self.validate_station()
		self.set_missing_rates()
		self.calculate_nozzle_rows()
		self.validate_nozzle_rows()
		self.validate_duplicate_nozzles()
		self.validate_credit_rows()
		self.calculate_other_rows()
		self.allocate_fuel()
		self.calculate_totals()
		self.validate_credit_limits()
		if self.docstatus == 0:
			self.status = "Draft"

	def before_submit(self):
		self.validate_reading_chain()
		self.validate_cash_variance()

	def on_submit(self):
		self.status = "Submitted"
		self.db_set("status", "Submitted", update_modified=False)
		self.make_postings()
		self.update_nozzles()

	def before_cancel(self):
		self.validate_cancel_order()

	def on_cancel(self):
		self.revert_nozzles()
		self.cancel_postings()
		self.db_set("status", "Cancelled", update_modified=False)

	# ------------------------------------------------------------------ helpers
	def validate_station(self):
		station = frappe.get_cached_doc("Fuel Station", self.station)
		if not station.is_active:
			frappe.throw(_("Fuel Station {0} is inactive.").format(self.station))
		self.company = station.company

	def set_missing_rates(self):
		for row in self.nozzle_readings:
			if not row.fuel_item and row.nozzle:
				row.fuel_item, row.tank = frappe.db.get_value("Fuel Nozzle Master", row.nozzle, ["fuel_item", "tank"])
			if not flt(row.rate) and row.fuel_item:
				row.rate = get_fuel_rate(row.fuel_item, self.posting_date)
		for row in self.credit_sales:
			if not flt(row.rate) and row.fuel_item:
				row.rate = get_fuel_rate(row.fuel_item, self.posting_date)

	def calculate_nozzle_rows(self):
		for row in self.nozzle_readings:
			row.meter_qty = flt(flt(row.closing_reading) - flt(row.opening_reading), QTY_PRECISION)
			row.test_qty = flt(row.test_qty, QTY_PRECISION)
			row.sale_qty = flt(row.meter_qty - row.test_qty, QTY_PRECISION)
			row.amount = flt(row.sale_qty * flt(row.rate), 2)

	def validate_nozzle_rows(self):
		if not self.nozzle_readings:
			frappe.throw(_("Add at least one nozzle reading."))
		station_nozzles = set(frappe.get_all("Fuel Nozzle Master", {"station": self.station}, pluck="name"))
		for row in self.nozzle_readings:
			if row.nozzle not in station_nozzles:
				frappe.throw(_("Row {0}: Nozzle {1} does not belong to station {2}.").format(row.idx, row.nozzle, self.station))
			if flt(row.closing_reading) < flt(row.opening_reading):
				frappe.throw(
					_("Row {0}: Closing reading {1} is less than opening reading {2} for nozzle {3}. "
					"If the meter was replaced, update the nozzle totalizer first.").format(
						row.idx, row.closing_reading, row.opening_reading, row.nozzle))
			if flt(row.test_qty) < 0 or flt(row.test_qty) > flt(row.meter_qty):
				frappe.throw(_("Row {0}: Test quantity must be between 0 and the meter quantity.").format(row.idx))
			if flt(row.rate) <= 0 and flt(row.sale_qty) > 0:
				frappe.throw(_("Row {0}: Rate is missing for {1}. Submit a Fuel Price Update first.").format(row.idx, row.fuel_item))

		# multiple rows for one nozzle (e.g. price change at 06:00) must chain
		for nozzle, rows in self._rows_by_nozzle().items():
			for prev, cur in zip(rows, rows[1:]):
				if abs(flt(cur.opening_reading) - flt(prev.closing_reading)) > READING_TOLERANCE:
					frappe.throw(
						_("Nozzle {0}: row {1} opening ({2}) must equal row {3} closing ({4}).").format(
							nozzle, cur.idx, cur.opening_reading, prev.idx, prev.closing_reading))

	def _rows_by_nozzle(self):
		out = defaultdict(list)
		for row in self.nozzle_readings:
			out[row.nozzle].append(row)
		for rows in out.values():
			rows.sort(key=lambda r: flt(r.opening_reading))
		return out

	def validate_duplicate_nozzles(self):
		nozzles = list({r.nozzle for r in self.nozzle_readings})
		if not nozzles:
			return
		snr = frappe.qb.DocType("Shift Nozzle Reading")
		sse = frappe.qb.DocType("Shift Sale Entry")
		dup = (
			frappe.qb.from_(snr)
			.join(sse).on(snr.parent == sse.name)
			.select(sse.name, snr.nozzle)
			.where(
				(sse.docstatus < 2) & (sse.name != (self.name or "")) & (sse.station == self.station)
				& (sse.posting_date == self.posting_date) & (sse.shift == self.shift) & (snr.nozzle.isin(nozzles))
			)
			.limit(1)
			.run(as_dict=True)
		)
		if dup:
			frappe.throw(_("Nozzle {0} is already recorded in {1} for this date and shift.").format(
				dup[0].nozzle, frappe.bold(dup[0].name)))

	def validate_reading_chain(self):
		for nozzle, rows in self._rows_by_nozzle().items():
			n = frappe.db.get_value("Fuel Nozzle Master", nozzle,
				["last_reading", "opening_totalizer", "last_reading_on", "last_shift_entry"], as_dict=True)
			expected = flt(n.last_reading)
			if abs(flt(rows[0].opening_reading) - expected) > READING_TOLERANCE:
				frappe.throw(
					_("Nozzle {0}: opening reading {1} does not match the last closing reading {2}{3}. "
					"Submit earlier shifts in order, or correct the reading.").format(
						nozzle, rows[0].opening_reading, expected,
						f" ({n.last_shift_entry})" if n.last_shift_entry else ""))
			if n.last_reading_on and getdate(self.posting_date) < getdate(n.last_reading_on):
				frappe.throw(_("Nozzle {0} already has a reading on {1}, after this business date.").format(
					nozzle, n.last_reading_on))

	def validate_credit_rows(self):
		for row in self.credit_sales:
			if flt(row.qty) <= 0:
				frappe.throw(_("Credit row {0}: quantity must be positive.").format(row.idx))
			if not flt(row.rate):
				frappe.throw(_("Credit row {0}: rate is missing.").format(row.idx))
			row.amount = flt(flt(row.qty) * flt(row.rate), 2)
			if row.vehicle:
				owner, active = frappe.db.get_value("Customer Vehicle", row.vehicle, ["customer", "is_active"])
				if owner != row.customer:
					frappe.throw(_("Credit row {0}: vehicle {1} belongs to {2}, not {3}.").format(
						row.idx, row.vehicle, owner, row.customer))
				if not cint(active):
					frappe.throw(_("Credit row {0}: vehicle {1} is inactive.").format(row.idx, row.vehicle))
		for row in self.driver_cash:
			if flt(row.amount) <= 0:
				frappe.throw(_("Driver cash row {0}: amount must be positive.").format(row.idx))

	def calculate_other_rows(self):
		station_wh = frappe.get_cached_value("Fuel Station", self.station, "lube_warehouse")
		for row in self.other_sales:
			row.amount = flt(flt(row.qty) * flt(row.rate), 2)
			if not row.warehouse:
				row.warehouse = station_wh or frappe.db.get_value(
					"Item Default", {"parent": row.item_code, "company": self.company}, "default_warehouse")
		for row in self.denominations:
			row.amount = flt(cint(row.denomination) * cint(row.count), 2)

	# ------------------------------------------------------------------ fuel allocation
	def allocate_fuel(self):
		"""Split metered fuel into credit slips and retail (walk-in) sales.

		Buckets are (item, rate, warehouse) from nozzle readings. Each credit
		row draws litres from buckets of the same fuel, same rate first.
		"""
		buckets: OrderedDict = OrderedDict()
		for row in self.nozzle_readings:
			wh = frappe.get_cached_value("Fuel Tank Master", row.tank, "warehouse")
			key = (row.fuel_item, flt(row.rate), wh)
			buckets[key] = flt(buckets.get(key, 0) + flt(row.sale_qty), QTY_PRECISION)

		credit_alloc = []  # (credit_row, warehouse, qty)
		for crow in self.credit_sales:
			need = flt(crow.qty, QTY_PRECISION)
			keys = sorted(
				[k for k in buckets if k[0] == crow.fuel_item and buckets[k] > 0],
				key=lambda k: (k[1] != flt(crow.rate), -buckets[k]),
			)
			for k in keys:
				if need <= 0:
					break
				take = min(need, buckets[k])
				buckets[k] = flt(buckets[k] - take, QTY_PRECISION)
				need = flt(need - take, QTY_PRECISION)
				credit_alloc.append((crow, k[2], take))
			if need > READING_TOLERANCE:
				frappe.throw(
					_("Credit sales of {0} exceed metered sales by {1} L. Check the slips and meter readings.").format(
						frappe.bold(crow.fuel_item), need))

		self._buckets = buckets
		self._credit_alloc = credit_alloc

		summary = OrderedDict()
		for row in self.nozzle_readings:
			s = summary.setdefault(row.fuel_item, defaultdict(float))
			s["meter_qty"] += flt(row.meter_qty)
			s["test_qty"] += flt(row.test_qty)
			s["sale_qty"] += flt(row.sale_qty)
			s["amount"] += flt(row.amount)
		for crow in self.credit_sales:
			if crow.fuel_item in summary:
				summary[crow.fuel_item]["credit_qty"] += flt(crow.qty)
		self.set("fuel_summary", [])
		for item, s in summary.items():
			self.append("fuel_summary", {
				"fuel_item": item,
				"meter_qty": flt(s["meter_qty"], QTY_PRECISION),
				"test_qty": flt(s["test_qty"], QTY_PRECISION),
				"sale_qty": flt(s["sale_qty"], QTY_PRECISION),
				"credit_qty": flt(s["credit_qty"], QTY_PRECISION),
				"retail_qty": flt(s["sale_qty"] - s["credit_qty"], QTY_PRECISION),
				"amount": flt(s["amount"], 2),
			})

	def calculate_totals(self):
		self.total_meter_qty = flt(sum(flt(r.meter_qty) for r in self.nozzle_readings), QTY_PRECISION)
		self.total_test_qty = flt(sum(flt(r.test_qty) for r in self.nozzle_readings), QTY_PRECISION)
		self.total_sale_qty = flt(sum(flt(r.sale_qty) for r in self.nozzle_readings), QTY_PRECISION)

		retail_fuel = flt(sum(qty * rate for (item, rate, wh), qty in self._buckets.items()), 2)
		self.credit_sales_amount = flt(sum(flt(r.amount) for r in self.credit_sales), 2)
		self.fuel_sales_amount = flt(retail_fuel + self.credit_sales_amount, 2)
		self.other_sales_amount = flt(sum(flt(r.amount) for r in self.other_sales), 2)
		self.gross_sales = flt(self.fuel_sales_amount + self.other_sales_amount, 2)

		self.digital_amount = flt(sum(flt(r.amount) for r in self.payments), 2)
		self.expense_amount = flt(sum(flt(r.amount) for r in self.expenses), 2)
		self.advance_amount = flt(sum(flt(r.amount) for r in self.employee_advances), 2)
		self.driver_cash_amount = flt(sum(flt(r.amount) for r in self.driver_cash), 2)

		self.retail_amount = flt(retail_fuel + self.other_sales_amount, 2)
		self.expected_cash = flt(
			self.retail_amount - self.digital_amount - self.expense_amount
			- self.advance_amount - self.driver_cash_amount, 2)
		self.cash_counted = flt(sum(flt(r.amount) for r in self.denominations), 2)
		self.short_excess = flt(self.cash_counted - self.expected_cash, 2)

	def validate_credit_limits(self):
		if not self.credit_sales:
			return
		from erpnext.selling.doctype.customer.customer import get_credit_limit, get_customer_outstanding

		per_customer = defaultdict(float)
		for r in self.credit_sales:
			per_customer[r.customer] += flt(r.amount)
		for r in self.driver_cash:
			per_customer[r.customer] += flt(r.amount)
		for customer, amount in per_customer.items():
			limit = flt(get_credit_limit(customer, self.company))
			if not limit:
				continue
			outstanding = flt(get_customer_outstanding(customer, self.company, ignore_outstanding_sales_order=True))
			if outstanding + amount > limit:
				msg = _("Credit limit of {0} exceeded: limit {1}, outstanding {2}, this shift {3}.").format(
					frappe.bold(customer), frappe.format(limit, "Currency"),
					frappe.format(outstanding, "Currency"), frappe.format(amount, "Currency"))
				frappe.throw(msg, title=_("Credit Limit Exceeded"))

	def validate_cash_variance(self):
		tol = flt(get_settings().cash_variance_tolerance)
		if tol and abs(flt(self.short_excess)) > tol and not self.remarks:
			frappe.throw(_("Cash {0} of {1} is above the tolerance of {2}. Enter the reason in Remarks.").format(
				_("shortage") if self.short_excess < 0 else _("excess"),
				frappe.format(abs(self.short_excess), "Currency"), frappe.format(tol, "Currency")))

	# ------------------------------------------------------------------ postings
	def make_postings(self):
		settings = get_settings()
		station = frappe.get_cached_doc("Fuel Station", self.station)
		self.allocate_fuel()

		# retail fuel invoice
		retail_items = [
			{"item_code": item, "qty": qty, "rate": rate, "warehouse": wh}
			for (item, rate, wh), qty in self._buckets.items() if qty > 0
		]
		if retail_items:
			si = self._make_invoice(station.walk_in_customer, retail_items, settings.fuel_tax_template,
				_("Retail fuel sales"))
			self.db_set("retail_fuel_invoice", si.name)

		# lubricant / shop invoice
		lube_items = [
			{"item_code": r.item_code, "qty": r.qty, "rate": r.rate, "warehouse": r.warehouse}
			for r in self.other_sales if flt(r.qty)
		]
		if lube_items:
			si = self._make_invoice(station.walk_in_customer, lube_items, settings.lube_tax_template,
				_("Lubricant and shop sales"))
			self.db_set("lube_invoice", si.name)

		# credit invoices, one per customer
		by_customer = OrderedDict()
		for crow, wh, qty in self._credit_alloc:
			by_customer.setdefault(crow.customer, []).append((crow, wh, qty))
		for customer, allocs in by_customer.items():
			items = []
			for crow, wh, qty in allocs:
				desc = " | ".join(x for x in [
					crow.fuel_item,
					f"Vehicle: {crow.vehicle}" if crow.vehicle else "",
					f"Slip: {crow.slip_no}" if crow.slip_no else "",
					f"Driver: {crow.driver_name}" if crow.driver_name else "",
				] if x)
				items.append({"item_code": crow.fuel_item, "qty": qty, "rate": crow.rate, "warehouse": wh,
					"description": desc, "petro_vehicle": crow.vehicle, "petro_slip_no": crow.slip_no})
			slips = ", ".join(sorted({c.slip_no for c, _w, _q in allocs if c.slip_no}))
			si = self._make_invoice(customer, items, settings.fuel_tax_template,
				_("Credit fuel sales") + (f" (slips {slips})" if slips else ""), po_no=slips[:140] or None)
			for crow in {c.name: c for c, _w, _q in allocs}.values():
				crow.db_set("sales_invoice", si.name)

		self.make_settlement_journal(station)

	def _make_invoice(self, customer, items, tax_template, remarks, po_no=None):
		si = frappe.new_doc("Sales Invoice")
		si.update({
			"company": self.company,
			"customer": customer,
			"posting_date": self.posting_date,
			"set_posting_time": 1,
			"posting_time": self.end_time or "23:59:00",
			"due_date": self.posting_date,
			"update_stock": 1,
			"ignore_pricing_rule": 1,
			"disable_rounded_total": 1,
			"cost_center": frappe.get_cached_value("Fuel Station", self.station, "cost_center"),
			"fuel_station": self.station,
			"shift_sale_entry": self.name,
			"remarks": f"{remarks} - {self.name}",
			"po_no": po_no,
		})
		for it in items:
			row = si.append("items", {
				"item_code": it["item_code"],
				"qty": it["qty"],
				"rate": it["rate"],
				"price_list_rate": it["rate"],
				"warehouse": it["warehouse"],
			})
			for f in ("description", "petro_vehicle", "petro_slip_no"):
				if it.get(f):
					row.set(f, it[f])
		si.set_missing_values()
		if tax_template:
			si.taxes_and_charges = tax_template
			si.set("taxes", [])
			si.append_taxes_from_master()
		for row in si.items:
			row.rate = row.price_list_rate
		si.calculate_taxes_and_totals()
		si.flags.ignore_permissions = True
		si.insert()
		si.submit()
		return si

	def make_settlement_journal(self, station):
		from erpnext.accounts.party import get_party_account

		cost_center = station.cost_center
		lines = []

		def add(account, debit=0.0, credit=0.0, party_type=None, party=None, ref=None, remark=None):
			if not flt(debit) and not flt(credit):
				return
			acct_type = frappe.get_cached_value("Account", account, "account_type")
			row = {"account": account, "debit_in_account_currency": flt(debit, 2),
				"credit_in_account_currency": flt(credit, 2), "cost_center": cost_center,
				"user_remark": remark}
			if party and acct_type in ("Receivable", "Payable"):
				row.update({"party_type": party_type, "party": party})
			if ref:
				row.update({"reference_type": "Sales Invoice", "reference_name": ref})
			lines.append(row)

		walkin = station.walk_in_customer
		debtors = get_party_account("Customer", walkin, self.company)
		for inv in (self.retail_fuel_invoice, self.lube_invoice):
			if inv:
				gt = flt(frappe.db.get_value("Sales Invoice", inv, "grand_total"))
				add(debtors, credit=gt, party_type="Customer", party=walkin, ref=inv)

		add(station.cash_account, debit=self.cash_counted, remark=_("Cash counted"))
		per_account = defaultdict(float)
		for p in self.payments:
			per_account[get_mode_of_payment_account(p.mode_of_payment, self.company)] += flt(p.amount)
		for account, amount in per_account.items():
			add(account, debit=amount, remark=_("Digital collections"))
		for e in self.expenses:
			add(e.expense_account, debit=e.amount, remark=e.description)
		if self.employee_advances:
			if not station.employee_advance_account:
				frappe.throw(_("Set Employee Advance Account on Fuel Station {0}.").format(self.station))
			for a in self.employee_advances:
				add(station.employee_advance_account, debit=a.amount, party_type="Employee", party=a.employee,
					remark=a.remarks)
		for d in self.driver_cash:
			add(get_party_account("Customer", d.customer, self.company), debit=d.amount,
				party_type="Customer", party=d.customer,
				remark=f"Driver cash {d.vehicle or ''} slip {d.slip_no or ''}".strip())

		total_dr = sum(flt(r["debit_in_account_currency"]) for r in lines)
		total_cr = sum(flt(r["credit_in_account_currency"]) for r in lines)
		diff = flt(total_cr - total_dr, 2)
		if diff > 0:
			add(station.cash_short_excess_account, debit=diff, remark=_("Cash shortage"))
		elif diff < 0:
			add(station.cash_short_excess_account, credit=-diff, remark=_("Cash excess"))
		if not lines:
			return

		je = frappe.new_doc("Journal Entry")
		je.update({
			"voucher_type": "Journal Entry",
			"company": self.company,
			"posting_date": self.posting_date,
			"user_remark": _("Shift settlement {0} ({1}, {2})").format(self.name, self.shift, self.posting_date),
			"shift_sale_entry": self.name,
		})
		for r in lines:
			je.append("accounts", r)
		je.flags.ignore_permissions = True
		je.insert()
		je.submit()
		self.db_set("settlement_journal", je.name)

	def cancel_postings(self):
		docs = []
		if self.settlement_journal:
			docs.append(("Journal Entry", self.settlement_journal))
		for name in frappe.get_all("Sales Invoice", {"shift_sale_entry": self.name, "docstatus": 1}, pluck="name"):
			docs.append(("Sales Invoice", name))
		for doctype, name in docs:
			doc = frappe.get_doc(doctype, name)
			if doc.docstatus == 1:
				doc.flags.ignore_permissions = True
				doc.flags.ignore_links = True
				doc.cancel()

	# ------------------------------------------------------------------ nozzles
	def update_nozzles(self):
		for nozzle, rows in self._rows_by_nozzle().items():
			frappe.db.set_value("Fuel Nozzle Master", nozzle, {
				"last_reading": flt(rows[-1].closing_reading),
				"last_shift_entry": self.name,
				"last_reading_on": self.posting_date,
			})

	def validate_cancel_order(self):
		for nozzle in self._rows_by_nozzle():
			last_entry = frappe.db.get_value("Fuel Nozzle Master", nozzle, "last_shift_entry")
			if last_entry and last_entry != self.name:
				frappe.throw(_("Nozzle {0} has a later shift {1}. Cancel that shift first.").format(nozzle, last_entry))
			if frappe.db.exists("Nozzle Meter Change", {"nozzle": nozzle, "docstatus": 1,
					"posting_date": [">=", self.posting_date], "creation": [">", self.creation]}):
				frappe.throw(_("Nozzle {0} had a meter change after this shift. Cancel the meter change first.").format(nozzle))

	def revert_nozzles(self):
		for nozzle, rows in self._rows_by_nozzle().items():
			prev = get_previous_entry_for_nozzle(nozzle, exclude=self.name)
			frappe.db.set_value("Fuel Nozzle Master", nozzle, {
				"last_reading": flt(rows[0].opening_reading),
				"last_shift_entry": prev.name if prev else None,
				"last_reading_on": prev.posting_date if prev else None,
			})


def get_previous_entry_for_nozzle(nozzle, exclude=None):
	snr = frappe.qb.DocType("Shift Nozzle Reading")
	sse = frappe.qb.DocType("Shift Sale Entry")
	sm = frappe.qb.DocType("Shift Master")
	rows = (
		frappe.qb.from_(snr)
		.join(sse).on(snr.parent == sse.name)
		.left_join(sm).on(sm.name == sse.shift)
		.select(sse.name, sse.posting_date)
		.where((snr.nozzle == nozzle) & (sse.docstatus == 1) & (sse.name != (exclude or "")))
		.orderby(sse.posting_date, order=frappe.qb.desc)
		.orderby(sm.sequence, order=frappe.qb.desc)
		.orderby(snr.closing_reading, order=frappe.qb.desc)
		.limit(1)
		.run(as_dict=True)
	)
	return rows[0] if rows else None


@frappe.whitelist()
def get_nozzles(station: str, posting_date: str | None = None) -> list[dict]:
	"""Active nozzles of a station with opening reading and the day's rate."""
	frappe.has_permission("Shift Sale Entry", "create", throw=True)
	nozzles = frappe.get_all(
		"Fuel Nozzle Master",
		filters={"station": station, "status": "Active"},
		fields=["name", "fuel_item", "tank", "last_reading", "opening_totalizer", "last_shift_entry"],
		order_by="dispensing_unit asc, name asc",
	)
	out = []
	for n in nozzles:
		opening = flt(n.last_reading)
		out.append({
			"nozzle": n.name,
			"fuel_item": n.fuel_item,
			"tank": n.tank,
			"opening_reading": opening,
			"closing_reading": opening,
			"rate": get_fuel_rate(n.fuel_item, posting_date),
		})
	return out


@frappe.whitelist()
def get_default_denominations() -> list[int]:
	return [500, 200, 100, 50, 20, 10, 5, 2, 1]
