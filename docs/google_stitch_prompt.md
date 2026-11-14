# Google Stitch prompts: PetroDesk frontend

How to use:
1. Paste **Prompt 0 (master brief)** first in a new Stitch project, choosing **Web** and asking for a **responsive** design.
2. Then paste each screen prompt (1–16) one at a time in the same project, so every screen reuses the same design system.
3. Export the result as HTML/Tailwind (or share the Stitch project link). The design will be rebuilt in Vue 3 + frappe-ui, so keep it to Tailwind-style components with no custom JS.

Field names in `code` are the real backend field names. Ask Stitch to use the labels, and keep the code names in this file for integration.

---

## Prompt 0: Master brief and design system

```
Design a responsive web app called "PetroDesk": a petrol pump (fuel retail outlet) management app for Indian dealers of IOCL, BPCL, HPCL, Nayara and Jio-bp. It is the front office for an ERPNext back office, so it must feel fast, calm and trustworthy, like a modern fintech dashboard, not a generic admin template.

USERS AND DEVICES
- Pump Owner (dealer): desktop and phone. Wants today's sales, cash, stock, credit dues and alerts at a glance. Approves things.
- Pump Manager: desktop and tablet. Approves shift closings and tanker receipts, checks stock and variance, manages masters.
- Pump Cashier / shift in-charge: tablet or phone at the forecourt sales room. Enters meter readings, credit slips, collections and cash count at shift end. Big touch targets, numeric keypads, works one-handed.
- Pump Stock Keeper: phone. Records tank dips, tanker decantation, pump tests.
The menu and home screen change by role.

DESIGN SYSTEM
- Font: Inter. Numbers use tabular figures. Indian number format everywhere (₹ 1,25,430.50; litres as 12,345.67 L). Dates as DD-MM-YYYY. Times in 24h.
- Colours: neutral grey surfaces (white cards on a #F7F7F8 background), near-black text #171717, one brand accent of deep teal #0F766E. Semantic colours: green for tallied / within limit / passed, amber for warning / pending approval, red for shortage / loss beyond limit / failed / expired, blue for informational / draft.
- Fuel colour chips used consistently: Petrol (MS) = green #16A34A, Diesel (HSD) = amber #D97706, Premium Petrol (XP95) = violet #7C3AED, Lubricants = slate.
- Components look like the frappe-ui component library (Tailwind): 8px radius, 1px #E5E7EB borders, subtle shadows only on popovers, compact 36px inputs on desktop and 44px on touch, pill status badges, a left sidebar on desktop, a bottom tab bar on mobile, a sticky top bar with outlet switcher, date and user avatar menu.
- Every money or litre figure that the system calculates is shown read-only in a slightly tinted box with a small "auto" label, so users know they do not type it.
- Light mode primary; also provide a dark-mode variant of the dashboard.
- Empty, loading (skeleton) and error states for lists and cards.
- Accessibility: 4.5:1 contrast, visible focus rings, labels on every input.

GLOBAL LAYOUT
- Desktop: collapsible left sidebar with sections: Home, Shift Closing, Tanker Receipts, Tank Dips, Daily Stock Register, Pump Tests, Price Updates, Credit Customers, Collections, Reports, Setup (Outlet, Tanks, Dispensing Units & Nozzles, Shifts, Vehicles, Settings), Approvals (with a count badge).
- Top bar: outlet name with RO code and OMC logo chip, a business-date picker, global search (vehicle no, customer, document no), a notification bell, and the user menu (profile, switch role view, logout).
- Mobile: bottom tabs Home / Shift / Stock / Credit / More, plus a floating "+" button for quick actions: New Shift Closing, Dip Reading, Tanker Receipt, Pump Test, Receive Payment.

Use realistic Indian demo data throughout:
- Outlet "SBF Highway Outlet, NH-44 Panipat, IOCL RO-245871".
- Staff: Rakesh Kumar (cashier), Suresh Malik (manager), Amit Saini (stock), attendants Vikas, Sonu, Deepak, Neha.
- Credit customers: Gupta Transport Co., Sharma Logistics, Green Valley Public School, Shiv Shakti Constructions, Kisan Agro Services.
- Vehicles like HR38AB4521.
- Prices: MS ₹95.37/L, HSD ₹87.86/L, XP95 ₹102.61/L.
```

---

## Prompt 1: Login

