# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""JSON API for the PetroDesk (Vue / frappe-ui) frontend.

Standard Frappe endpoints (frappe.client.*, frappe.model.workflow.*,
frappe.desk.query_report.run) are used for CRUD; this module adds the
aggregate and preview endpoints the screens need.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, now_datetime, today

from petrodiesel import dashboard as dash
from petrodiesel.petrodiesel.utils import get_fuel_rate, get_settings, get_tank_book_stock

PUMP_ROLES = ("Pump Owner", "Pump Manager", "Pump Cashier", "Pump Stock Keeper")
PREVIEW_DOCTYPES = (
	"Shift Sale Entry",
	"Tanker Receipt",
	"Tank Dip Reading",
	"Daily Stock Register",
	"Pump Test Log",
	"Fuel Price Update",
	"Nozzle Meter Change",
	"Staff Advance",
	"Staff Advance Recovery",
	"Credit Bill",
	"Shop Purchase",
	"Internal Stock Transfer",
)


def _station(station=None):
	return station or get_settings().default_station


def _role_view(roles):
	if "Pump Owner" in roles or "System Manager" in roles:
		return "owner"
	if "Pump Manager" in roles:
		return "manager"
	if "Pump Stock Keeper" in roles and "Pump Cashier" not in roles:
		return "stock"
	if "Pump Cashier" in roles:
		return "cashier"
	return "viewer"


# ------------------------------------------------------------------ session / boot
@frappe.whitelist()
def boot():
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Not logged in"), frappe.AuthenticationError)
	roles = frappe.get_roles(user)
	station = _station()
	st = (
		frappe.db.get_value(
			"Fuel Station",
			station,
			["name", "station_name", "omc", "ro_code", "address", "company"],
			as_dict=True,
		)
		if station
		else None
	)
	employee = frappe.db.get_value(
		"Employee", {"user_id": user, "status": "Active"}, ["name", "employee_name"], as_dict=True
	)
	fuels = frappe.get_all(
		"Item", {"petro_product_type": "Fuel", "disabled": 0}, ["name", "item_name"], order_by="name"
	)
	can = {
		dt: {p: bool(frappe.has_permission(dt, p)) for p in ("read", "create", "submit")}
		for dt in (*PREVIEW_DOCTYPES, "Customer", "Payment Entry", "Petrodiesel Settings")
	}
	machines = (
		frappe.get_all(
			"Dispensing Unit",
			{"station": station, "status": ["!=", "Inactive"]},
			["name", "make", "status"],
			order_by="name",
		)
		if station
		else []
	)
	return {
		"user": user,
		"full_name": frappe.utils.get_fullname(user),
		"user_image": frappe.db.get_value("User", user, "user_image"),
		"roles": [r for r in roles if r in PUMP_ROLES or r == "System Manager"],
		"view": _role_view(roles),
		"employee": employee,
		"station": st,
		"stations": frappe.get_all("Fuel Station", {"is_active": 1}, ["name", "ro_code", "omc"]),
		"shifts": frappe.get_all(
			"Shift Master",
			{"is_active": 1},
			["name", "start_time", "end_time", "sequence"],
			order_by="sequence",
		),
		"fuels": [{**f, "rate": get_fuel_rate(f.name, today())} for f in fuels],
		"today": today(),
		"can": can,
		"settings": {
			k: get_settings().get(k)
			for k in (
				"density_tolerance",
				"pump_test_tolerance_ml",
				"cash_variance_tolerance",
				"require_shift_approval",
				"default_permissible_loss",
			)
		},
		"counts": counts(),
		"payment_modes": payment_modes(st.company if st else None),
		"machines": machines,
	}


def payment_modes(company):
	"""Modes of payment usable at the outlet: enabled, not cash, with an account for the company."""
	if not company:
		return []
	return frappe.db.sql_list(
		"""select m.name from `tabMode of Payment` m
		join `tabMode of Payment Account` a on a.parent = m.name and a.company = %s and ifnull(a.default_account, '') != ''
		where m.enabled = 1 and m.type != 'Cash' order by m.name""",
		company,
	)


