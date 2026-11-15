# Copyright (c) 2026, Aman Boora and contributors
"""Serve the PetroDesk SPA at /petrodiesel."""

import frappe

no_cache = 1


def get_context(context):
	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()  # nosemgrep: tmp.claude-1000.-home-boora--claude-spares-spare-CfC2s3.5539f4da-34d8-44a3-9154-ee671e5b4956.scratchpad.frappe-semgrep-rules.rules.frappe-manual-commit -- intentional commit
	context.boot = {
		"csrf_token": csrf_token,
		"site_name": frappe.local.site,
		"petrodesk_user": frappe.session.user,
	}
	return context
