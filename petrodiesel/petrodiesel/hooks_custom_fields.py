# Copyright (c) 2026, Aman Boora and contributors
# For license information, please see license.txt

import frappe

def after_install():
    """Create custom fields after app installation"""
    from petrodiesel.petrodiesel.custom_fields import create_customer_custom_fields
    create_customer_custom_fields()
