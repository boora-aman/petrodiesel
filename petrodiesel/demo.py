# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt
"""Demo data for an Indian fuel retail outlet.

    bench --site <site> execute petrodiesel.demo.setup_demo
    bench --site <site> execute petrodiesel.demo.setup_demo --kwargs "{'days': 30}"

Creates (idempotently) a company, chart of accounts additions, VAT/GST
templates, fuel and lubricant items, tanks with calibration charts,
dispensing units, nozzles, shifts, credit customers with vehicles, staff,
demo users, and then simulates `days` business days of operations: price
updates, morning dips, pump tests, tanker decantation, three shift closings
per day, night dips, Daily Stock Registers, cash deposits and customer
payments.

Demo users (all password `Demo@12345`): owner@petro.demo, manager@petro.demo,
cashier@petro.demo, stock@petro.demo.
"""

from __future__ import annotations

import math
import random

import frappe
from frappe.utils import add_days, cint, flt, getdate, today

COMPANY = "Shree Balaji Fuels"
ABBR = "SBF"
STATION = "SBF Highway Outlet"
DEMO_PASSWORD = "Demo@12345"

FUELS = {
	# code: (name, sell, buy, vat %, permissible loss %, density@15)
	"MS": ("Petrol (MS)", 95.20, 91.10, 18.20, 0.60, 745.0),
	"HSD": ("Diesel (HSD)", 87.85, 85.20, 16.00, 0.25, 832.0),
	"XP95": ("Premium Petrol (XP95)", 102.40, 97.60, 18.20, 0.60, 748.0),
}
LUBES = {
	# code: (name, uom, sell, buy)
	"SERVO-4T-1L": ("SERVO 4T Xtra 20W-40 1 L", "Nos", 420, 330),
	"SERVO-PRIDE-5L": ("SERVO Pride TC 15W-40 5 L", "Nos", 1650, 1320),
	"COOLANT-1L": ("Engine Coolant 1 L", "Nos", 260, 190),
	"DEF-10L": ("Diesel Exhaust Fluid (DEF) 10 L", "Nos", 850, 640),
}
TANKS = [
	# tank, fuel, capacity L, diameter mm, length mm
	("T1-MS", "MS", 20000, 2400, 4420),
	("T2-HSD", "HSD", 20000, 2400, 4420),
	("T3-HSD", "HSD", 15000, 2200, 3950),
	("T4-XP95", "XP95", 10000, 2000, 3180),
]
NOZZLES = [
	# nozzle, DU, side, tank, opening totalizer
	("DU1-N1", "DU-1", "A", "T1-MS", 1254300.00),
	("DU1-N2", "DU-1", "A", "T2-HSD", 2873410.00),
	("DU1-N3", "DU-1", "B", "T1-MS", 1198765.00),
	("DU1-N4", "DU-1", "B", "T2-HSD", 2911020.00),
	("DU2-N1", "DU-2", "A", "T4-XP95", 214560.00),
	("DU2-N2", "DU-2", "A", "T3-HSD", 1765430.00),
	("DU2-N3", "DU-2", "B", "T4-XP95", 209870.00),
	("DU2-N4", "DU-2", "B", "T3-HSD", 1802215.00),
]
# litres per shift (low, high) by fuel
SHIFT_SALES = {"MS": (380, 720), "HSD": (650, 1300), "XP95": (40, 120)}
SHIFTS = [("Morning", 1, "06:00:00", "14:00:00"), ("Evening", 2, "14:00:00", "22:00:00"),
	("Night", 3, "22:00:00", "06:00:00")]
CREDIT_CUSTOMERS = {
	# customer: (credit limit, [vehicles])
	"Gupta Transport Co.": (400000, [("HR38AB4521", "Truck"), ("HR38AB7788", "Truck"), ("HR55K1290", "Truck")]),
	"Sharma Logistics": (300000, [("HR26CX9081", "Truck"), ("DL1LAB3344", "Truck")]),
	"Green Valley Public School": (250000, [("HR51BT2201", "Bus"), ("HR51BT2202", "Bus")]),
	"Shiv Shakti Constructions": (250000, [("HR29N5512", "Tractor"), ("HR29GEN01", "Generator / DG Set"),
		("HR29J7781", "Truck")]),
	"Kisan Agro Services": (200000, [("HR30T1199", "Tractor")]),
}
STAFF = [
	# first, last, gender, designation, user email, roles
	("Rajender", "Yadav", "Male", "Owner", "owner@petro.demo", ["Pump Owner", "Accounts Manager", "Stock Manager"]),
	("Suresh", "Malik", "Male", "Manager", "manager@petro.demo", ["Pump Manager", "Accounts User", "Stock User"]),
	("Rakesh", "Kumar", "Male", "Cashier", "cashier@petro.demo", ["Pump Cashier"]),
	("Pooja", "Sharma", "Female", "Cashier", None, None),
	("Amit", "Saini", "Male", "Stock Keeper", "stock@petro.demo", ["Pump Stock Keeper", "Stock User"]),
	("Vikas", "Kumar", "Male", "Attendant", None, None),
	("Sonu", "Jangra", "Male", "Attendant", None, None),
	("Deepak", "Rathi", "Male", "Attendant", None, None),
	("Neha", "Rani", "Female", "Attendant", None, None),
]