@frappe.whitelist()
def counts():
	return {
		"pending_shifts": frappe.db.count(
			"Shift Sale Entry", {"workflow_state": "Pending Approval", "docstatus": 0}
		),
		"pending_tankers": frappe.db.count(
			"Tanker Receipt", {"workflow_state": "Pending Verification", "docstatus": 0}
		),
		"unread": frappe.db.count("Notification Log", {"for_user": frappe.session.user, "read": 0}),
	}


# ------------------------------------------------------------------ dashboard
@frappe.whitelist()
def dashboard(station=None, date=None):
	station = _station(station)
	date = date or today()
	f = {"station": station}
	kpis = {
		"fuel_today": dash._sse_sum("total_sale_qty", f, date),
		"fuel_yesterday": dash._sse_sum("total_sale_qty", f, add_days(date, -1)),
		"gross_today": dash._sse_sum("gross_sales", f, date),
		"gross_yesterday": dash._sse_sum("gross_sales", f, add_days(date, -1)),
		"credit_today": dash._sse_sum("credit_sales_amount", f, date),
		"digital_today": dash._sse_sum("digital_amount", f, date),
		"short_excess_today": dash._sse_sum("short_excess", f, date),
		"gross_month": dash._sse_sum("gross_sales", f, getdate(date).replace(day=1), date),
		"fuel_month": dash._sse_sum("total_sale_qty", f, getdate(date).replace(day=1), date),
		"stock_total": dash.fuel_stock_litres(f)["value"],
		"credit_outstanding": dash.credit_outstanding(f)["value"],
		"variance_month": dash.month_stock_variance(f)["value"],
	}
	return {
		"kpis": kpis,
		"tanks": tanks(station),
		"charts": {
			"daily_fuel": dash.daily_fuel_sales(filters=f),
			"collection_mix": dash.collection_mix(filters=f),
			"variance": dash.daily_stock_variance(filters=f),
		},
		"shifts": shift_timeline(station, date),
		"machines": frappe.db.sql(
			"""select m.dispensing_unit, m.side, sum(m.sale_qty) sale_qty, sum(m.sale_amount) sale_amount,
				group_concat(distinct nullif(m.attendants, '') separator ', ') attendants
			from `tabShift Machine Summary` m join `tabShift Sale Entry` s on s.name = m.parent
			where s.docstatus < 2 and s.station = %s and s.posting_date = %s
			group by m.dispensing_unit, m.side order by m.dispensing_unit, m.side""",
			(station, date),
			as_dict=True,
		),
		"attendants": frappe.db.sql(
			"""select a.attendant, a.attendant_name, group_concat(distinct s.shift) shifts,
				sum(a.sale_qty) sale_qty, sum(a.sale_amount) sale_amount, sum(a.credit_amount) credit_amount,
				sum(a.digital_amount) digital_amount, sum(a.expected_cash) expected_cash, sum(a.cash_handed) cash_handed,
				sum(a.short_excess) short_excess
			from `tabShift Attendant Collection` a join `tabShift Sale Entry` s on s.name = a.parent
			where s.docstatus < 2 and s.station = %s and s.posting_date = %s
			group by a.attendant, a.attendant_name order by a.attendant_name""",
			(station, date),
			as_dict=True,
		),
		"top_credit": [c for c in credit_customers()][:5],
		"attention": attention(station),
		"prices": [
			{"item": i.name, "rate": get_fuel_rate(i.name, date)}
			for i in frappe.get_all(
				"Item", {"petro_product_type": "Fuel", "disabled": 0}, ["name"], order_by="name"
			)
		],
	}


