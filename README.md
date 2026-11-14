# Petrodiesel

Petrol pump (fuel retail outlet) management for Indian dealers, built on Frappe v16 and ERPNext v16.

It covers the daily routine of an IOCL / BPCL / HPCL / Nayara / Jio-bp outlet: nozzle meter readings, shift cash closing, credit (indent / slip) customers with vehicles, UPI / card / fleet-card collections, tanker decantation with density and dip checks, tank dips, the Daily Stock Register (DSR), daily price changes and the 5 litre pump test. Every operational document posts to ERPNext, so stock, receivables, cash, bank and the profit and loss account stay in step with the forecourt.

## Install

```bash
bench get-app https://github.com/boora-aman/petrodiesel --branch rebuild/indian-retail-outlet
bench --site <site> install-app erpnext petrodiesel
bench --site <site> migrate
```

`after_install` / `after_migrate` create the roles, custom fields on ERPNext doctypes, the approval workflows and default settings. ERPNext is required; HRMS is optional (only Employee is used).

### Demo data

```bash
bench --site <site> execute petrodiesel.demo.setup_demo --kwargs "{'days': 21}"
```

Use the demo on a fresh site. It runs the setup wizard if needed and creates the company *Shree Balaji Fuels* (abbr SBF) with one outlet. The outlet has 4 tanks (MS, 2 × HSD, XP95) with calibration charts, 2 dispensing units with 8 nozzles, three shifts, five credit customers with vehicles, staff, VAT and GST templates, and modes of payment. It then simulates `days` business days of operations. The last shift of the last day is left *Pending Approval* so the workflow can be tried.

Demo logins (password `Demo@12345`):

| User | Role |
| --- | --- |
| owner@petro.demo | Pump Owner |
| manager@petro.demo | Pump Manager |
| cashier@petro.demo | Pump Cashier |
| stock@petro.demo | Pump Stock Keeper |

### Tests

```bash
bench --site <site> set-config allow_tests true
bench --site <site> run-tests --app petrodiesel
```

The tests use the demo masters and roll back their own data.

## Setup checklist (real outlet)

