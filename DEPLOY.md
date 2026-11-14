# Deploying PetroDesk on a VPS (with demo data)

This sets up a production Frappe v16 bench with ERPNext, HRMS and Petrodiesel, loads three weeks of demo data, and serves the PetroDesk app at `https://<your-domain>/petrodiesel`. After logging in, pump staff land in the app; the ERPNext desk is still at `/desk`.

## 1. Server

| Item | Minimum | Recommended |
| --- | --- | --- |
| OS | Ubuntu 22.04 / 24.04 LTS (64-bit) | Ubuntu 24.04 |
| CPU / RAM | 2 vCPU / 4 GB (add 2 GB swap) | 4 vCPU / 8 GB |
| Disk | 40 GB SSD | 80 GB SSD |
| Domain | An A record pointing to the VPS IP, e.g. `pump.example.com` | |
| Ports | 22, 80, 443 open | |

Software installed below: Python 3.14, Node.js 24 + Yarn 1, MariaDB 11.8, Redis, Nginx, Supervisor, wkhtmltopdf 0.12.6 (patched Qt), Git, cron.

## 2. Packages (as root)

```bash
apt update && apt upgrade -y
apt install -y git curl build-essential pkg-config software-properties-common \
  redis-server nginx supervisor cron xvfb libfontconfig fontconfig \
  libmysqlclient-dev libffi-dev libssl-dev
# MariaDB 11.8
curl -LsS https://r.mariadb.com/downloads/mariadb_repo_setup | bash -s -- --mariadb-server-version="mariadb-11.8"
apt install -y mariadb-server mariadb-client
# Node 24 + yarn
curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && apt install -y nodejs && npm install -g yarn
# wkhtmltopdf (patched qt) for PDF printing
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.jammy_amd64.deb
apt install -y ./wkhtmltox_0.12.6.1-3.jammy_amd64.deb
# a 2 GB swap file helps on 4 GB machines
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile && echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

MariaDB settings (`/etc/mysql/mariadb.conf.d/99-frappe.cnf`):

```ini
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
```

```bash
systemctl restart mariadb
mariadb-secure-installation   # set a root password, remove anonymous users and the test DB
```

## 3. Frappe user, Python and bench

```bash
adduser frappe && usermod -aG sudo frappe
su - frappe
curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.bashrc
uv python install 3.14
uv tool install frappe-bench
bench init frappe-bench --frappe-branch version-16 --python "$(uv python find 3.14)"
cd frappe-bench
chmod -R o+rx /home/frappe
```

## 4. Apps

```bash
bench get-app erpnext --branch version-16
bench get-app hrms --branch version-16
bench get-app https://github.com/boora-aman/petrodiesel --branch rebuild/indian-retail-outlet
```

`get-app` installs PetroDesk's frontend dependencies and builds it (`yarn build` in `apps/petrodiesel/frontend`).

## 5. Site with demo data

```bash
bench new-site pump.example.com --install-app erpnext --install-app hrms --install-app petrodiesel \
  --admin-password '<strong-admin-password>' --mariadb-root-password '<mariadb-root-password>'
bench use pump.example.com

# Demo: company "Shree Balaji Fuels", one outlet, tanks, machines, staff, credit customers,
# demo users and 21 days of shifts, tankers, dips, DSRs and payments (takes ~5–10 minutes).
bench --site pump.example.com execute petrodiesel.demo.setup_demo --kwargs "{'days': 21}"

bench build --app petrodiesel
bench --site pump.example.com enable-scheduler
bench --site pump.example.com set-config maintenance_mode 0
```

Run the demo only on a **new** site: it completes the setup wizard itself. To start a real outlet instead, skip the demo command, finish the ERPNext setup wizard, and follow the *Setup checklist* in `README.md`.

## 6. Production (Nginx + Supervisor + HTTPS)

```bash
sudo bench setup production frappe          # nginx + supervisor, as the frappe user
bench setup nginx && sudo systemctl reload nginx
sudo bench setup lets-encrypt pump.example.com   # free SSL certificate
```

Open `https://pump.example.com/login` and sign in.

## 7. Demo logins

Password for all: `Demo@12345` (change or disable them before real use).

| Login | Role | Lands on |
| --- | --- | --- |
| owner@petro.demo | Pump Owner | /petrodiesel (everything) |
| manager@petro.demo | Pump Manager | /petrodiesel (approvals, stock register, prices) |
| cashier@petro.demo | Pump Cashier | /petrodiesel (shift closing, dips, pump tests) |
| stock@petro.demo | Pump Stock Keeper | /petrodiesel (tankers, dips, purchases, transfers) |
| Administrator | System Manager | /petrodiesel; ERPNext desk at /desk |

## 8. Updating later

```bash
cd ~/frappe-bench
bench update --pull --apps petrodiesel        # or: cd apps/petrodiesel && git pull
bench --site pump.example.com migrate
bench build --app petrodiesel
sudo supervisorctl restart all
```

## 9. Backups

```bash
bench --site pump.example.com backup --with-files      # one-off
# daily at 02:30
(crontab -l; echo "30 2 * * * cd /home/frappe/frappe-bench && bench --site pump.example.com backup --with-files") | crontab -
```

Backups are written to `sites/pump.example.com/private/backups/`. Copy them off the server regularly.

## Notes

- **URLs:** the app is at `/petrodiesel`; old `/petrodesk` links redirect there. The ERPNext desk stays at `/desk`. The user guide PDF is at `/assets/petrodiesel/docs/PetroDesk-User-Guide.pdf` and is linked from the app's user menu.
- **Landing page:** the `role_home_page` hook sends Pump Owner, Manager, Cashier and Stock Keeper users to `/petrodiesel` after login. Setup also sets *System Settings → Default App* to Petrodiesel if it is empty.
- **Accounts setting:** setup turns off *Accounts Settings → Automatically Add Taxes from Item Tax Template*. Fuel items carry a VAT template for sales; without this, VAT would also be added to fuel purchase invoices.
- **Payroll:** the demo gives the staff a basic salary structure, so advances can be recovered from salary. On a real outlet, assign salary structures in HR first.
- **Running tests:** `bench --site <site> set-config allow_tests true && bench --site <site> run-tests --app petrodiesel`. Run them on a copy, not on a live site.