@frappe.whitelist()
def tanks(station=None):
	station = _station(station)
	out = []
	for t in frappe.get_all(
		"Fuel Tank Master",
		{"station": station, "status": ["!=", "Inactive"]},
		[
			"name",
			"fuel_item",
			"capacity_liters",
			"safe_fill_percent",
			"dead_stock_liters",
			"last_dip_mm",
			"last_dip_stock",
			"last_dip_on",
			"status",
		],
		order_by="name",
	):
		book = flt(get_tank_book_stock(t.name), 2)
		sold = flt(
			frappe.db.sql(
				"""select coalesce(sum(n.sale_qty), 0) from `tabShift Nozzle Reading` n
			join `tabShift Sale Entry` s on s.name = n.parent
			where s.docstatus = 1 and n.tank = %s and s.posting_date > %s""",
				(t.name, add_days(today(), -7)),
			)[0][0]
		)
		avg = sold / 7
		cover = flt((book - flt(t.dead_stock_liters)) / avg, 1) if avg else None
		out.append(
			{
				**t,
				"book_stock": book,
				"fill": flt(book * 100 / t.capacity_liters, 1) if t.capacity_liters else 0,
				"ullage": flt(t.capacity_liters * flt(t.safe_fill_percent or 100) / 100 - book, 0),
				"avg_daily_sale": flt(avg, 0),
				"days_cover": cover,
				"reorder": cover is not None and cover < 2,
			}
		)
	return out


def shift_timeline(station, date):
	entries = frappe.get_all(
		"Shift Sale Entry",
		{"station": station, "posting_date": date, "docstatus": ["<", 2]},
		[
			"name",
			"shift",
			"cashier_name",
			"total_sale_qty",
			"gross_sales",
			"short_excess",
			"workflow_state",
			"docstatus",
		],
	)
	by_shift = {}
	for e in entries:
		by_shift.setdefault(e.shift, []).append(e)
	out = []
	for s in frappe.get_all(
		"Shift Master", {"is_active": 1}, ["name", "start_time", "end_time"], order_by="sequence"
	):
		out.append(
			{
				"shift": s.name,
				"start_time": _hhmm(s.start_time),
				"end_time": _hhmm(s.end_time),
				"entries": by_shift.get(s.name, []),
			}
		)
	return out


def _hhmm(t):
	h, m, *_ = (str(t) + ":00").split(":")
	return f"{int(h):02d}:{int(m):02d}"


def attention(station):
	from petrodiesel.tasks import get_expiring_items

	items = []
	for d in frappe.get_all(
		"Shift Sale Entry",
		{"workflow_state": "Pending Approval", "docstatus": 0},
		["name", "shift", "posting_date", "cashier_name", "short_excess"],
		limit=10,
	):
		items.append(
			{
				"type": "shift",
				"severity": "warning",
				"doctype": "Shift Sale Entry",
				"name": d.name,
				"title": _("Shift {0} ({1}) awaiting approval").format(
					d.shift, frappe.format(d.posting_date, "Date")
				),
				"detail": _("{0}: cash {1}").format(d.cashier_name or "", _fmt_signed(d.short_excess)),
			}
		)
	for d in frappe.get_all(
		"Tanker Receipt",
		{"workflow_state": "Pending Verification", "docstatus": 0},
		["name", "truck_no", "total_invoice_qty", "total_shortage_qty"],
		limit=10,
	):
		items.append(
			{
				"type": "tanker",
				"severity": "warning",
				"doctype": "Tanker Receipt",
				"name": d.name,
				"title": _("Tanker {0} awaiting verification").format(d.truck_no),
				"detail": _("{0} L invoiced, short {1} L").format(
					flt(d.total_invoice_qty, 0), flt(d.total_shortage_qty, 2)
				),
			}
		)
	yesterday = add_days(today(), -1)
	if frappe.db.exists(
		"Shift Sale Entry", {"station": station, "posting_date": yesterday, "docstatus": 1}
	) and not frappe.db.exists(
		"Daily Stock Register", {"station": station, "posting_date": yesterday, "docstatus": 1}
	):
		items.append(
			{
				"type": "dsr",
				"severity": "danger",
				"doctype": "Daily Stock Register",
				"name": None,
				"title": _("DSR for {0} not submitted").format(frappe.format(yesterday, "Date")),
				"detail": "",
			}
		)
	for n in frappe.get_all(
		"Fuel Nozzle Master", {"station": station, "status": "Under Maintenance"}, ["name"]
	):
		items.append(
			{
				"type": "nozzle",
				"severity": "danger",
				"doctype": "Fuel Nozzle Master",
				"name": n.name,
				"title": _("Nozzle {0} under maintenance").format(n.name),
				"detail": _("Sales stopped on this nozzle"),
			}
		)
	for e in get_expiring_items(30):
		left = (getdate(e["valid_till"]) - getdate(today())).days
		items.append(
			{
				"type": "compliance",
				"severity": "danger" if left < 0 else "warning",
				"doctype": e["doctype"],
				"name": e["name"],
				"title": f"{e['what']}",
				"detail": _("Expired")
				if left < 0
				else _("{0} days left ({1})").format(left, frappe.format(e["valid_till"], "Date")),
			}
		)
	for t in tanks(station):
		if t["reorder"]:
			items.append(
				{
					"type": "stock",
					"severity": "danger",
					"doctype": "Fuel Tank Master",
					"name": t["name"],
					"title": _("Low stock in {0}").format(t["name"]),
					"detail": _("{0} L, about {1} days cover").format(
						flt(t["book_stock"], 0), t["days_cover"]
					),
				}
			)
	for c in credit_customers():
		if c["limit"] and c["used_pct"] >= 90:
			items.append(
				{
					"type": "credit",
					"severity": "danger" if c["used_pct"] >= 100 else "warning",
					"doctype": "Customer",
					"name": c["name"],
					"title": _("{0} at {1}% of credit limit").format(c["name"], flt(c["used_pct"], 0)),
					"detail": "",
				}
			)
	return items