```
Login screen for PetroDesk. Split layout on desktop: on the left a calm teal illustration of a fuel forecourt with the tagline "Every litre, every rupee, reconciled."; on the right the form. Single column on mobile.
- Form: email or mobile number, password with show/hide, "Remember me", "Forgot password?" link, primary "Sign in" button, and a secondary "Sign in with email link" button.
- Error state: an inline red message "Invalid login. Check email and password."
- Locked/disabled user state.
- Footer: app version and "Powered by ERPNext".
After login the app opens the role's home screen.
```

## Prompt 2: Owner / Manager home dashboard

```
Home dashboard for Pump Owner and Manager (desktop first, responsive).

Header row:
- Greeting "Good morning, Rajender".
- Business-date selector and outlet selector.
- Live status pill "Morning shift running · 06:00–14:00".

KPI cards (2 rows of 5 on desktop, horizontal scroll on mobile), each with value, label, small comparison to yesterday and a sparkline:
- Fuel Sale Today (L): 4,805 L
- Gross Sales Today: ₹4,33,000
- Credit Sales Today: ₹1,09,000
- Digital Collection Today: ₹1,73,000
- Cash Short (−) / Excess (+) Today: −₹240 (red)
- Gross Sales This Month: ₹96,19,000
- Fuel Sale This Month (L): 1,05,469 L
- Fuel Stock in Tanks (L): 41,230 L
- Credit Outstanding: ₹5,90,000
- Stock Gain/Loss This Month: −253 L (red)

Tank gauges section: one card per tank (T1-MS 20,000 L, T2-HSD 20,000 L, T3-HSD 15,000 L, T4-XP95 10,000 L). Each card has:
- a horizontal cylinder fill graphic coloured by fuel;
- book stock, ullage (space left), fill %, days of cover;
- last dip time;
- a red "Order now" badge when cover is under 2 days.

Charts:
- Daily Fuel Sales (stacked bars by fuel, last 30 days).
- Collection Mix (donut: Cash, Credit, UPI, Card, Fleet Card).
- Daily Stock Gain/Loss (line per fuel with a shaded permissible band).

Right column / lower section:
- "Needs your attention": shift closings pending approval, tanker receipts pending verification, DSR not submitted yesterday, nozzles under maintenance, licences expiring (PESO licence expires in 20 days, W&M stamping DU-1 in 15 days), customers over 90% of credit limit.
- "Today's shifts" timeline: Morning / Evening / Night with status chips (Not started, Draft, Pending Approval, Approved), cashier name, litres, short/excess.
```

## Prompt 3: Shift closing list

```
Shift Closing list (doctype "Shift Sale Entry").
- Filters: date range, shift (Morning/Evening/Night), cashier, status (Draft, Pending Approval, Approved, Rejected, Cancelled), and "only short/excess".
- Desktop table columns: Entry No (SSE-2026-11-0066), Business Date, Shift, Cashier, Total Sale (L), Gross Sales ₹, Credit ₹, Digital ₹, Expected Cash ₹, Cash Counted ₹, Short/Excess ₹ (coloured), and a Status badge.
- Mobile: cards with the same key figures.
- Row actions: Open, Print Shift Report, Approve / Reject (manager only).
- Primary button "New Shift Closing". A summary bar at the top with totals for the filtered period.
```

## Prompt 4: Shift closing form (most important screen)