def setup_demo(days: int = 21, seed: int = 42):
	random.seed(seed)
	frappe.flags.in_demo = True
	frappe.set_user("Administrator")
	ensure_setup_complete()
	company = ensure_company()
	accounts = ensure_accounts(company)
	ensure_masters(company, accounts)
	frappe.db.commit()
	simulate(company, accounts, days)
	frappe.db.commit()
	print(f"Demo ready: company {COMPANY}, station {STATION}, {days} days simulated.")


# ---------------------------------------------------------------------- setup
def ensure_setup_complete():
	if cint(frappe.db.get_single_value("System Settings", "setup_complete")):
		return
	from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

	year = getdate(today()).year
	fy_start = f"{year if getdate(today()).month >= 4 else year - 1}-04-01"
	setup_complete({
		"language": "English",
		"country": "India",
		"timezone": "Asia/Kolkata",
		"currency": "INR",
		"full_name": "Petrol Pump Admin",
		"email": "admin@petro.demo",
		"password": "admin",
		"company_name": COMPANY,
		"company_abbr": ABBR,
		"chart_of_accounts": "Standard",
		"fy_start_date": fy_start,
		"fy_end_date": str(add_days(add_days(fy_start, 365), -1)),
		"setup_demo": 0,
		"industry": "Retail",
	})
	frappe.db.commit()


def ensure_fiscal_years(start_date):
	from erpnext.accounts.utils import get_fiscal_year

	d = getdate(start_date)
	while d <= getdate(today()):
		try:
			get_fiscal_year(d, company=COMPANY)
		except Exception:
			y = d.year if d.month >= 4 else d.year - 1
			fy = frappe.get_doc({"doctype": "Fiscal Year", "year": f"{y}-{str(y + 1)[2:]}",
				"year_start_date": f"{y}-04-01", "year_end_date": f"{y + 1}-03-31"})
			fy.insert(ignore_if_duplicate=True)
		d = add_days(d, 30)


def ensure_company():
	if not frappe.db.exists("Company", COMPANY):
		frappe.get_doc({"doctype": "Company", "company_name": COMPANY, "abbr": ABBR, "country": "India",
			"default_currency": "INR", "chart_of_accounts": "Standard"}).insert()
	frappe.defaults.set_global_default("company", COMPANY)
	return COMPANY


def _group(company, *names, root_type=None):
	for n in names:
		acc = frappe.db.get_value("Account", {"company": company, "account_name": n, "is_group": 1})
		if acc:
			return acc
	return frappe.db.get_value("Account", {"company": company, "root_type": root_type, "is_group": 1},
		order_by="lft asc")


def _account(company, name, parent, account_type=None):
	existing = frappe.db.get_value("Account", {"company": company, "account_name": name})
	if existing:
		if account_type and frappe.db.get_value("Account", existing, "account_type") != account_type:
			frappe.db.set_value("Account", existing, "account_type", account_type)
		return existing
	doc = frappe.get_doc({"doctype": "Account", "account_name": name, "company": company,
		"parent_account": parent, "account_type": account_type or ""})
	doc.insert(ignore_permissions=True)
	return doc.name


def ensure_accounts(company):
	cur_assets = _group(company, "Current Assets", root_type="Asset")
	bank_group = _group(company, "Bank Accounts", root_type="Asset")
	loans = _group(company, "Loans and Advances (Assets)", "Current Assets", root_type="Asset")
	taxes = _group(company, "Duties and Taxes", root_type="Liability")
	ind_exp = _group(company, "Indirect Expenses", root_type="Expense")
	acc = {
		"cash": frappe.get_cached_value("Company", company, "default_cash_account"),
		"bank": _account(company, "HDFC Bank Current A/c", bank_group, "Bank"),
		"card_clearing": _account(company, "Card Settlement Clearing", cur_assets, "Bank"),
		"fleet_clearing": _account(company, "IOCL Fleet Card Clearing", cur_assets, "Bank"),
		"short_excess": _account(company, "Cash Short and Excess", ind_exp),
		"staff_advance": _account(company, "Staff Advances", loans),
		"vat": _account(company, "VAT Payable on Fuel", taxes, "Tax"),
		"cgst": _account(company, "Output CGST", taxes, "Tax"),
		"sgst": _account(company, "Output SGST", taxes, "Tax"),
		"welfare": _account(company, "Staff Tea and Refreshment", ind_exp),
		"sundry": _account(company, "Outlet Sundry Expenses", ind_exp),
		"generator": _account(company, "Generator Diesel and Power", ind_exp),
	}
	if not acc["cash"]:
		acc["cash"] = _account(company, "Cash", _group(company, "Cash In Hand", root_type="Asset"), "Cash")
	return acc