def _fmt_signed(v):
	v = flt(v)
	return ("+" if v > 0 else "-" if v < 0 else "") + frappe.format(abs(v), "Currency")


# ------------------------------------------------------------------ previews (exact server maths)
@frappe.whitelist()
def preview(doc: str | dict):
	"""Run validate on an unsaved document and return computed values. Nothing is saved."""
	doc = frappe.parse_json(doc)
	if doc.get("doctype") not in PREVIEW_DOCTYPES:
		frappe.throw(_("Preview not allowed for {0}").format(doc.get("doctype")))
	frappe.has_permission(doc["doctype"], "read", throw=True)
	d = frappe.get_doc(doc)
	try:
		d.run_method("validate")
		error = None
	except frappe.ValidationError as e:
		error = frappe.utils.strip_html(str(e)) or _("Validation failed")
		frappe.clear_messages()
		if hasattr(d, "compute"):
			try:
				d.compute()
			except Exception:
				frappe.clear_messages()
	finally:
		frappe.db.rollback()
	return {"doc": d.as_dict(convert_dates_to_str=True), "error": error}


@frappe.whitelist()
def fetch_dsr(station: str, posting_date: str):
	frappe.has_permission("Daily Stock Register", "create", throw=True)
	d = frappe.new_doc("Daily Stock Register")
	d.update({"station": station, "posting_date": posting_date})
	d.company = frappe.db.get_value("Fuel Station", station, "company")
	d.set_data()
	d.calculate()
	return d.as_dict(convert_dates_to_str=True)


@frappe.whitelist()
def get_doc_full(doctype: str, name: str):
	"""Document plus workflow transitions and linked accounting documents."""
	from frappe.model.workflow import get_transitions

	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	try:
		transitions = [t.action for t in get_transitions(doc)] if doc.docstatus < 2 else []
	except Exception:
		transitions = []
	linked = []
	if doctype == "Shift Sale Entry":
		for si in frappe.get_all(
			"Sales Invoice",
			{"shift_sale_entry": name, "docstatus": ["<", 2]},
			["name", "customer", "grand_total", "outstanding_amount", "docstatus"],
		):
			linked.append({"doctype": "Sales Invoice", **si})
		if doc.settlement_journal:
			linked.append(
				{
					"doctype": "Journal Entry",
					"name": doc.settlement_journal,
					"grand_total": frappe.db.get_value(
						"Journal Entry", doc.settlement_journal, "total_debit"
					),
				}
			)
	elif doctype == "Tanker Receipt":
		if doc.purchase_invoice:
			linked.append(
				{
					"doctype": "Purchase Invoice",
					"name": doc.purchase_invoice,
					"grand_total": frappe.db.get_value(
						"Purchase Invoice", doc.purchase_invoice, "grand_total"
					),
				}
			)
		for se in frappe.get_all("Stock Entry", {"tanker_receipt": name}, ["name", "purpose", "docstatus"]):
			linked.append({"doctype": "Stock Entry", **se})
	elif doctype == "Daily Stock Register" and doc.stock_reconciliation:
		linked.append({"doctype": "Stock Reconciliation", "name": doc.stock_reconciliation})
	timeline = frappe.get_all(
		"Version",
		{"ref_doctype": doctype, "docname": name},
		["owner", "creation", "data"],
		order_by="creation asc",
		limit=30,
	)
	events = []
	for v in timeline:
		data = frappe.parse_json(v.data or "{}")
		for ch in data.get("changed", []):
			if ch[0] in ("workflow_state", "docstatus"):
				events.append(
					{
						"by": frappe.utils.get_fullname(v.owner),
						"at": str(v.creation),
						"field": ch[0],
						"to": ch[2],
					}
				)
	return {
		"doc": doc.as_dict(convert_dates_to_str=True),
		"transitions": transitions,
		"linked": linked,
		"events": events,
		"can_write": doc.has_permission("write"),
		"can_submit": doc.has_permission("submit"),
		"can_cancel": doc.has_permission("cancel"),
	}


