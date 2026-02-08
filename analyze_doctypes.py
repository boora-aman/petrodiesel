#!/usr/bin/env python3
"""
Comprehensive Doctype Analysis Script
Analyzes all doctypes in petrodiesel app to verify field consistency
"""

import json
import os
from pathlib import Path

def analyze_doctype_fields(doctype_path):
    """Extract all fields from a doctype JSON file"""
    json_file = doctype_path / f"{doctype_path.name}.json"
    
    if not json_file.exists():
        return None
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        fields = {}
        for field in data.get('fields', []):
            fieldname = field.get('fieldname')
            fieldtype = field.get('fieldtype')
            if fieldname:
                fields[fieldname] = {
                    'fieldtype': fieldtype,
                    'label': field.get('label', ''),
                    'options': field.get('options', ''),
                    'reqd': field.get('reqd', 0)
                }
        
        return {
            'name': data.get('name'),
            'is_submittable': data.get('is_submittable', 0),
            'fields': fields
        }
    except Exception as e:
        print(f"Error reading {json_file}: {e}")
        return None

def main():
    doctype_dir = Path('/home/boora/my-bench/apps/petrodiesel/petrodiesel/petrodiesel/doctype')
    
    # Key doctypes to analyze
    key_doctypes = [
        'shift_sale_entry',
        'cashier_wise_shift_sale_entry',
        'credit_sale',
        'customer_payment_entry',
        'customer_bill',
        'fuel_tank_master',
        'fuel_nozzle_master',
        'tanker_receipt',
        'tank_dip_reading',
        'shift_master'
    ]
    
    print("=" * 80)
    print("PETRODIESEL DOCTYPE FIELD ANALYSIS")
    print("=" * 80)
    
    for doctype_name in key_doctypes:
        doctype_path = doctype_dir / doctype_name
        if not doctype_path.exists():
            print(f"\n❌ {doctype_name}: NOT FOUND")
            continue
        
        info = analyze_doctype_fields(doctype_path)
        if not info:
            print(f"\n❌ {doctype_name}: ERROR READING")
            continue
        
        print(f"\n{'='*80}")
        print(f"📋 {info['name']}")
        print(f"{'='*80}")
        print(f"Submittable: {'Yes' if info['is_submittable'] else 'No'}")
        print(f"Total Fields: {len(info['fields'])}")
        
        # Check for key financial fields
        financial_fields = ['total_sales', 'total_fuel_sales', 'total_other_sales', 
                          'total_credit_fuel', 'cash_received', 'expected_cash', 
                          'cash_variance', 'outstanding_amount', 'paid_amount',
                          'total_amount', 'total_online', 'total_expenses',
                          'total_emp_advances', 'total_driver_cash']
        
        print("\n🔍 Key Financial Fields:")
        for field in financial_fields:
            if field in info['fields']:
                finfo = info['fields'][field]
                print(f"  ✅ {field:25} -> {finfo['fieldtype']:15} {finfo['label']}")
            else:
                print(f"  ❌ {field:25} -> MISSING")
        
        # Check for posting fields
        posting_fields = ['posting_date', 'posting_time', 'docstatus']
        print("\n📅 Posting Fields:")
        for field in posting_fields:
            if field in info['fields']:
                finfo = info['fields'][field]
                print(f"  ✅ {field:25} -> {finfo['fieldtype']:15}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