def _get_or_insert(doc: dict, name_field=None, name=None):
	dt = doc["doctype"]
	key = name or (doc.get(name_field) if name_field else None)
	if key and frappe.db.exists(dt, key):
		return frappe.get_doc(dt, key)
	d = frappe.get_doc(doc)
	d.insert(ignore_permissions=True)
	return d


def ensure_masters(company, acc):
	cost_center = frappe.get_cached_value("Company", company, "cost_center")
	ensure_fiscal_years(add_days(today(), -400))

	for grp in ("Fuel", "Lubricants"):
		_get_or_insert({"doctype": "Item Group", "item_group_name": grp, "parent_item_group": "All Item Groups"},
			name=grp)
	for uom in ("Litre", "Nos"):
		_get_or_insert({"doctype": "UOM", "uom_name": uom}, name=uom)

	# taxes
	for code, (_n, _s, _b, vat, _l, _d) in FUELS.items():
		title = f"VAT {vat}%"
		if not frappe.db.exists("Item Tax Template", f"{title} - {ABBR}"):
			frappe.get_doc({"doctype": "Item Tax Template", "title": title, "company": company,
				"taxes": [{"tax_type": acc["vat"], "tax_rate": vat}]}).insert()
	fuel_tpl = f"Fuel VAT Inclusive - {ABBR}"
	if not frappe.db.exists("Sales Taxes and Charges Template", fuel_tpl):
		frappe.get_doc({"doctype": "Sales Taxes and Charges Template", "title": "Fuel VAT Inclusive",
			"company": company, "taxes": [{"charge_type": "On Net Total", "account_head": acc["vat"], "rate": 0,
			"included_in_print_rate": 1, "description": "State VAT on motor spirit / HSD"}]}).insert()
	lube_tpl = f"GST 18% Inclusive - {ABBR}"
	if not frappe.db.exists("Sales Taxes and Charges Template", lube_tpl):
		frappe.get_doc({"doctype": "Sales Taxes and Charges Template", "title": "GST 18% Inclusive",
			"company": company, "taxes": [
				{"charge_type": "On Net Total", "account_head": acc["cgst"], "rate": 9, "included_in_print_rate": 1,
					"description": "CGST 9%"},
				{"charge_type": "On Net Total", "account_head": acc["sgst"], "rate": 9, "included_in_print_rate": 1,
					"description": "SGST 9%"}]}).insert()

	# items
	for code, (name, _sell, buy, vat, loss, _dens) in FUELS.items():
		_get_or_insert({"doctype": "Item", "item_code": code, "item_name": name, "item_group": "Fuel",
			"stock_uom": "Litre", "is_stock_item": 1, "include_item_in_manufacturing": 0,
			"petro_product_type": "Fuel", "permissible_loss_percent": loss, "valuation_rate": buy,
			"taxes": [{"item_tax_template": f"VAT {vat}% - {ABBR}"}],
			"description": f"{name}. Outside GST; State VAT {vat}% included in price."}, name=code)
	for code, (name, uom, _sell, buy) in LUBES.items():
		_get_or_insert({"doctype": "Item", "item_code": code, "item_name": name, "item_group": "Lubricants",
			"stock_uom": uom, "is_stock_item": 1, "include_item_in_manufacturing": 0,
			"petro_product_type": "Lubricant", "valuation_rate": buy}, name=code)
		if not frappe.db.exists("Item Price", {"item_code": code, "price_list": "Standard Selling"}):
			frappe.get_doc({"doctype": "Item Price", "item_code": code, "price_list": "Standard Selling",
				"price_list_rate": LUBES[code][2]}).insert()

	# warehouses
	parent_wh = _get_or_insert({"doctype": "Warehouse", "warehouse_name": "Highway Outlet", "is_group": 1,
		"company": company}, name=f"Highway Outlet - {ABBR}").name
	wh = {}
	for tank, fuel, *_ in TANKS:
		wh[tank] = _get_or_insert({"doctype": "Warehouse", "warehouse_name": f"Tank {tank}",
			"parent_warehouse": parent_wh, "company": company}, name=f"Tank {tank} - {ABBR}").name
	lube_wh = _get_or_insert({"doctype": "Warehouse", "warehouse_name": "Lube Store", "parent_warehouse": parent_wh,
		"company": company}, name=f"Lube Store - {ABBR}").name

	# parties
	_get_or_insert({"doctype": "Customer", "customer_name": "Retail Customer (Walk-in)",
		"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}) or "All Customer Groups",
		"territory": frappe.db.get_value("Territory", {"is_group": 0}) or "All Territories"},
		name="Retail Customer (Walk-in)")
	for cust, (limit, vehicles) in CREDIT_CUSTOMERS.items():
		if not frappe.db.exists("Customer", cust):
			frappe.get_doc({"doctype": "Customer", "customer_name": cust, "customer_type": "Company",
				"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}) or "All Customer Groups",
				"territory": frappe.db.get_value("Territory", {"is_group": 0}) or "All Territories",
				"credit_limits": [{"company": company, "credit_limit": limit}],
				"payment_terms": None}).insert()
		else:
			frappe.db.set_value("Customer Credit Limit", {"parent": cust, "company": company}, "credit_limit", limit)
		for vno, vtype in vehicles:
			_get_or_insert({"doctype": "Customer Vehicle", "vehicle_no": vno, "customer": cust,
				"vehicle_type": vtype, "fuel_item": "HSD", "driver_name": random.choice(
					["Balwan Singh", "Mukesh", "Ramesh Chand", "Satbir", "Jagdish", "Naresh"])}, name=vno)
	_get_or_insert({"doctype": "Supplier", "supplier_name": "Indian Oil Corporation Ltd",
		"supplier_group": frappe.db.get_value("Supplier Group", {"is_group": 0}) or "All Supplier Groups"},
		name="Indian Oil Corporation Ltd")
	_get_or_insert({"doctype": "Supplier", "supplier_name": "Servo Lubricants Distributor",
		"supplier_group": frappe.db.get_value("Supplier Group", {"is_group": 0}) or "All Supplier Groups"},
		name="Servo Lubricants Distributor")

	# modes of payment
	for mop, account, mtype in (("Cash", acc["cash"], "Cash"), ("UPI", acc["bank"], "Bank"),
			("Credit / Debit Card", acc["card_clearing"], "Bank"), ("IOCL Fleet Card", acc["fleet_clearing"], "General")):
		m = frappe.get_doc("Mode of Payment", mop) if frappe.db.exists("Mode of Payment", mop) else frappe.get_doc(
			{"doctype": "Mode of Payment", "mode_of_payment": mop, "type": mtype})
		if not any(a.company == company for a in m.get("accounts", [])):
			m.append("accounts", {"company": company, "default_account": account})
		m.save(ignore_permissions=True) if not m.is_new() else m.insert(ignore_permissions=True)

	# staff & users
	employees = {}
	for first, last, gender, desig, email, roles in STAFF:
		emp = frappe.db.get_value("Employee", {"first_name": first, "last_name": last, "company": company})
		if not emp:
			if not frappe.db.exists("Designation", desig):
				frappe.get_doc({"doctype": "Designation", "designation_name": desig}).insert()
			e = frappe.get_doc({"doctype": "Employee", "first_name": first, "last_name": last, "gender": gender,
				"date_of_birth": "1990-01-01", "date_of_joining": "2022-04-01", "company": company,
				"designation": desig, "status": "Active"})
			e.insert()
			emp = e.name
		employees[desig] = employees.get(desig, []) + [emp]
		if email and not frappe.db.exists("User", email):
			u = frappe.get_doc({"doctype": "User", "email": email, "first_name": first, "last_name": last,
				"send_welcome_email": 0, "new_password": DEMO_PASSWORD, "user_type": "System User"})
			u.insert(ignore_permissions=True)
			u.add_roles(*roles)
			frappe.db.set_value("Employee", emp, "user_id", email)
	frappe.flags.demo_employees = employees

	# station
	if not frappe.db.exists("Fuel Station", STATION):
		frappe.get_doc({
			"doctype": "Fuel Station", "station_name": STATION, "company": company, "omc": "IOCL",
			"ro_code": "RO-245871", "dealer_name": "Shree Balaji Fuels", "address": "NH-44, Panipat, Haryana",
			"cost_center": cost_center, "walk_in_customer": "Retail Customer (Walk-in)", "lube_warehouse": lube_wh,
			"cash_account": acc["cash"], "cash_short_excess_account": acc["short_excess"],
			"employee_advance_account": acc["staff_advance"],
			"licences": [
				{"licence_type": "PESO Storage Licence", "licence_no": "P/HQ/HR/15/4521(P12345)",
					"issued_on": "2022-01-01", "valid_till": add_days(today(), 20)},
				{"licence_type": "Fire NOC", "licence_no": "FIRE/PNP/2024/889", "issued_on": "2024-06-01",
					"valid_till": add_days(today(), 210)},
				{"licence_type": "Weights & Measures", "licence_no": "LM/HR/PNP/1177", "issued_on": "2025-12-01",
					"valid_till": add_days(today(), 15)},
				{"licence_type": "Pollution Consent (CTO)", "licence_no": "HSPCB/CTO/9981", "issued_on": "2023-04-01",
					"valid_till": add_days(today(), 400)},
			],
		}).insert()

	for name, seq, start, end in SHIFTS:
		_get_or_insert({"doctype": "Shift Master", "shift_name": name, "sequence": seq, "start_time": start,
			"end_time": end}, name=name)

	for du, make in (("DU-1", "Tokheim"), ("DU-2", "Gilbarco")):
		_get_or_insert({"doctype": "Dispensing Unit", "du_code": du, "station": STATION, "make": make,
			"model": "Quantium 510" if make == "Gilbarco" else "Quantium Q300", "serial_no": f"SN{random.randint(10**6, 10**7)}",
			"installed_on": "2021-03-15", "wm_certificate_no": f"LM/{du}/2025", "wm_stamped_on": "2025-12-01",
			"wm_valid_till": add_days(today(), 15 if du == "DU-1" else 300)}, name=du)

	for tank, fuel, cap, dia, length in TANKS:
		if not frappe.db.exists("Fuel Tank Master", tank):
			frappe.get_doc({"doctype": "Fuel Tank Master", "tank_id": tank, "station": STATION, "fuel_item": fuel,
				"warehouse": wh[tank], "capacity_liters": cap, "dead_stock_liters": round(cap * 0.03),
				"safe_fill_percent": 95, "diameter_mm": dia, "length_mm": length,
				"last_calibrated_on": "2024-02-10", "next_calibration_due": add_days(today(), 450),
				"calibration_data": calibration_chart(dia, length, cap)}).insert()

	for nozzle, du, side, tank, opening in NOZZLES:
		_get_or_insert({"doctype": "Fuel Nozzle Master", "nozzle_id": nozzle, "dispensing_unit": du, "side": side,
			"tank": tank, "opening_totalizer": opening}, name=nozzle)

	s = frappe.get_single("Petrodiesel Settings")
	s.update({"default_station": STATION, "fuel_price_list": "Standard Selling", "fuel_item_group": "Fuel",
		"lube_item_group": "Lubricants", "fuel_tax_template": fuel_tpl, "lube_tax_template": lube_tpl})
	s.save(ignore_permissions=True)


