# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Credit Bill: consolidated periodic bill for a credit customer (statement, no GL)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt


class CreditBill(Document):
	def validate(self):
		self.company = frappe.get_cached_value("Fuel Station", self.station, "company")
		if self.from_date > self.to_date:
			frappe.throw(_("From date cannot be after To date."))
		overlap = frappe.db.sql(
			"""select name from `tabCredit Bill` where customer=%s and docstatus=1 and name!=%s
			and from_date <= %s and to_date >= %s limit 1""",
			(self.customer, self.name or "", self.to_date, self.from_date),
		)
		if overlap:
			frappe.msgprint(
				_("Bill {0} already covers part of this period.").format(overlap[0][0]),
				indicator="orange",
				alert=True,
			)
		if not self.items and not self.payments:
			self.set_entries()
		self.calculate()

	def calculate(self):
		self.total_billed = flt(sum(flt(r.amount) for r in self.items), 2)
		self.total_qty = flt(sum(flt(r.qty) for r in self.items), 2)
		self.total_received = flt(sum(flt(r.amount) for r in self.payments), 2)
		self.closing_balance = flt(flt(self.opening_balance) + self.total_billed - self.total_received, 2)

	@frappe.whitelist()
	def fetch_entries(self):
		self.set("items", [])
		self.set("payments", [])
		self.set_entries()
		self.calculate()
		return self

	def set_entries(self):
		args = {
			"customer": self.customer,
			"company": self.company,
			"from": self.from_date,
			"to": self.to_date,
		}
		self.opening_balance = flt(
			frappe.db.sql(
				"""select coalesce(sum(debit - credit), 0) from `tabGL Entry`
			where is_cancelled=0 and company=%(company)s and party_type='Customer' and party=%(customer)s
			and posting_date < %(from)s""",
				args,
			)[0][0]
		)
		for r in frappe.db.sql(
			"""select si.posting_date, si.name sales_invoice, i.petro_vehicle vehicle, i.petro_slip_no slip_no,
				i.item_code, i.qty, i.rate, i.amount
			from `tabSales Invoice Item` i join `tabSales Invoice` si on si.name = i.parent
			where si.docstatus=1 and si.company=%(company)s and si.customer=%(customer)s
			and si.posting_date between %(from)s and %(to)s order by si.posting_date, si.name, i.idx""",
			args,
			as_dict=True,
		):
			self.append("items", r)
		# invoice rounding / tax differences so the bill ties to the ledger
		gl = dict(
			frappe.db.sql(
				"""select voucher_no, sum(debit - credit) from `tabGL Entry`
			where is_cancelled=0 and company=%(company)s and party_type='Customer' and party=%(customer)s
			and voucher_type='Sales Invoice' and posting_date between %(from)s and %(to)s group by voucher_no""",
				args,
			)
		)
		billed = {}
		for r in self.items:
			billed[r.sales_invoice] = billed.get(r.sales_invoice, 0) + flt(r.amount)
		for inv, amt in gl.items():
			diff = flt(amt) - billed.get(inv, 0)
			if abs(diff) >= 0.01:
				self.append(
					"items",
					{
						"posting_date": frappe.db.get_value("Sales Invoice", inv, "posting_date"),
						"sales_invoice": inv,
						"item_code": None,
						"amount": diff,
						"slip_no": _("Adjustment"),
					},
				)
		for r in frappe.db.sql(
			"""select g.posting_date, g.voucher_type, g.voucher_no, sum(g.debit - g.credit) amt,
				(select mode_of_payment from `tabPayment Entry` where name = g.voucher_no) mode
			from `tabGL Entry` g where g.is_cancelled=0 and g.company=%(company)s and g.party_type='Customer'
			and g.party=%(customer)s and g.voucher_type != 'Sales Invoice' and g.posting_date between %(from)s and %(to)s
			group by g.voucher_type, g.voucher_no, g.posting_date order by g.posting_date""",
			args,
			as_dict=True,
		):
			# negative = received; positive (e.g. driver cash journal) is billed
			if flt(r.amt) < 0:
				self.append(
					"payments",
					{
						"posting_date": r.posting_date,
						"voucher_type": r.voucher_type,
						"voucher_no": r.voucher_no,
						"mode_of_payment": r.mode or "",
						"amount": -flt(r.amt),
					},
				)
			else:
				self.append(
					"items",
					{
						"posting_date": r.posting_date,
						"slip_no": _("Driver cash / journal"),
						"amount": flt(r.amt),
					},
				)
		if not self.due_date:
			self.due_date = add_days(self.bill_date or self.to_date, 15)