@frappe.whitelist()
def save_doc(doc: str | dict, action: str | None = None):
	"""Insert or update a document, then optionally apply a workflow action or submit."""
	from frappe.model.workflow import apply_workflow

	doc = frappe.parse_json(doc)
	if doc.get("doctype") not in PREVIEW_DOCTYPES:
		frappe.throw(_("Not allowed"))
	if (
		doc.get("name")
		and not str(doc["name"]).startswith("new-")
		and frappe.db.exists(doc["doctype"], doc["name"])
	):
		d = frappe.get_doc(doc["doctype"], doc["name"])
		for key in ("modified",):
			doc.pop(key, None)
		d.update({k: v for k, v in doc.items() if k not in ("name", "owner", "creation", "docstatus")})
		d.save()
	else:
		doc.pop("name", None)
		d = frappe.get_doc(doc)
		d.insert()
	if action:
		if action == "submit":
			d.submit()
		else:
			d = apply_workflow(d, action)
	return d.name


@frappe.whitelist()
def doc_action(doctype: str, name: str, action: str, reason: str | None = None):
	"""Workflow action, submit or cancel an existing document."""
	from frappe.model.workflow import apply_workflow

	if doctype not in PREVIEW_DOCTYPES:
		frappe.throw(_("Not allowed"))
	d = frappe.get_doc(doctype, name)
	if reason:
		d.add_comment("Comment", _("{0}: {1}").format(action, reason))
	if action == "submit":
		d.submit()
	elif action == "cancel_doc":
		d.cancel()
	elif action == "delete":
		frappe.delete_doc(doctype, name)
		return None
	else:
		apply_workflow(d, action)
	return name


# ------------------------------------------------------------------ lists
@frappe.whitelist()
def list_docs(
	doctype: str,
	filters: str | dict | None = None,
	fields: str | list | None = None,
	limit: int = 50,
	start: int = 0,
	order_by: str | None = None,
	search: str | None = None,
	search_fields: str | list | None = None,
):
	if doctype not in PREVIEW_DOCTYPES:
		frappe.throw(_("Not allowed"))
	meta = frappe.get_meta(doctype)
	filters = frappe.parse_json(filters) if filters else {}
	fields = frappe.parse_json(fields) if fields else ["name"]
	if order_by:
		col, _sep, direction = order_by.partition(" ")
		if col != "name" and not meta.has_field(col) and col not in ("creation", "modified"):
			order_by = None
		else:
			order_by = f"{col} {'asc' if direction.strip().lower() == 'asc' else 'desc'}"
	sort = order_by or (
		"posting_date desc, creation desc" if meta.has_field("posting_date") else "creation desc"
	)
	or_filters = None
	if search:
		sf = frappe.parse_json(search_fields) if search_fields else ["name"]
		or_filters = [[f, "like", f"%{search}%"] for f in sf if f == "name" or meta.has_field(f)]
	rows = frappe.get_list(
		doctype,
		filters=filters,
		or_filters=or_filters,
		fields=fields,
		limit_start=cint(start),
		limit_page_length=cint(limit),
		order_by=sort,
	)
	total = len(
		frappe.get_list(doctype, filters=filters, or_filters=or_filters, pluck="name", limit_page_length=0)
	)
	return {"rows": rows, "total": total}