def horizontal_volume(h, dia, length):
	r = dia / 2
	h = min(max(h, 0), dia)
	area = r * r * math.acos((r - h) / r) - (r - h) * math.sqrt(max(2 * r * h - h * h, 0))
	return area * length / 1e6  # mm^3 -> litres


def calibration_chart(dia, length, capacity):
	full = horizontal_volume(dia, dia, length)
	scale = capacity / full
	rows = []
	for h in list(range(0, dia, 50)) + [dia]:
		rows.append({"dip_mm": h, "volume_liters": round(horizontal_volume(h, dia, length) * scale, 2)})
	return rows


def volume_to_dip(tank, litres):
	rows = frappe.get_all("Tank Calibration Chart", {"parent": tank}, ["dip_mm", "volume_liters"], order_by="dip_mm")
	for a, b in zip(rows, rows[1:]):
		if a.volume_liters <= litres <= b.volume_liters:
			if b.volume_liters == a.volume_liters:
				return b.dip_mm
			return round(a.dip_mm + (b.dip_mm - a.dip_mm) * (litres - a.volume_liters) / (b.volume_liters - a.volume_liters), 1)
	return rows[-1].dip_mm if litres > 0 else 0


# ---------------------------------------------------------------------- simulation
def simulate(company, acc, days):
	"""Simulate `days` business days ending today. Resumable: completed days are skipped."""
	from petrodiesel.petrodiesel.utils import get_fuel_rate, get_tank_book_stock

	start = add_days(today(), -days)
	employees = frappe.flags.demo_employees
	attendants = employees.get("Attendant", [])
	cashiers = employees.get("Cashier", [])
	keeper = (employees.get("Stock Keeper") or [None])[0]

	opening_stock(company, start)

	for i in range(days + 1):
		date = add_days(start, i)
		last_day = i == days
		if frappe.db.exists("Daily Stock Register", {"station": STATION, "posting_date": date, "docstatus": 1}):
			continue

		if not frappe.db.exists("Fuel Price Update", {"effective_date": date, "docstatus": 1}):
			if i == 0 or not frappe.db.exists("Fuel Price Update", {"docstatus": 1}):
				price_update(date, {code: v[1] for code, v in FUELS.items()})
			elif i % 3 == 0:
				prices = {code: round(get_fuel_rate(code, add_days(date, -1)) + random.choice(
					[-0.12, -0.05, 0, 0.04, 0.09, 0.15]), 2) for code in FUELS}
				price_update(date, prices)

		if not _exists_dip(date, "Morning (Opening)"):
			dip_reading(date, "06:05:00", "Morning (Opening)", keeper, loss_factor=0)
		if not frappe.db.exists("Pump Test Log", {"station": STATION, "posting_date": date, "docstatus": 1}):
			pump_test(date, keeper)

		received = set(frappe.db.sql_list("""select i.tank from `tabTanker Receipt Item` i
			join `tabTanker Receipt` t on t.name = i.parent where t.docstatus = 1 and t.posting_date = %s""", date))
		for tank, fuel, cap, *_ in TANKS:
			if tank not in received and get_tank_book_stock(tank) < cap * 0.45:
				tanker_receipt(date, tank, fuel, cap, keeper)

		for shift_name, seq, _start_t, end_t in SHIFTS:
			if frappe.db.exists("Shift Sale Entry", {"station": STATION, "posting_date": date, "shift": shift_name,
					"docstatus": ["<", 2]}):
				continue
			pending = last_day and seq == len(SHIFTS)
			shift_entry(date, shift_name, end_t, attendants, cashiers, submit=not pending)

		if not last_day:
			if not _exists_dip(date, "Night (Closing)"):
				dip_reading(date, "23:55:00", "Night (Closing)", keeper, loss_factor=0.003)
			dsr = frappe.get_doc({"doctype": "Daily Stock Register", "station": STATION, "posting_date": date})
			dsr.insert()
			dsr.submit()
			cash_deposit(company, acc, date)
			if i and i % 3 == 0:
				customer_payments(company, acc, date)
		frappe.db.commit()
		print(f"  simulated {date}")


