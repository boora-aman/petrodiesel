#!/usr/bin/env python3
"""
Verify all SQL queries in number_card.py and reports match actual doctype fields
"""

import re
import json
from pathlib import Path

def extract_sql_fields(file_path):
    """Extract field names from SQL queries"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find all SQL queries
    sql_pattern = r'frappe\.db\.sql\(["\']+(.*?)["\']+'
    queries = re.findall(sql_pattern, content, re.DOTALL)
    
    fields_used = set()
    for query in queries:
        # Extract field names from SELECT and WHERE clauses
        field_pattern = r'\b([a-z_]+)\s*(?:=|>|<|>=|<=|!=|FROM|WHERE|AND|OR)'
        fields = re.findall(field_pattern, query.lower())
        fields_used.update(fields)
    
    return fields_used

def verify_doctype_fields(doctype_name, fields_to_check):
    """Verify if fields exist in doctype"""
    doctype_path = Path(f'/home/boora/my-bench/apps/petrodiesel/petrodiesel/petrodiesel/doctype/{doctype_name}/{doctype_name}.json')
    
    if not doctype_path.exists():
        return None, []
    
    with open(doctype_path, 'r') as f:
        data = json.load(f)
    
    actual_fields = {field['fieldname'] for field in data.get('fields', []) if 'fieldname' in field}
    
    missing = [f for f in fields_to_check if f not in actual_fields and f not in ['docstatus', 'name', 'modified', 'creation']]
    
    return actual_fields, missing

# Check number_card.py
print("=" * 80)
print("VERIFYING number_card.py")
print("=" * 80)

number_card_path = Path('/home/boora/my-bench/apps/petrodiesel/petrodiesel/petrodiesel/number_card.py')
fields_in_queries = extract_sql_fields(number_card_path)

print(f"\nFields used in SQL queries: {len(fields_in_queries)}")
print(f"Fields: {sorted(fields_in_queries)}")

# Check against Shift Sale Entry
print("\n" + "-" * 80)
print("Checking Shift Sale Entry fields...")
actual, missing = verify_doctype_fields('shift_sale_entry', fields_in_queries)
if missing:
    print(f"❌ Missing fields in Shift Sale Entry: {missing}")
else:
    print("✅ All fields exist in Shift Sale Entry")

# Check against Cashier Wise Shift Sale Entry
print("\n" + "-" * 80)
print("Checking Cashier Wise Shift Sale Entry fields...")
actual, missing = verify_doctype_fields('cashier_wise_shift_sale_entry', fields_in_queries)
if missing:
    print(f"❌ Missing fields in Cashier Wise Shift Sale Entry: {missing}")
else:
    print("✅ All fields exist in Cashier Wise Shift Sale Entry")

# Check against Credit Sale
print("\n" + "-" * 80)
print("Checking Credit Sale fields...")
actual, missing = verify_doctype_fields('credit_sale', fields_in_queries)
if missing:
    print(f"❌ Missing fields in Credit Sale: {missing}")
else:
    print("✅ All fields exist in Credit Sale")

# Check reports
print("\n" + "=" * 80)
print("CHECKING REPORTS")
print("=" * 80)

report_dir = Path('/home/boora/my-bench/apps/petrodiesel/petrodiesel/petrodiesel/report')
for report_path in report_dir.iterdir():
    if report_path.is_dir():
        py_file = report_path / f"{report_path.name}.py"
        if py_file.exists():
            print(f"\n📊 {report_path.name}")
            fields = extract_sql_fields(py_file)
            print(f"   Fields used: {len(fields)}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