```
New / edit Shift Closing form. It is a multi-step wizard on tablet and phone, and a single page with a sticky step navigator on desktop.

At all times a sticky summary bar shows: Sale (L) · Gross ₹ · Expected Cash ₹ · Cash Counted ₹ · and a big status chip "Short ₹7,932.55" (red), "Excess ₹20" (amber) or "Cash Tallied" (green). Every number in this bar updates live as the user types.

HEADER
- Outlet (auto, `station`), Business Date (`posting_date`), Shift (`shift`, with start/end time filled from the shift), Cashier (`cashier`, auto-filled with the logged-in user).
- A status badge and an approval timeline (Draft → Pending Approval → Approved / Rejected) with who and when.

STEP 1: METER READINGS (`nozzle_readings`)
- A "Load active nozzles" button fills one row per nozzle, grouped by dispensing unit (DU-1, DU-2).
- Each nozzle is a row/card with:
  - nozzle id + fuel chip;
  - tank;
  - attendant (DSM) selector;
  - Opening reading (auto, from last closing, read-only with a lock icon);
  - Closing reading (large numeric input with a big numeric keypad on touch);
  - Test qty (returned to tank, default 0, quick button "+5 L");
  - auto fields Meter qty, Sale qty, Rate (auto, today's price), Amount.
- Validation shown inline: closing less than opening (red), test qty more than metered.
- An "Add price-change row" action for a nozzle: shows a second row with opening = first row's closing and a different rate (the price changed at 06:00).
- A fuel-wise summary table below: Fuel, Meter Qty, Test Qty, Sale Qty, Credit Qty, Retail Qty, Amount.

STEP 2: CREDIT & OTHER SALES
- Credit slips (`credit_sales`): customer (search), vehicle (search, filtered by customer; picking a vehicle auto-fills fuel and driver), indent/slip no, fuel, qty (L), rate (auto), amount (auto), odometer.
  - A small credit-limit meter under the customer: "₹1,18,840 of ₹4,00,000 used".
  - The row turns red with "Credit limit exceeded" when over.
- Lubricant & shop sales (`other_sales`): item search, qty, rate (auto), amount. GST 18% inclusive note.
- Cash paid to fleet drivers (`driver_cash`): customer, vehicle, slip no, amount, driver, remarks. Note: "billed to customer account".

STEP 3: COLLECTIONS
- Digital collections (`payments`): mode (UPI, Credit/Debit Card, IOCL Fleet Card, BPCL SmartFleet, HP DriveTrack), amount, batch/settlement ref, terminal. Shown as tappable mode tiles, each with an amount field.
- Expenses paid from cash (`expenses`): expense head, description, amount.
- Staff advances (`employee_advances`): employee, amount, remarks.

STEP 4: CASH COUNT
- A denomination counter grid (`denominations`) for ₹500, 200, 100, 50, 20, 10, 5, 2, 1, with − / + steppers and a count input. Line amount and total update live.
- A big reconciliation panel:
    Fuel Sales
    + Lubricant & Shop
    = Gross Sales
    − Credit Sales
    − Digital Collections (each mode listed)
    − Expenses
    − Staff Advances
    − Driver Cash
    = Expected Cash
    Cash Counted
    Short (−) / Excess (+)
- If |short/excess| is over ₹100, a Remarks field becomes required, with a hint.

STEP 5: REVIEW & SUBMIT
- A read-only summary of all steps with edit links.
- Cashier buttons: "Save Draft", "Submit for Approval".
- Manager view of the same screen: "Approve" (primary) and "Reject" (with a reason dialog).
- After approval, an "Accounting" panel lists the auto-created documents as links: Retail Fuel Invoice, Lubricant Invoice, Credit Invoices (one per customer), Settlement Journal.
- Buttons: Print Shift Report, Cancel (manager, with a warning that later shifts must be cancelled first).

Also show the error state for "Opening reading does not match last closing reading 12,57,304.94".
```

## Prompt 5: Tanker receipt (decantation)

```
Tanker Receipt list and form (stock keeper on phone, manager on desktop).

List columns: No, Date, Tank Lorry No, OMC Invoice No, Products, Invoice Qty, Received Qty, Short/Excess (L, coloured), Density OK, Status (Draft, Pending Verification, Accepted, Rejected).

Form sections:
1. Header: outlet, date/time, supplier (OMC), OMC invoice no & date, tank lorry no, driver, received by.
2. Safety checklist (toggles): Seals intact (plus seal numbers), Sales stopped from tank during decantation, Water paste test done. Turning off "Seals intact" makes Remarks required.
3. Products (one card per compartment/tank):
   - tank select (auto-fills fuel chip and last purchase rate);
   - compartment, invoice qty (L), rate/L, amount (auto);
   - Density check: challan density @15°C, observed density, observed temp, density @15°C. Show an auto variance badge, green if within ±3.0 kg/m³ and red "Do not decant" if outside.
   - Dips: dip before (mm), stock before (auto from the calibration chart), sales during decantation (L), dip after (mm), stock after (auto), received qty (auto), short/excess (auto, red if short).
4. A manager-only override: "Accept despite density variance" with required remarks.
5. Totals: invoice qty, received qty, total short/excess, invoice amount.
6. Actions: Save, Send for Verification, Accept (manager), Reject. After accept, show links to the Purchase Invoice and the Transit Loss/Gain Stock Entry.
```

## Prompt 6: Tank dip reading

```
Tank Dip Reading screen for phone.
- Reading type segmented control: Morning (Opening), Night (Closing), Shift Change, Before Decantation, After Decantation, Surprise Check.
- Date/time and recorded by.
- "Load tanks" creates one card per tank. Each card has: fuel chip; product dip (mm) with a large numeric input; water dip (mm); temperature (°C); observed density; density @15°C.
- Auto values per card: dip stock (L) from the calibration chart, water volume (L), book stock (L, from the system), variance (L) coloured.
- A visual tank cross-section showing the product level and a blue water layer.
- Warning banner if water is found: "Water found in T2-HSD (20 mm). Inform OMC."
- Totals at the bottom and a Submit button.
```

