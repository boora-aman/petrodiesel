# Copyright (c) 2025, Aman Boora and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def fetch_shift_advances(doc, method=None):
    """Fetch shift advances for the employee during salary period"""
    
    if not doc.employee or not doc.start_date or not doc.end_date:
        return
    
    # Get all advances for this employee in this period
    advances = frappe.db.sql("""
        SELECT 
            sea.employee,
            nsr.name as shift_reading,
            nsr.posting_date,
            nsr.shift,
            sea.advance_type,
            sea.amount,
            sea.reason
        FROM `tabShift Employee Advance` sea
        INNER JOIN `tabNozzle Shift Reading` nsr ON nsr.name = sea.parent
        WHERE nsr.docstatus = 1
        AND sea.employee = %(employee)s
        AND nsr.posting_date BETWEEN %(start_date)s AND %(end_date)s
        ORDER BY nsr.posting_date
    """, {
        'employee': doc.employee,
        'start_date': doc.start_date,
        'end_date': doc.end_date
    }, as_dict=1)
    
    # Clear existing advances
    doc.shift_advances = []
    
    # Add advances to child table
    total_advances = 0
    for adv in advances:
        doc.append('shift_advances', {
            'shift_reading': adv.shift_reading,
            'posting_date': adv.posting_date,
            'shift': adv.shift,
            'advance_type': adv.advance_type,
            'amount': adv.amount,
            'reason': adv.reason
        })
        total_advances += adv.amount
    
    doc.total_shift_advances = total_advances
    
    # Add to deductions if total advances > 0
    if total_advances > 0:
        # Check if "Advance Deduction" salary component exists
        if not frappe.db.exists("Salary Component", "Advance Deduction"):
            salary_component = frappe.get_doc({
                "doctype": "Salary Component",
                "salary_component": "Advance Deduction",
                "salary_component_abbr": "ADV",
                "type": "Deduction",
                "description": "Deduction for advances taken during shifts"
            })
            salary_component.insert(ignore_permissions=True)
            frappe.db.commit()
        
        # Check if already exists in deductions
        advance_exists = False
        for d in doc.deductions:
            if d.salary_component == "Advance Deduction":
                d.amount = total_advances
                advance_exists = True
                break
        
        # Add if not exists
        if not advance_exists:
            doc.append('deductions', {
                'salary_component': 'Advance Deduction',
                'abbr': 'ADV',
                'amount': total_advances
            })
