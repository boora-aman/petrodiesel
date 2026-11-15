# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Daily Stock Register (DSR), as kept by IOCL/BPCL/HPCL dealers.

Per tank: opening dip stock + receipts - net meter sales = book closing.
Book closing is compared with the closing dip stock to give the day's gain
or loss, checked against the product's permissible loss %. On submit the
ERPNext tank warehouse can be reconciled to the physical dip stock.
"""

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, get_first_day, getdate

from petrodiesel.petrodiesel.utils import (
	dip_to_volume,
	get_settings,
	get_tank_book_stock,
	validate_not_future,
)


class DailyStockRegister(Document):
	ignore_linked_doctypes = (
		"GL Entry",
		"Stock Ledger Entry",
		"Stock Reconciliation",
		"Repost Item Valuation",
		"Serial and Batch Bundle",
	)

	def validate(self):
		self.company = frappe.get_cached_value("Fuel Station", self.station, "company")
		dup = frappe.db.exists(
			"Daily Stock Register",
			{
				"station": self.station,
				"posting_date": self.posting_date,
				"docstatus": ["<", 2],
				"name": ["!=", self.name or ""],
			},
		)
		if dup:
			frappe.throw(_("Daily Stock Register {0} already exists for this date.").format(dup))
		validate_not_future(self.posting_date)
		if self.docstatus == 0:
			self.refresh_data()
		elif not self.items:
			self.set_data()
		self.calculate()

	def refresh_data(self):
		"""Drafts always carry the figures of their own date (the date may have been changed after
		fetching). Closing dips typed by the user are kept."""
		typed = {
			r.tank: (flt(r.closing_dip_mm), flt(r.closing_stock), flt(r.permissible_percent))
			for r in self.items
		}
		self.set("items", [])
		self.set_data()
		for row in self.items:
			if row.tank in typed:
				dip, stock, perm = typed[row.tank]
				if dip:
					row.closing_dip_mm = dip
					row.closing_stock = 0  # recomputed from the dip in calculate()
				elif stock:
					row.closing_stock = stock
				if perm:
					row.permissible_percent = perm

	def calculate(self):
		default_perm = flt(get_settings().default_permissible_loss) or 0.6
		month_start = get_first_day(self.posting_date)
		for row in self.items:
			row.fuel_item = frappe.get_cached_value("Fuel Tank Master", row.tank, "fuel_item")
			if flt(row.closing_dip_mm) < 0:
				frappe.throw(_("Tank {0}: closing dip cannot be negative.").format(row.tank))
			if flt(row.closing_dip_mm):
				row.closing_stock = flt(dip_to_volume(row.tank, row.closing_dip_mm), 2)
			row.net_sales = flt(flt(row.meter_sales) - flt(row.test_qty), 2)
			row.book_closing = flt(
				flt(row.opening_stock) + flt(row.receipts) + flt(row.transfers) - row.net_sales, 2
			)
			if not flt(row.permissible_percent):
				row.permissible_percent = (
					flt(frappe.get_cached_value("Item", row.fuel_item, "permissible_loss_percent"))
					or default_perm
				)
			if not flt(row.closing_stock) and not flt(row.closing_dip_mm):
				# closing dip not taken yet: nothing to compare
				row.variance = row.variance_percent = row.cumulative_variance = 0
				row.within_limit = 1
				continue
			row.variance = flt(flt(row.closing_stock) - row.book_closing, 2)
			row.variance_percent = flt(row.variance * 100 / row.net_sales, 3) if row.net_sales else 0
			if not flt(row.permissible_percent):
				row.permissible_percent = (
					flt(frappe.get_cached_value("Item", row.fuel_item, "permissible_loss_percent"))
					or default_perm
				)
			allowed = flt(row.permissible_percent) * max(row.net_sales, 0) / 100
			row.within_limit = 1 if row.variance >= -allowed - 0.01 else 0
			prior = frappe.db.sql(
				"""
				select coalesce(sum(i.variance), 0) from `tabDaily Stock Register Item` i
				join `tabDaily Stock Register` d on d.name = i.parent
				where d.docstatus = 1 and d.station = %s and i.tank = %s
				and d.posting_date >= %s and d.posting_date < %s and d.name != %s
			""",
				(self.station, row.tank, month_start, self.posting_date, self.name or ""),
			)[0][0]
			row.cumulative_variance = flt(flt(prior) + row.variance, 2)
		self.total_receipts = flt(sum(flt(r.receipts) for r in self.items), 2)
		self.total_sales = flt(sum(flt(r.net_sales) for r in self.items), 2)
		self.total_variance = flt(sum(flt(r.variance) for r in self.items), 2)
		self.all_within_limit = 1 if all(r.within_limit for r in self.items) else 0

	@frappe.whitelist()
	def fetch_data(self):
		self.set("items", [])
		self.set_data()
		self.calculate()
		return self

	def set_data(self):
		date = getdate(self.posting_date)
		tanks = frappe.get_all(
			"Fuel Tank Master",
			{"station": self.station, "status": ["!=", "Inactive"]},
			["name", "fuel_item"],
			order_by="name asc",
		)

		sales = defaultdict(lambda: [0.0, 0.0])
		for r in frappe.db.sql(
			"""
			select n.tank, sum(n.meter_qty) meter, sum(n.test_qty) test
			from `tabShift Nozzle Reading` n join `tabShift Sale Entry` s on s.name = n.parent
			where s.docstatus = 1 and s.station = %s and s.posting_date = %s group by n.tank
		""",
			(self.station, date),
			as_dict=True,
		):
			sales[r.tank] = [flt(r.meter), flt(r.test)]

		receipts = defaultdict(float)
		for r in frappe.db.sql(
			"""
			select i.tank, sum(i.received_qty) qty from `tabTanker Receipt Item` i
			join `tabTanker Receipt` t on t.name = i.parent
			where t.docstatus = 1 and t.station = %s and t.posting_date = %s group by i.tank
		""",
			(self.station, date),
			as_dict=True,
		):
			receipts[r.tank] = flt(r.qty)

		transfers = defaultdict(float)
		for r in frappe.db.sql(
			"""
			select ist.from_warehouse src, ist.to_warehouse dst, sum(i.qty) qty
			from `tabInternal Stock Transfer` ist join `tabInternal Stock Transfer Item` i on i.parent = ist.name
			where ist.docstatus = 1 and ist.station = %s and ist.posting_date = %s
			and ist.transfer_type = 'Fuel Tank to Tank' group by ist.from_warehouse, ist.to_warehouse
		""",
			(self.station, date),
			as_dict=True,
		):
			transfers[r.src] -= flt(r.qty)
			transfers[r.dst] += flt(r.qty)
		tank_wh = dict(
			frappe.get_all("Fuel Tank Master", {"station": self.station}, ["name", "warehouse"], as_list=True)
		)

		for t in tanks:
			opening = self._previous_closing(t.name, date)
			morning = self._dip(t.name, date, first=True, types=("Morning (Opening)",))
			if opening is None:
				opening = (
					flt(morning.dip_stock)
					if morning
					else get_tank_book_stock(t.name, add_days(date, -1), "23:59:59")
				)
			closing = self._dip(t.name, date, first=False, types=("Night (Closing)",))
			self.append(
				"items",
				{
					"tank": t.name,
					"fuel_item": t.fuel_item,
					"opening_stock": flt(opening, 2),
					"receipts": receipts[t.name],
					"transfers": flt(transfers.get(tank_wh.get(t.name), 0), 2),
					"meter_sales": flt(sales[t.name][0], 2),
					"test_qty": flt(sales[t.name][1], 2),
					"closing_dip_mm": closing.dip_mm if closing else 0,
					"closing_stock": flt(closing.dip_stock, 2) if closing else 0,
					"density_at_15": morning.density_at_15 if morning else 0,
				},
			)

	def _previous_closing(self, tank, date):
		val = frappe.db.sql(
			"""
			select i.closing_stock from `tabDaily Stock Register Item` i
			join `tabDaily Stock Register` d on d.name = i.parent
			where d.docstatus = 1 and d.station = %s and i.tank = %s and d.posting_date = %s
		""",
			(self.station, tank, add_days(date, -1)),
		)
		return flt(val[0][0]) if val else None

	def _dip(self, tank, date, first=True, types=None):
		cond = ""
		params = [tank, self.station, date]
		if types:
			cond = "and d.reading_type in %s"
			params.append(types)
		order = "asc" if first else "desc"
		rows = frappe.db.sql(  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.security.frappe-sql-format-injection -- only fixed column/condition fragments are interpolated; values are passed as query params
			f"""
			select r.dip_mm, r.dip_stock, r.density_at_15 from `tabTank Dip Detail` r
			join `tabTank Dip Reading` d on d.name = r.parent
			where r.tank = %s and d.station = %s and d.posting_date = %s and d.docstatus = 1 {cond}
			order by d.posting_time {order} limit 1
		""",
			params,
			as_dict=True,
		)
		return rows[0] if rows else None

	def before_submit(self):
		missing = [r.tank for r in self.items if not flt(r.closing_stock) and not flt(r.closing_dip_mm)]
		if missing:
			frappe.throw(_("Enter the closing dip for tanks: {0}").format(", ".join(missing)))

	def on_submit(self):
		if get_settings().post_dsr_stock_adjustment:
			self.make_stock_reconciliation()

	def on_cancel(self):
		if (
			self.stock_reconciliation
			and frappe.db.get_value("Stock Reconciliation", self.stock_reconciliation, "docstatus") == 1
		):
			doc = frappe.get_doc("Stock Reconciliation", self.stock_reconciliation)
			doc.flags.ignore_permissions = True
			doc.cancel()

	def make_stock_reconciliation(self):
		sr = frappe.new_doc("Stock Reconciliation")
		sr.update(
			{
				"company": self.company,
				"purpose": "Stock Reconciliation",
				"posting_date": self.posting_date,
				"set_posting_time": 1,
				"posting_time": "23:59:59",
				"daily_stock_register": self.name,
				"expense_account": frappe.get_cached_value(
					"Company", self.company, "stock_adjustment_account"
				),
				"cost_center": frappe.get_cached_value("Fuel Station", self.station, "cost_center")
				or frappe.get_cached_value("Company", self.company, "cost_center"),
			}
		)
		for row in self.items:
			wh = frappe.get_cached_value("Fuel Tank Master", row.tank, "warehouse")
			book = get_tank_book_stock(row.tank, self.posting_date, "23:59:59")
			if abs(flt(row.closing_stock) - book) < 0.01:
				continue
			rate = (
				flt(
					frappe.db.get_value(
						"Bin", {"item_code": row.fuel_item, "warehouse": wh}, "valuation_rate"
					)
				)
				or flt(frappe.db.get_value("Item", row.fuel_item, "valuation_rate"))
				or flt(frappe.db.get_value("Item", row.fuel_item, "last_purchase_rate"))
			)
			sr.append(
				"items",
				{
					"item_code": row.fuel_item,
					"warehouse": wh,
					"qty": flt(row.closing_stock, 2),
					"valuation_rate": rate,
				},
			)
		if not sr.items:
			return
		sr.flags.ignore_permissions = True
		sr.insert()
		sr.submit()
		self.db_set("stock_reconciliation", sr.name)