## Prompt 7: Daily Stock Register (DSR)

```
Daily Stock Register screen (manager / stock keeper), styled like the official OMC DSR register but modern.
- Date picker and a "Fetch day's data" button.
- Table with one row per tank and columns: Tank, Fuel, Opening Dip Stock, Receipts, Meter Sales, Testing (returned), Net Sales, Book Closing, Closing Dip (mm, editable), Closing Dip Stock, Gain(+)/Loss(−), Variance % of Sales, Permissible %, Within Limit (✓/✗ badge), Month-to-date Gain/Loss, Morning Density @15°C.
- Editing the closing dip recalculates the row live.
- A summary chip: "All tanks within permissible loss" (green) or "Loss beyond limit in T3-HSD" (red).
- Bottom: totals, remarks, and a Submit button with the note "On submit, ERPNext stock is reconciled to the physical dip."
- Print button for the DSR format with signature lines.
- Mobile: each tank is a stacked card.
```

## Prompt 8: Pump test log (5 litre measure)

```
Pump Test Log screen.
- Test type: Daily Check, Customer Request, W&M Inspection, OMC Inspection, After Repair.
- Tested by, 5 L measure certificate no.
- One row per nozzle: nozzle, fuel chip, measure (L, default 5), error (ml, ±), and an auto result badge: Pass (within ±15 ml per 5 L) or Fail. A returned-to-tank toggle.
- A big friendly "All passed" state, or a red alert: "DU2-N2 failed. Nozzle set Under Maintenance. Stop sales and call service engineer."
- History list with filters by nozzle and result.
```

## Prompt 9: Fuel price update

```
Fuel Price Update screen (owner/manager).
- Effective date and "Effective from 06:00" note. Source: OMC SMS / Portal / Email / Manual.
- "Load fuel items" fills rows: fuel chip, old price (auto), new price (input), change ₹ and % (auto, green down / red up arrows).
- Submit creates dated prices.
- Price history chart (line per fuel, last 60 days) and a table of past updates.
- Phone view: a quick "Today's prices" card on the home screen with a "Update prices" button.
```

## Prompt 10: Credit customers

```
Credit Customers module.
1. Customer list: name, vehicles count, credit limit, outstanding, % used (progress bar, amber over 80%, red over 100%), last payment date, overdue days.
2. Customer detail page:
   - Header with outstanding, limit, available credit.
   - Tabs: Vehicles (vehicle no, type, default fuel, driver, monthly limit, active toggle; add vehicle dialog); Statement (vehicle and slip-wise lines with Date, Voucher, Vehicle, Slip No, Item, Qty, Rate, Debit, Credit, running Balance; filters date range and vehicle; Print / Share PDF / WhatsApp buttons); Invoices; Payments.
3. Receive Payment dialog: customer, amount, mode (Cash, UPI, NEFT/RTGS, Cheque), reference no & date, and allocation to oldest invoices first (auto, editable).
4. Vehicle quick search from the top bar: typing "HR38AB" shows the vehicle, its owner and outstanding.
```

## Prompt 11: Reports hub

```
Reports hub with cards grouped as Sales, Stock, Credit, Compliance. Reports:
- Daily Sales Summary, Nozzle Sales Register, Shift Cash Reconciliation, Payment Mode Collection, Attendant Sales.
- Tank Stock Status, Stock Variance Register, Tanker Receipt Register.
- Credit Customer Statement, Fuel Price History, Compliance Expiry.

Report viewer template:
- Filter bar (date range, outlet, plus report-specific filters).
- A chart on top where relevant.
- A sortable table with a totals row and column picker.
- Export buttons for Excel / PDF / Print.
- Saved filter presets.
- A mobile-friendly card list mode.
```

## Prompt 12: Approvals inbox

```
Approvals inbox (manager/owner).
- Tabs: Shift Closings, Tanker Receipts.
- Each item card shows the key numbers: litres, gross, short/excess, or invoice vs received qty and density variance.
- Who submitted and when. Buttons: Approve, Reject (with reason), Open.
- Bulk approve for shift closings that are within the cash tolerance.
- Empty state: "All caught up".
```

## Prompt 13: Outlet setup