def _exists_dip(date, rtype):
	return frappe.db.exists("Tank Dip Reading", {"station": STATION, "posting_date": date, "reading_type": rtype,
		"docstatus": 1})


def _credit_headroom(customer, company):
	from erpnext.selling.doctype.customer.customer import get_credit_limit, get_customer_outstanding

	limit = flt(get_credit_limit(customer, company))
	if not limit:
		return float("inf")
	return limit - flt(get_customer_outstanding(customer, company, ignore_outstanding_sales_order=True))


def opening_stock(company, date):
	if frappe.db.exists("Stock Reconciliation", {"company": company, "purpose": "Opening Stock", "docstatus": 1}):
		return
	sr = frappe.get_doc({"doctype": "Stock Reconciliation", "company": company, "purpose": "Opening Stock",
		"posting_date": add_days(date, -1), "set_posting_time": 1, "posting_time": "23:00:00",
		"expense_account": frappe.db.get_value("Account", {"company": company, "account_name": "Temporary Opening"}),
		"items": []})
	for tank, fuel, cap, *_ in TANKS:
		sr.append("items", {"item_code": fuel, "warehouse": frappe.db.get_value("Fuel Tank Master", tank, "warehouse"),
			"qty": round(cap * random.uniform(0.6, 0.8)), "valuation_rate": FUELS[fuel][2]})
	lube_wh = f"Lube Store - {ABBR}"
	for code, (_n, _u, _s, buy) in LUBES.items():
		sr.append("items", {"item_code": code, "warehouse": lube_wh, "qty": 120, "valuation_rate": buy})
	sr.insert()
	sr.submit()


