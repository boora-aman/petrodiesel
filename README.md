### Petrodiesel

Petrolium Management System

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app petrodiesel
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/petrodiesel
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.

### License

mit

Basic Setup



## **DAY 1: MANUAL SETUP (Foundation Data)**

These **CANNOT** be created via console - must use UI.

---

## **Step 1.1: Create Custom Roles**

1. Go to: **Home → Settings → Role → New**
2. Create these 5 roles:

**Role 1:**

* **Role Name** : `Pump Manager`
* **Desk Access** : ✓
* Save

**Role 2:**

* **Role Name** : `Cashier`
* **Desk Access** : ✓
* Save

**Role 3:**

* **Role Name** : `Stock Manager`
* **Desk Access** : ✓
* Save

**Role 4:**

* **Role Name** : `Credit Manager`
* **Desk Access** : ✓
* Save

**Role 5:**

* **Role Name** : `Nozzle Attendant`
* **Desk Access** : ✓
* Save

✅  **Checkpoint** : You should have 5 new custom roles

---

## **Step 1.2: Create Item Groups**

1. Go to: **Home → Stock → Item Group**
2. Click on **All Item Groups** (tree view)
3. Create this structure:

**Root: Products**

* Click **Products** → Click **Add Child**
  * **Item Group Name** : `Fuels`
  * **Parent Item Group** : Products
  * Save
* Click **Fuels** → Click **Add Child**
  * **Item Group Name** : `Petrol`
  * **Parent Item Group** : Fuels
  * Save
* Click **Fuels** → Click **Add Child**
  * **Item Group Name** : `Diesel`
  * **Parent Item Group** : Fuels
  * Save
* Click **Fuels** → Click **Add Child**
  * **Item Group Name** : `CNG`
  * **Parent Item Group** : Fuels
  * Save
* Click **Products** → Click **Add Child**
  * **Item Group Name** : `Lubricants`
  * **Parent Item Group** : Products
  * Save
* Click **Products** → Click **Add Child**
  * **Item Group Name** : `Accessories`
  * **Parent Item Group** : Products
  * Save

✅  **Checkpoint** : Tree should look like:

<pre class="not-prose w-full rounded font-mono text-sm font-extralight"><div class="codeWrapper text-light selection:text-super selection:bg-super/10 my-md relative flex flex-col rounded-lg font-mono text-sm font-normal bg-subtler"><div class="translate-y-xs -translate-x-xs bottom-xl mb-xl flex h-0 items-start justify-end md:sticky md:top-[calc(var(--header-height)+var(--size-xs))]"><div class="overflow-hidden rounded-full border-subtlest ring-subtlest divide-subtlest bg-base"><div class="border-subtlest ring-subtlest divide-subtlest bg-subtler"></div></div></div><div class="-mt-xl"><div><div data-testid="code-language-indicator" class="text-quiet bg-subtle py-xs px-sm inline-block rounded-br rounded-tl-lg text-xs font-thin">text</div></div><div><span><code><span><span>Products
</span></span><span>├── Fuels
</span><span>│   ├── Petrol
</span><span>│   ├── Diesel
</span><span>│   └── CNG
</span><span>├── Lubricants
</span><span>└── Accessories
</span><span></span></code></span></div></div></div></pre>

---

## **Step 1.3: Create Fuel Items**

1. Go to: **Home → Stock → Item → New Item**

**Item 1: Petrol**

* **Item Code** : `PETROL-MS`
* **Item Name** : `Petrol (Motor Spirit)`
* **Item Group** : Select `Fuels > Petrol`
* **Stock Settings** section:
  * **Default Unit of Measure** : `Litre`
  * **Is Stock Item** : ✓ (checked)
  * **Include Item in Manufacturing** : ✗ (unchecked)
  * **Maintain Stock** : ✓ (checked)
* **Purchase, Replenishment** section:
  * **Is Purchase Item** : ✓ (checked)
* **Sales** section:
  * **Is Sales Item** : ✓ (checked)
* **Save**

**Item 2: Diesel**

* **Item Code** : `DIESEL-HSD`
* **Item Name** : `Diesel (High Speed Diesel)`
* **Item Group** : Select `Fuels > Diesel`
* **Default Unit of Measure** : `Litre`
* **Is Stock Item** : ✓
* **Maintain Stock** : ✓
* **Is Purchase Item** : ✓
* **Is Sales Item** : ✓
* **Save**

**Item 3: CNG**

* **Item Code** : `CNG`
* **Item Name** : `Compressed Natural Gas`
* **Item Group** : Select `Fuels > CNG`
* **Default Unit of Measure** : `Kg`
* **Is Stock Item** : ✓
* **Maintain Stock** : ✓
* **Is Purchase Item** : ✓
* **Is Sales Item** : ✓
* **Save**

✅  **Checkpoint** : You should have 3 fuel items in Item List

---

## **Step 1.4: Create Warehouses**

1. Go to: **Home → Stock → Warehouse → New Warehouse**

**Warehouse 1:**

* **Warehouse Name** : `Tank 1 - Petrol`
* **Parent Warehouse** : Select `Stores - [Your Company]`
* **Is Group** : ✗ (unchecked)
* **Warehouse Type** : `Transit`
* **Save**

**Warehouse 2:**

* **Warehouse Name** : `Tank 2 - Diesel`
* **Parent Warehouse** : `Stores - [Your Company]`
* **Save**

**Warehouse 3:**

* **Warehouse Name** : `Tank 3 - CNG`
* **Parent Warehouse** : `Stores - [Your Company]`
* **Save**

**Warehouse 4:**

* **Warehouse Name** : `Lubricant Store`
* **Parent Warehouse** : `Stores - [Your Company]`
* **Save**

✅  **Checkpoint** : You should have 4 new warehouses under Stores

---

## **Step 1.5: Create Employees**

1. Go to: **Home → Human Resources → Employee → New Employee**

**Employee 1:**

* **First Name** : `John`
* **Last Name** : `Doe`
* **Employee Name** : `John Doe (Cashier)`
* **Gender** : `Male`
* **Date of Birth** : `1995-01-15`
* **Date of Joining** : Today's date
* **Company** : Your company
* **Employment Type** section:
  * **Status** : `Active`
  * **Designation** : `Cashier` (create new if doesn't exist)
  * **Department** : `Operations` (create new if doesn't exist)
* **Save**

**Employee 2:**

* **First Name** : `Mike`
* **Last Name** : `Wilson`
* **Employee Name** : `Mike Wilson (Supervisor)`
* **Gender** : `Male`
* **Date of Birth** : `1990-05-20`
* **Date of Joining** : Today's date
* **Company** : Your company
* **Status** : `Active`
* **Designation** : `Supervisor`
* **Department** : `Operations`
* **Save**

**Employee 3:**

* **First Name** : `Sarah`
* **Last Name** : `Manager`
* **Employee Name** : `Sarah Manager`
* **Gender** : `Female`
* **Date of Birth** : `1988-03-10`
* **Date of Joining** : Today's date
* **Company** : Your company
* **Status** : `Active`
* **Designation** : `Pump Manager`
* **Department** : `Operations`
* **Save**

✅  **Checkpoint** : You should have 3 employees