@frappe.whitelist()
def advances_overview():
	from petrodiesel.petrodiesel.advances import get_balances

	return {
		"balances": get_balances(),
		"recent": frappe.get_list(
			"Staff Advance",
			fields=["name", "employee_name", "posting_date", "amount", "docstatus", "recovery_method"],
			order_by="posting_date desc",
			limit_page_length=20,
		),
		"recoveries": frappe.get_list(
			"Staff Advance Recovery",
			fields=["name", "employee_name", "posting_date", "amount", "method", "docstatus"],
			order_by="posting_date desc",
			limit_page_length=20,
		),
	}


# ------------------------------------------------------------------ credit customers
@frappe.whitelist()
def credit_customers(search: str | None = None):
	frappe.has_permission("Customer", "read", throw=True)
	company = frappe.db.get_value("Fuel Station", _station(), "company")
	walk_in = frappe.db.get_value("Fuel Station", _station(), "walk_in_customer")
	vehicle_counts = dict(
		frappe.db.sql("select customer, count(*) from `tabCustomer Vehicle` group by customer")
	)
	customers = set(vehicle_counts) | set(
		frappe.get_all("Customer Credit Limit", {"company": company}, pluck="parent")
	)
	customers.discard(walk_in)
	out = []
	for c in sorted(customers):
		if search and search.lower() not in c.lower():
			continue
		bal = flt(
			frappe.db.sql(
				"""select coalesce(sum(debit - credit), 0) from `tabGL Entry`
			where is_cancelled = 0 and party_type = 'Customer' and party = %s and company = %s""",
				(c, company),
			)[0][0]
		)
		limit = flt(
			frappe.db.get_value("Customer Credit Limit", {"parent": c, "company": company}, "credit_limit")
		)
		last_pay = frappe.db.get_value(
			"Payment Entry", {"party": c, "docstatus": 1}, "posting_date", order_by="posting_date desc"
		)
		oldest = frappe.db.get_value(
			"Sales Invoice",
			{"customer": c, "docstatus": 1, "outstanding_amount": [">", 0]},
			"posting_date",
			order_by="posting_date asc",
		)
		out.append(
			{
				"name": c,
				"vehicles": vehicle_counts.get(c, 0),
				"outstanding": bal,
				"limit": limit,
				"available": limit - bal if limit else None,
				"used_pct": flt(bal * 100 / limit, 1) if limit else 0,
				"last_payment": last_pay,
				"overdue_days": (getdate(today()) - getdate(oldest)).days if oldest else 0,
			}
		)
	out.sort(key=lambda r: -r["outstanding"])
	return out


@frappe.whitelist()
def customer_detail(
	customer: str, from_date: str | None = None, to_date: str | None = None, vehicle: str | None = None
):
	frappe.has_permission("Customer", "read", throw=True)
	from petrodiesel.petrodiesel.report.credit_customer_statement.credit_customer_statement import execute

	company = frappe.db.get_value("Fuel Station", _station(), "company")
	summary = next((c for c in credit_customers() if c["name"] == customer), None)
	_cols, statement = execute(
		{
			"company": company,
			"customer": customer,
			"from_date": from_date or add_days(today(), -30),
			"to_date": to_date or today(),
			"vehicle": vehicle,
		}
	)
	return {
		"summary": summary,
		"vehicles": frappe.get_all(
			"Customer Vehicle",
			{"customer": customer},
			[
				"name",
				"vehicle_type",
				"fuel_item",
				"driver_name",
				"driver_mobile",
				"monthly_limit_liters",
				"is_active",
			],
		),
		"statement": statement,
		"invoices": frappe.get_all(
			"Sales Invoice",
			{"customer": customer, "docstatus": 1},
			["name", "posting_date", "grand_total", "outstanding_amount", "shift_sale_entry"],
			order_by="posting_date desc",
			limit=50,
		),
		"payments": frappe.get_all(
			"Payment Entry",
			{"party": customer, "docstatus": 1},
			["name", "posting_date", "paid_amount", "mode_of_payment", "reference_no"],
			order_by="posting_date desc",
			limit=50,
		),
	}