def price_update(date, prices):
	doc = frappe.get_doc({"doctype": "Fuel Price Update", "effective_date": date, "effective_time": "06:00:00",
		"price_list": "Standard Selling", "source": "OMC SMS",
		"items": [{"fuel_item": k, "new_price": v} for k, v in prices.items()]})
	doc.insert()
	doc.submit()


def dip_reading(date, time, rtype, keeper, loss_factor=0.0):
	from petrodiesel.petrodiesel.utils import get_tank_book_stock

	rows = []
	for tank, fuel, *_ in TANKS:
		book = get_tank_book_stock(tank, date, time)
		sold = flt(frappe.db.sql("""select coalesce(sum(n.sale_qty), 0) from `tabShift Nozzle Reading` n
			join `tabShift Sale Entry` s on s.name = n.parent
			where s.docstatus = 1 and s.posting_date = %s and n.tank = %s""", (date, tank))[0][0])
		# physical stock: book minus an evaporation / handling loss proportional to the day's sales
		physical = max(book - sold * loss_factor * random.uniform(0.2, 1.4), 0)
		rows.append({"tank": tank, "dip_mm": volume_to_dip(tank, physical), "water_dip_mm": 0,
			"temperature": round(random.uniform(24, 32), 1),
			"observed_density": FUELS[fuel][5] - 4, "density_at_15": round(FUELS[fuel][5] + random.uniform(-1.5, 1.5), 1)})
	doc = frappe.get_doc({"doctype": "Tank Dip Reading", "station": STATION, "posting_date": date,
		"posting_time": time, "reading_type": rtype, "recorded_by": keeper, "readings": rows})
	doc.insert()
	doc.submit()