```
Setup screens (owner/manager), clean master-detail layout:
- Outlet profile: name, OMC, RO code, dealer, GSTIN, address, walk-in customer, cash account, short/excess account, staff advance account, lube store; plus a Licences table (PESO storage licence, Fire NOC, W&M, Pollution CTO, Trade licence) with valid-till dates and colour-coded expiry chips.
- Tanks: tank id, fuel, warehouse, capacity, dead stock, safe fill %, dimensions, calibration due date; plus a calibration chart editor (dip mm → litres table with CSV upload and a curve preview chart).
- Dispensing Units & Nozzles: a visual layout of DU cards, each with its nozzles (side A/B, fuel chip, tank, last reading, status). W&M stamping validity on each DU. Actions: "Meter change" dialog (old meter final reading, new start reading, reason) and "Set under maintenance".
- Shifts: name, sequence, start/end time.
- Settings: default outlet, fuel price list, VAT template for fuel, GST template for lubes, density tolerance (3.0 kg/m³), pump test tolerance (15 ml), default permissible loss %, cash short/excess tolerance (₹100), require shift approval toggle, reconcile stock on DSR toggle, expiry alert days.
- Users & roles: list users with role chips (Owner, Manager, Cashier, Stock Keeper), invite user, link to employee.
```

## Prompt 14: Notifications and alerts

```
Notifications drawer and full page.
- Types: licence/stamping expiring, DSR not submitted, shift pending approval, tanker density failed, pump test failed, credit limit crossed, low tank stock.
- Each has an icon, colour, time and deep link. Mark all read.
```

## Prompt 15: Print layouts (A4 and 80 mm thermal)

```
Printable layouts:
1. Shift Closing Report (A4):
   - Outlet header with RO code.
   - Meter readings table, credit sales table, lube sales.
   - Cash reconciliation box, denomination table.
   - Cashier and manager signature lines.
2. Daily Stock Register (A4 landscape), in the OMC register style.
3. Credit Customer Statement (A4) with vehicle-wise lines and a balance summary.
4. Fuel sale bill (80 mm thermal):
   - Outlet name, GSTIN, date/time.
   - Vehicle no, fuel, litres, rate, amount, payment mode.
   - The line "VAT included. Fuel outside GST."
```

## Prompt 16: Mobile cashier quick flow

```
A focused mobile flow for the cashier at shift end, optimised for one hand:
1. Screen "Closing readings": one nozzle per screen card with a giant numeric keypad. Swipe to the next nozzle; a progress dot row shows 8 nozzles.
2. Screen "Collections": mode tiles UPI / Card / Fleet with amount pads.
3. Screen "Count cash": denomination steppers with the live total.
4. Result screen: a huge status "Cash Tallied ✓" (green), or "Short ₹240" (red) with a remarks box, then a "Submit for Approval" button.
Include an offline banner "No network: saved on this device, will sync" and a sync-success toast.
```

---

## Integration notes (for the developer, not for Stitch)

| Screen | Backend |
| --- | --- |
| Login | `POST /api/method/login`, `GET /api/method/frappe.auth.get_logged_user`, `/api/method/logout`; roles from `frappe.boot` |
| KPI cards | `petrodiesel.dashboard.*` (todays_fuel_litres, todays_gross_sales, todays_credit_sales, todays_digital, todays_short_excess, month_gross_sales, month_fuel_litres, fuel_stock_litres, credit_outstanding, month_stock_variance) |
| Charts | `petrodiesel.dashboard.daily_fuel_sales / collection_mix / tank_levels / daily_stock_variance` |
| Tank gauges | report `Tank Stock Status` via `frappe.desk.query_report.run` |
| Shift closing | doctype `Shift Sale Entry`; prefill `...shift_sale_entry.get_nozzles`; denominations `get_default_denominations`; workflow `frappe.model.workflow.apply_workflow` (actions: Submit for Approval, Approve, Reject, Revise, Cancel) |
| Rates | `petrodiesel.petrodiesel.utils.get_rate` |
| Dip → litres | `petrodiesel.petrodiesel.utils.get_dip_volume` |
| Tanker / Dip / DSR / Pump test / Price / Meter change | doctypes `Tanker Receipt`, `Tank Dip Reading`, `Daily Stock Register` (method `fetch_data`), `Pump Test Log`, `Fuel Price Update` (`get_fuel_items`), `Nozzle Meter Change` |
| Credit | `Customer`, `Customer Vehicle`, report `Credit Customer Statement`, ERPNext `Payment Entry` |
| Reports | `frappe.desk.query_report.run` with report names above |
| Alerts | `Notification Log`, report `Compliance Expiry` |

The client must still calculate live totals for instant feedback. The server recalculates everything on save, so the UI never needs to post computed fields.