1. **Company:** create it in ERPNext with the fiscal year and chart of accounts.
2. **Items:** set *Petrol Pump Product Type* (Fuel / Lubricant) on each item. For fuels also set *Permissible Stock Loss %* (MS ≈ 0.6, HSD ≈ 0.25; follow your OMC's figures) and an Item Tax Template with the state VAT rate.
3. **Tax templates:** create a fuel VAT template and a lubricant GST 18% template, both *Included in Print Rate*.
4. **Warehouses:** one per tank, plus one for the lube store.
5. **Fuel Station:** fill in the OMC, RO code, walk-in customer, cash account, cash short/excess account, staff advance account and licences (PESO, fire NOC, W&M and so on).
6. **Fuel Tank Master:** one per tank, with the calibration chart rows (dip mm → litres) from the calibration certificate.
7. **Dispensing Unit** (with the W&M stamping validity), then **Fuel Nozzle Master** with the totalizer reading at go-live.
8. **Shift Master:** e.g. Morning / Evening / Night, with a sequence.
9. **Mode of Payment:** UPI, Card, and one per fleet card (XTRAPOWER, SmartFleet, DriveTrack Plus), each with its company account.
10. **Petrodiesel Settings:** default station, fuel price list, tax templates and tolerances.
11. **Opening stock:** post a Stock Reconciliation (Opening Stock) per tank.
12. **Prices:** submit the first Fuel Price Update.

## PetroDesk frontend (Vue 3 + frappe-ui)

A mobile-first app for the forecourt at **`/petrodiesel`** (login, role-based home, shift closing wizard, tanker
decantation, dips, DSR, pump tests, prices, credit customers, approvals, reports, alerts, outlet setup). It uses
the same backend: every calculation is previewed on the server (`petrodiesel.api.preview`) while the user types,
and saving goes through the same validation, workflows and ERPNext postings as Desk.

```bash
cd apps/petrodiesel/frontend
yarn install
yarn build          # outputs to petrodiesel/public/frontend and petrodiesel/www/petrodiesel.html
yarn dev            # dev server on :8087 proxying to the bench (set FRAPPE_WEB_SERVER_PORT if not 8000)
```

`bench build` also builds it (root `package.json`). The UI design came from Google Stitch screens
(`docs/google_stitch_prompt.md`).

## Roles

| Role | Can do |
| --- | --- |
| Pump Owner | Everything, including settings, prices and approvals |
| Pump Manager | Approves shifts, tanker receipts and DSR; maintains masters |
| Pump Cashier | Creates shift closings, credit slips, collections; dip readings and pump tests |
| Pump Stock Keeper | Tanker receipts, dip readings, DSR, pump tests |

The app also grants these roles read access to the ERPNext masters and reports they need.

## Daily workflow

1. **06:00: Fuel Price Update.** Enter the OMC's prices for the day. This creates dated Item Prices (history kept) in the fuel price list.
2. **Morning dip (Tank Dip Reading, *Morning (Opening)*).** Record the product dip, water dip, temperature and density at 15°C per tank. The dip is converted to litres from the calibration chart and compared with ERPNext book stock.
3. **Pump Test Log.** Record the 5 L measure test per nozzle. An error beyond ±15 ml per 5 L fails the test and puts the nozzle *Under Maintenance*.
4. **Tanker Receipt.** Record seal and water checks, then the challan density against the observed density at 15°C. A variance beyond ±3 kg/m³ blocks the receipt unless a manager overrides it with remarks. Record the dips before and after decantation and any sales during decantation.
   - On approval the app submits a Purchase Invoice (update stock) for the invoiced quantity into the tank warehouse.
   - It also submits a Stock Entry for the transit shortage or excess.
5. **Shift Sale Entry (per shift, or per cashier).** Click *Get Active Nozzles*: the opening readings come from the last closing and the rate from the day's price.
   - Enter the closing totalizer and the test litres.
   - Add credit slips (customer, vehicle, slip no.), lube sales, cash paid to fleet drivers, UPI / card / fleet-card totals, expenses and staff advances.
   - Count the cash by denomination; the form shows expected cash and short / excess live.
   - If a price changes mid-shift, add a second row for the nozzle; its opening is the first row's closing.
   - The cashier sends the entry for approval and the manager approves. On approval it posts:
     - a **retail fuel Sales Invoice** (walk-in customer, fuel VAT template, stock out of each tank warehouse);
     - a **lubricant Sales Invoice** (GST template);
     - one **credit Sales Invoice per customer**, with vehicle and slip number on each line;
     - a **settlement Journal Entry** that settles the walk-in invoices against cash counted, each payment mode's account, expenses, staff advances, driver cash (debited to the credit customer) and the cash short/excess account.
   - The nozzle totalizers move forward. Cancelling reverses everything, latest shift first.
6. **Night dip (Tank Dip Reading, *Night (Closing)*).**
7. **Daily Stock Register.** *Fetch Day's Data* builds, per tank: opening dip stock + receipts − (meter sales − testing) = book closing, against the closing dip.
   - It shows the gain or loss, % of sales against the permissible loss %, the month-to-date total and morning density.
   - On submit a Stock Reconciliation brings the ERPNext tank stock to the physical dip, if that option is enabled in settings.
8. **Bank deposit and customer receipts.** Use ERPNext Journal Entry / Payment Entry. Run the *Credit Customer Statement* (vehicle-wise) report for billing.

## Reports

| Report | Purpose |
| --- | --- |
| Daily Sales Summary | Litres per fuel and sales/collection split per day, with chart |
| Nozzle Sales Register | Opening, closing, test and sale per nozzle per shift |
| Shift Cash Reconciliation | Expected vs counted cash per shift and cashier |
| Payment Mode Collection | Cash / credit / UPI / card / fleet per day |
| Attendant Sales | Litres and value per attendant (DSM) |
| Tank Stock Status | Book stock, ullage, fill %, days of cover, reorder flag |
| Stock Variance Register | DSR rows over a period |
| Tanker Receipt Register | Shortage and density check per decantation |
| Credit Customer Statement | Vehicle / slip-wise statement with running balance |
| Fuel Price History | Price changes with chart |
| Compliance Expiry | Licences, W&M stamping and tank calibration due |

The **Petrol Pump** workspace has number cards for today and the month, charts for daily litres, collection mix, tank levels and DSR gain/loss, and quick-entry shortcuts. A daily job notifies owners and managers about expiring licences and stamping, and about a DSR not submitted for the previous day.

## Notes on Indian practice

- **Tax:** petrol and diesel are outside GST and carry state VAT, so prices are VAT-inclusive. Lubricants carry 18% GST. Each goes on its own invoice.
- **Totalizers** are cumulative and never reset. A replaced meter needs the nozzle's totalizer updated by a manager before the next shift.
- **Test fuel** returned to the tank is not a sale; it is excluded from billed litres and from DSR net sales.
- **Shrinkage:** the permissible loss % differs by OMC and product, so set it per item.

## Deployment

See [DEPLOY.md](DEPLOY.md) for a step-by-step VPS setup with demo data.

## License

MIT