def pump_test(date, keeper):
	doc = frappe.get_doc({"doctype": "Pump Test Log", "station": STATION, "posting_date": date,
		"posting_time": "06:15:00", "test_type": "Daily Check", "tested_by": keeper,
		"measure_certificate_no": "LM/5L/2025/112",
		"tests": [{"nozzle": n[0], "measure_liters": 5, "error_ml": random.choice([-10, -5, 0, 0, 5, 10]),
			"returned_to_tank": 1} for n in NOZZLES]})
	doc.insert()
	doc.submit()


def tanker_receipt(date, tank, fuel, cap, keeper):
	from petrodiesel.petrodiesel.utils import get_tank_book_stock

	before = get_tank_book_stock(tank, date, "07:00:00")
	qty = 12000 if cap >= 15000 else 4000
	qty = min(qty, int((cap * 0.95 - before) / 1000) * 1000)
	if qty < 2000:
		return
	short = round(random.uniform(0, 18), 1)
	after = before + qty - short
	dens = FUELS[fuel][5]
	doc = frappe.get_doc({
		"doctype": "Tanker Receipt", "station": STATION, "posting_date": date, "posting_time": "07:30:00",
		"supplier": "Indian Oil Corporation Ltd", "supplier_invoice_no": f"IOC/{getdate(date).strftime('%y%m%d')}/{random.randint(1000, 9999)}",
		"supplier_invoice_date": date, "truck_no": random.choice(["HR67A4412", "HR67B9021", "PB11CQ7781"]),
		"driver_name": "Gurmeet Singh", "received_by": keeper, "seals_intact": 1, "seal_numbers": f"S{random.randint(100000, 999999)}",
		"items": [{
			"tank": tank, "invoice_qty": qty, "rate": FUELS[fuel][2], "challan_density": dens,
			"observed_density": dens - 5, "observed_temperature": 30, "density_at_15": round(dens + random.uniform(-1.8, 1.8), 1),
			"dip_before_mm": volume_to_dip(tank, before), "dip_after_mm": volume_to_dip(tank, after),
		}],
	})
	doc.insert()
	doc.submit()