@frappe.whitelist()
def receive_payment(
	customer: str,
	amount: float,
	mode_of_payment: str,
	reference_no: str | None = None,
	reference_date: str | None = None,
	posting_date: str | None = None,
):
	"""Payment Entry from a credit customer, allocated to the oldest invoices first."""
	frappe.has_permission("Payment Entry", "create", throw=True)
	from erpnext.accounts.party import get_party_account

	from petrodiesel.petrodiesel.utils import get_mode_of_payment_account

	amount = flt(amount)
	if amount <= 0:
		frappe.throw(_("Amount must be positive"))
	company = frappe.db.get_value("Fuel Station", _station(), "company")
	paid_to = get_mode_of_payment_account(mode_of_payment, company)
	pe = frappe.new_doc("Payment Entry")
	pe.update(
		{
			"payment_type": "Receive",
			"company": company,
			"posting_date": posting_date or today(),
			"party_type": "Customer",
			"party": customer,
			"mode_of_payment": mode_of_payment,
			"paid_from": get_party_account("Customer", customer, company),
			"paid_to": paid_to,
			"paid_amount": amount,
			"received_amount": amount,
			"reference_no": reference_no or mode_of_payment,
			"reference_date": reference_date or today(),
		}
	)
	left = amount
	for inv in frappe.get_all(
		"Sales Invoice",
		{"customer": customer, "company": company, "docstatus": 1, "outstanding_amount": [">", 0]},
		["name", "outstanding_amount", "grand_total"],
		order_by="posting_date asc",
	):
		if left <= 0:
			break
		alloc = min(left, flt(inv.outstanding_amount))
		pe.append(
			"references",
			{
				"reference_doctype": "Sales Invoice",
				"reference_name": inv.name,
				"total_amount": inv.grand_total,
				"outstanding_amount": inv.outstanding_amount,
				"allocated_amount": alloc,
			},
		)
		left -= alloc
	pe.setup_party_account_field()
	pe.set_missing_values()
	pe.insert()
	pe.submit()
	return {"name": pe.name, "unallocated": flt(left, 2)}


@frappe.whitelist()
def save_vehicle(vehicle: str | dict):
	v = frappe.parse_json(vehicle)
	if v.get("name") and frappe.db.exists("Customer Vehicle", v["name"]):
		d = frappe.get_doc("Customer Vehicle", v["name"])
		d.update(
			{
				k: v[k]
				for k in (
					"vehicle_type",
					"fuel_item",
					"driver_name",
					"driver_mobile",
					"monthly_limit_liters",
					"is_active",
				)
				if k in v
			}
		)
		d.save()
	else:
		d = frappe.get_doc(
			{
				"doctype": "Customer Vehicle",
				**{
					k: v.get(k)
					for k in (
						"vehicle_no",
						"customer",
						"vehicle_type",
						"fuel_item",
						"driver_name",
						"driver_mobile",
						"monthly_limit_liters",
					)
				},
			}
		)
		d.insert()
	return d.name


# ------------------------------------------------------------------ search, notifications
@frappe.whitelist()
def search(q: str):
	q = (q or "").strip()
	if len(q) < 2:
		return []
	like = f"%{q}%"
	out = []
	for v in frappe.get_list(
		"Customer Vehicle", {"name": ["like", like.upper().replace(" ", "")]}, ["name", "customer"], limit=5
	):
		out.append(
			{
				"type": "Vehicle",
				"doctype": "Customer Vehicle",
				"name": v.name,
				"label": v.name,
				"description": v.customer,
			}
		)
	for c in frappe.get_list("Customer", {"customer_name": ["like", like]}, ["name"], limit=5):
		out.append(
			{"type": "Customer", "doctype": "Customer", "name": c.name, "label": c.name, "description": ""}
		)
	for dt in ("Shift Sale Entry", "Tanker Receipt", "Daily Stock Register"):
		if frappe.has_permission(dt, "read"):
			for d in frappe.get_list(dt, {"name": ["like", like]}, ["name"], limit=3):
				out.append({"type": dt, "doctype": dt, "name": d.name, "label": d.name, "description": dt})
	return out


