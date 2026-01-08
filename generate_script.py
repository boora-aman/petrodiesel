#!/usr/bin/env python3
"""
Petrodiesel Dashboard Generator
================================
This script generates all Number Cards, Charts, and Workspaces for Petrodiesel module.

Usage:
    python generate_dashboard.py

Output:
    Creates 3 folders with JSON files:
    - number_card/ (18 files)
    - dashboard_chart/ (8 files)
    - workspace/ (6 files)

After running, copy these folders to:
    petrodiesel/petrodiesel/

Then run: bench --site [site] migrate
"""

import json
import os

def create_directory(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"✅ Created directory: {path}")

def save_json(filepath, data):
    """Save JSON data to file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print(f"✅ Created: {filepath}")

# ============================================================================
# NUMBER CARDS
# ============================================================================

def generate_number_cards():
    """Generate all 18 Number Card JSON files"""

    create_directory('number_card')

    number_cards = [
        {
            "name": "Today\'s Fuel Sales",
            "label": "Today\'s Fuel Sales",
            "function": "get_today_fuel_sales",
            "document_type": "Shift Sale Entry",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#29CD42",
            "show_percentage_stats": 1,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Today\'s Total Collection",
            "label": "Today\'s Total Collection",
            "function": "get_today_total_collection",
            "document_type": "Shift Sale Entry",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#7575FF",
            "show_percentage_stats": 1,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Current Stock (Liters)",
            "label": "Current Stock (Liters)",
            "function": "get_current_stock",
            "document_type": "Tank Dip Reading",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#FFA00A",
            "show_percentage_stats": 0,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Week Shifts Count",
            "label": "Week Shifts Count",
            "function": "get_week_shifts_count",
            "document_type": "Shift Sale Entry",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#5E64FF",
            "show_percentage_stats": 1,
            "stats_time_interval": "Weekly"
        },
        {
            "name": "Credit Outstanding",
            "label": "Credit Outstanding",
            "function": "get_credit_outstanding",
            "document_type": "Credit Sale",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#FF5858",
            "show_percentage_stats": 0,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Month Revenue",
            "label": "Month Revenue",
            "function": "get_month_revenue",
            "document_type": "Shift Sale Entry",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#29CD42",
            "show_percentage_stats": 1,
            "stats_time_interval": "Monthly"
        },
        {
            "name": "Credit Sales This Month",
            "label": "Credit Sales This Month",
            "function": "get_credit_sales_count",
            "document_type": "Credit Sale",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#FF8989",
            "show_percentage_stats": 1,
            "stats_time_interval": "Monthly"
        },
        {
            "name": "Total Active Employees",
            "label": "Total Active Employees",
            "function": "get_total_employees",
            "document_type": "Employee",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#7575FF",
            "show_percentage_stats": 0,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Total Customers",
            "label": "Total Customers",
            "function": "get_total_customers",
            "document_type": "Customer",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#5E64FF",
            "show_percentage_stats": 0,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Active Nozzles",
            "label": "Active Nozzles",
            "function": "get_active_nozzles",
            "document_type": "Fuel Nozzle Master",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#29CD42",
            "show_percentage_stats": 0,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Total Fuel Tanks",
            "label": "Total Fuel Tanks",
            "function": "get_total_tanks",
            "document_type": "Fuel Tank Master",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#7575FF",
            "show_percentage_stats": 0,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Total Fuel Items",
            "label": "Total Fuel Items",
            "function": "get_total_items",
            "document_type": "Item",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#FFA00A",
            "show_percentage_stats": 0,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Cash Shortage/Variance",
            "label": "Cash Shortage/Variance",
            "function": "get_total_cash_shortage",
            "document_type": "Cashier Wise Shift Sale Entry",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#FF5858",
            "show_percentage_stats": 0,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Total Advance Given",
            "label": "Total Advance Given",
            "function": "get_total_advance_given",
            "document_type": "Shift Sale Entry",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#FFA00A",
            "show_percentage_stats": 0,
            "stats_time_interval": "Monthly"
        },
        {
            "name": "Today\'s Cash Collection",
            "label": "Today\'s Cash Collection",
            "function": "get_today_cash_collection",
            "document_type": "Shift Sale Entry",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#29CD42",
            "show_percentage_stats": 1,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Active Shifts Today",
            "label": "Active Shifts Today",
            "function": "get_active_shifts_today",
            "document_type": "Shift Sale Entry",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#5E64FF",
            "show_percentage_stats": 0,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Payments Received Today",
            "label": "Payments Received Today",
            "function": "get_payments_received_today",
            "document_type": "Customer Payment Entry",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#29CD42",
            "show_percentage_stats": 1,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Credit Customers Count",
            "label": "Credit Customers Count",
            "function": "get_credit_customers_count",
            "document_type": "Credit Sale",
            "type": "Custom",
            "module": "Petrodiesel",
            "doctype": "Number Card",
            "color": "#FF8989",
            "show_percentage_stats": 0,
            "stats_time_interval": "Daily"
        }
    ]

    for nc in number_cards:
        filename = nc['name'].lower().replace("'", "").replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
        filepath = f"number_card/{filename}.json"
        save_json(filepath, nc)

    print(f"\n✅ Generated {len(number_cards)} Number Cards\n")

# ============================================================================
# DASHBOARD CHARTS
# ============================================================================

def generate_charts():
    """Generate all 8 Dashboard Chart JSON files"""

    create_directory('dashboard_chart')

    charts = [
        {
            "name": "Daily Sales Trend",
            "chart_name": "Daily Sales Trend",
            "chart_type": "Line",
            "document_type": "Shift Sale Entry",
            "based_on": "posting_date",
            "value_based_on": "total_sales",
            "filters_json": "[[\"Shift Sale Entry\", \"docstatus\", \"=\", 1]]",
            "time_interval": "Daily",
            "timespan": "Last Week",
            "timeseries": 1,
            "module": "Petrodiesel",
            "doctype": "Dashboard Chart",
            "type": "Sum",
            "number_of_groups": 0,
            "is_public": 1,
            "color": "#29CD42"
        },
        {
            "name": "Fuel Sales Breakdown",
            "chart_name": "Fuel Sales Breakdown",
            "chart_type": "Donut",
            "document_type": "Shift Sale Entry",
            "based_on": "posting_date",
            "value_based_on": "total_fuel",
            "filters_json": "[[\"Shift Sale Entry\", \"docstatus\", \"=\", 1]]",
            "time_interval": "Daily",
            "timespan": "Last Month",
            "timeseries": 0,
            "module": "Petrodiesel",
            "doctype": "Dashboard Chart",
            "type": "Sum",
            "number_of_groups": 0,
            "is_public": 1,
            "color": "#7575FF"
        },
        {
            "name": "Weekly Revenue",
            "chart_name": "Weekly Revenue",
            "chart_type": "Bar",
            "document_type": "Shift Sale Entry",
            "based_on": "posting_date",
            "value_based_on": "total_sales",
            "filters_json": "[[\"Shift Sale Entry\", \"docstatus\", \"=\", 1]]",
            "time_interval": "Weekly",
            "timespan": "Last Month",
            "timeseries": 1,
            "module": "Petrodiesel",
            "doctype": "Dashboard Chart",
            "type": "Sum",
            "number_of_groups": 0,
            "is_public": 1,
            "color": "#FFA00A"
        },
        {
            "name": "Credit Outstanding Trend",
            "chart_name": "Credit Outstanding Trend",
            "chart_type": "Line",
            "document_type": "Credit Sale",
            "based_on": "posting_date",
            "value_based_on": "outstanding_amount",
            "filters_json": "[[\"Credit Sale\", \"docstatus\", \"=\", 1], [\"Credit Sale\", \"outstanding_amount\", \">\", 0]]",
            "time_interval": "Daily",
            "timespan": "Last Month",
            "timeseries": 1,
            "module": "Petrodiesel",
            "doctype": "Dashboard Chart",
            "type": "Sum",
            "number_of_groups": 0,
            "is_public": 1,
            "color": "#FF5858"
        },
        {
            "name": "Monthly Fuel vs Non-Fuel Sales",
            "chart_name": "Monthly Fuel vs Non-Fuel Sales",
            "chart_type": "Bar",
            "document_type": "Shift Sale Entry",
            "based_on": "posting_date",
            "value_based_on": "total_fuel",
            "filters_json": "[[\"Shift Sale Entry\", \"docstatus\", \"=\", 1]]",
            "time_interval": "Monthly",
            "timespan": "Last Year",
            "timeseries": 1,
            "module": "Petrodiesel",
            "doctype": "Dashboard Chart",
            "type": "Sum",
            "number_of_groups": 0,
            "is_public": 1,
            "color": "#5E64FF"
        },
        {
            "name": "Payment Collections",
            "chart_name": "Payment Collections",
            "chart_type": "Line",
            "document_type": "Customer Payment Entry",
            "based_on": "posting_date",
            "value_based_on": "paid_amount",
            "filters_json": "[[\"Customer Payment Entry\", \"docstatus\", \"=\", 1]]",
            "time_interval": "Daily",
            "timespan": "Last Week",
            "timeseries": 1,
            "module": "Petrodiesel",
            "doctype": "Dashboard Chart",
            "type": "Sum",
            "number_of_groups": 0,
            "is_public": 1,
            "color": "#29CD42"
        },
        {
            "name": "Stock Level Trends",
            "chart_name": "Stock Level Trends",
            "chart_type": "Line",
            "document_type": "Tank Dip Reading",
            "based_on": "posting_date",
            "value_based_on": "stock_qty",
            "filters_json": "[[\"Tank Dip Reading\", \"docstatus\", \"=\", 1]]",
            "time_interval": "Daily",
            "timespan": "Last Week",
            "timeseries": 1,
            "module": "Petrodiesel",
            "doctype": "Dashboard Chart",
            "type": "Sum",
            "number_of_groups": 0,
            "is_public": 1,
            "color": "#FFA00A"
        },
        {
            "name": "Tanker Receipts",
            "chart_name": "Tanker Receipts",
            "chart_type": "Bar",
            "document_type": "Tanker Receipt",
            "based_on": "posting_date",
            "value_based_on": "total_quantity",
            "filters_json": "[[\"Tanker Receipt\", \"docstatus\", \"=\", 1]]",
            "time_interval": "Weekly",
            "timespan": "Last Month",
            "timeseries": 1,
            "module": "Petrodiesel",
            "doctype": "Dashboard Chart",
            "type": "Sum",
            "number_of_groups": 0,
            "is_public": 1,
            "color": "#7575FF"
        }
    ]

    for chart in charts:
        filename = chart['name'].lower().replace(" ", "_").replace("-", "_")
        filepath = f"dashboard_chart/{filename}.json"
        save_json(filepath, chart)

    print(f"\n✅ Generated {len(charts)} Dashboard Charts\n")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("PETRODIESEL DASHBOARD GENERATOR")
    print("=" * 80)
    print()

    generate_number_cards()
    generate_charts()
    # Workspaces are too large - will create separately

    print("=" * 80)
    print("GENERATION COMPLETE!")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("1. Copy generated folders to: petrodiesel/petrodiesel/")
    print("2. Run: bench --site [your-site] migrate")
    print("3. Run: bench --site [your-site] clear-cache")
    print("4. Reload browser")
    print()
    print("Note: Workspace JSONs will be created separately due to size")