def shift_entry(date, shift_name, end_time, attendants, cashiers, submit=True):
	from petrodiesel.petrodiesel.doctype.shift_sale_entry.shift_sale_entry import get_nozzles

	cashier = random.choice(cashiers)
	doc = frappe.new_doc("Shift Sale Entry")
	doc.update({"station": STATION, "posting_date": date, "shift": shift_name, "cashier": cashier})
	for n in get_nozzles(STATION, date):
		fuel = n["fuel_item"]
		lo, hi = SHIFT_SALES[fuel]
		sale = round(random.uniform(lo, hi) / 2, 2)  # two nozzles per fuel per tank pair
		test = 5.0 if shift_name == "Morning" else 0.0
		doc.append("nozzle_readings", {**n, "closing_reading": round(n["opening_reading"] + sale + test, 2),
			"test_qty": test, "attendant": random.choice(attendants) if attendants else None})
	doc.run_method("validate")  # compute totals for realistic collections below

	# credit slips (diesel mostly)
	hsd_rate = next((r.rate for r in doc.nozzle_readings if r.fuel_item == "HSD"), 0)
	ms_rate = next((r.rate for r in doc.nozzle_readings if r.fuel_item == "MS"), 0)
	hsd_sold = sum(r.sale_qty for r in doc.nozzle_readings if r.fuel_item == "HSD")
	credit_left = hsd_sold * 0.45
	company = frappe.db.get_value("Fuel Station", STATION, "company")
	headroom = {c: _credit_headroom(c, company) * 0.9 for c in CREDIT_CUSTOMERS}
	for _ in range(random.randint(2, 6)):
		cust = random.choice(list(CREDIT_CUSTOMERS))
		vno, vtype = random.choice(CREDIT_CUSTOMERS[cust][1])
		qty = round(random.uniform(20, 80) if vtype in ("Tractor", "Generator / DG Set") else random.uniform(60, 180), 2)
		if qty > credit_left:
			break
		if qty * hsd_rate > headroom[cust]:
			continue
		headroom[cust] -= qty * hsd_rate
		credit_left -= qty
		doc.append("credit_sales", {"customer": cust, "vehicle": vno, "slip_no": str(random.randint(10000, 99999)),
			"fuel_item": "HSD", "qty": qty, "rate": hsd_rate, "odometer": random.randint(20000, 400000)})
	if random.random() < 0.3 and ms_rate and headroom["Green Valley Public School"] > 3000:
		doc.append("credit_sales", {"customer": "Green Valley Public School", "slip_no": str(random.randint(10000, 99999)),
			"fuel_item": "MS", "qty": round(random.uniform(10, 25), 2), "rate": ms_rate, "driver_name": "Office car"})

	for _ in range(random.randint(0, 4)):
		code = random.choice(list(LUBES))
		doc.append("other_sales", {"item_code": code, "qty": random.randint(1, 3), "rate": LUBES[code][2]})
	dcust = random.choice(list(CREDIT_CUSTOMERS)[:2]) if random.random() < 0.15 else None
	if dcust and headroom[dcust] > 2000:
		vno = CREDIT_CUSTOMERS[dcust][1][0][0]
		doc.append("driver_cash", {"customer": dcust, "vehicle": vno, "slip_no": str(random.randint(10000, 99999)),
			"amount": random.choice([500, 1000, 1500]), "driver_name": "Balwan Singh", "remarks": "Toll and food"})
	if random.random() < 0.4:
		acct = random.choice(["Staff Tea and Refreshment", "Outlet Sundry Expenses", "Generator Diesel and Power"])
		doc.append("expenses", {"expense_account": f"{acct} - {ABBR}", "description": acct,
			"amount": random.choice([120, 150, 200, 350, 800])})
	if random.random() < 0.1 and attendants:
		doc.append("employee_advances", {"employee": random.choice(attendants), "amount": random.choice([500, 1000]),
			"remarks": "Salary advance"})
	doc.run_method("validate")

	retail = doc.expected_cash + doc.digital_amount
	upi = round(retail * random.uniform(0.30, 0.42), 0)
	card = round(retail * random.uniform(0.06, 0.12), 0)
	fleet = round(retail * random.uniform(0.02, 0.06), 0)
	doc.append("payments", {"mode_of_payment": "UPI", "amount": upi, "reference_no": f"UPI-{random.randint(10**5, 10**6)}",
		"terminal_id": "Paytm QR-1"})
	doc.append("payments", {"mode_of_payment": "Credit / Debit Card", "amount": card,
		"reference_no": f"BATCH-{random.randint(100, 999)}", "terminal_id": "HDFC POS-1"})
	doc.append("payments", {"mode_of_payment": "IOCL Fleet Card", "amount": fleet,
		"reference_no": f"XTRA-{random.randint(100, 999)}", "terminal_id": "XTRAPOWER EDC"})
	doc.run_method("validate")

	variance = random.choice([0, 0, 0, -10, -20, -50, 10, 20, -120])
	count_cash(doc, max(doc.expected_cash + variance, 0))
	doc.run_method("validate")
	if abs(doc.short_excess) > 100:
		doc.remarks = "Shortage recovered from cashier at month end"
	doc.insert()
	if submit:
		doc.submit()
	else:
		from frappe.model.workflow import apply_workflow

		if frappe.db.get_value("Workflow", "Shift Sale Entry Approval", "is_active"):
			apply_workflow(doc, "Submit for Approval")


def count_cash(doc, amount):
	remaining = int(round(amount))
	counts = {}
	for d in (500, 200, 100, 50, 20, 10, 5, 2, 1):
		counts[d], remaining = divmod(remaining, d)
	doc.set("denominations", [])
	for d, c in counts.items():
		doc.append("denominations", {"denomination": d, "count": c})


def cash_deposit(company, acc, date):
	from erpnext.accounts.utils import get_balance_on

	bal = flt(get_balance_on(acc["cash"], date, company=company))
	amount = int(bal / 500) * 500 - 10000  # keep a float of about ₹10,000
	if amount <= 0:
		return
	je = frappe.get_doc({"doctype": "Journal Entry", "voucher_type": "Bank Entry", "company": company,
		"posting_date": date, "cheque_no": f"DEP-{getdate(date).strftime('%Y%m%d')}", "cheque_date": date,
		"user_remark": "Daily cash deposit to bank",
		"accounts": [{"account": acc["bank"], "debit_in_account_currency": amount},
			{"account": acc["cash"], "credit_in_account_currency": amount}]})
	je.insert()
	je.submit()


def customer_payments(company, acc, date):
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	for cust in CREDIT_CUSTOMERS:
		invoices = frappe.get_all("Sales Invoice", {"customer": cust, "docstatus": 1, "outstanding_amount": [">", 0],
			"posting_date": ["<=", add_days(date, -2)]}, ["name", "outstanding_amount"], order_by="posting_date asc")
		for inv in invoices:
			pe = get_payment_entry("Sales Invoice", inv.name, bank_account=acc["bank"])
			pe.posting_date = date
			pe.mode_of_payment = "UPI"
			pe.reference_no = f"NEFT{random.randint(10**6, 10**7)}"
			pe.reference_date = date
			pe.insert()
			pe.submit()