@frappe.whitelist()
def notifications():
	logs = frappe.get_all(
		"Notification Log",
		{"for_user": frappe.session.user},
		["name", "subject", "document_type", "document_name", "read", "creation", "type"],
		order_by="creation desc",
		limit=50,
	)
	for l in logs:
		l.subject = frappe.utils.strip_html(l.subject or "")
	return {"logs": logs, "alerts": attention(_station())}


@frappe.whitelist()
def mark_notifications_read():
	frappe.db.set_value("Notification Log", {"for_user": frappe.session.user, "read": 0}, "read", 1)
	return True


# ------------------------------------------------------------------ setup
@frappe.whitelist()
def setup_data(station=None):
	station = _station(station)
	st = frappe.get_doc("Fuel Station", station)
	st.check_permission("read")
	dus = frappe.get_all(
		"Dispensing Unit",
		{"station": station},
		["name", "make", "model", "serial_no", "status", "wm_certificate_no", "wm_valid_till"],
		order_by="name",
	)
	for du in dus:
		du["nozzles"] = frappe.get_all(
			"Fuel Nozzle Master",
			{"dispensing_unit": du.name},
			["name", "side", "tank", "fuel_item", "last_reading", "last_reading_on", "status"],
			order_by="name",
		)
	tks = frappe.get_all(
		"Fuel Tank Master",
		{"station": station},
		[
			"name",
			"fuel_item",
			"warehouse",
			"capacity_liters",
			"dead_stock_liters",
			"safe_fill_percent",
			"diameter_mm",
			"length_mm",
			"next_calibration_due",
			"status",
		],
		order_by="name",
	)
	for t in tks:
		t["chart"] = frappe.get_all(
			"Tank Calibration Chart", {"parent": t.name}, ["dip_mm", "volume_liters"], order_by="dip_mm"
		)
	settings = get_settings().as_dict()
	return {
		"station": st.as_dict(convert_dates_to_str=True),
		"dispensing_units": dus,
		"tanks": tks,
		"shifts": frappe.get_all(
			"Shift Master",
			fields=["name", "sequence", "start_time", "end_time", "is_active"],
			order_by="sequence",
		),
		"settings": {
			k: settings.get(k)
			for k in (
				"default_station",
				"fuel_price_list",
				"fuel_tax_template",
				"lube_tax_template",
				"density_tolerance",
				"pump_test_tolerance_ml",
				"default_permissible_loss",
				"cash_variance_tolerance",
				"require_shift_approval",
				"post_dsr_stock_adjustment",
				"expiry_alert_days",
			)
		},
		"users": users()
		if "Pump Owner" in frappe.get_roles() or "System Manager" in frappe.get_roles()
		else [],
		"can_edit_settings": frappe.has_permission("Petrodiesel Settings", "write"),
	}


def users():
	out = []
	for u in frappe.get_all(
		"User",
		{"user_type": "System User", "enabled": 1, "name": ["not in", ["Administrator"]]},
		["name", "full_name", "last_active"],
	):
		roles = [r for r in frappe.get_roles(u.name) if r in PUMP_ROLES]
		if roles:
			out.append(
				{
					**u,
					"roles": roles,
					"employee": frappe.db.get_value("Employee", {"user_id": u.name}, "employee_name"),
				}
			)
	return out


@frappe.whitelist()
def save_settings(values: str | dict):
	frappe.has_permission("Petrodiesel Settings", "write", throw=True)
	values = frappe.parse_json(values)
	s = frappe.get_single("Petrodiesel Settings")
	allowed = (
		"density_tolerance",
		"pump_test_tolerance_ml",
		"default_permissible_loss",
		"cash_variance_tolerance",
		"require_shift_approval",
		"post_dsr_stock_adjustment",
		"expiry_alert_days",
	)
	s.update({k: values[k] for k in allowed if k in values})
	s.save()
	return True


@frappe.whitelist()
def set_nozzle_status(nozzle: str, status: str):
	if status not in ("Active", "Under Maintenance", "Inactive"):
		frappe.throw(_("Invalid status"))
	d = frappe.get_doc("Fuel Nozzle Master", nozzle)
	d.status = status
	d.save()
	return status


@frappe.whitelist()
def server_time():
	return str(now_datetime())
