import os

import frappe
from frappe.modules.import_file import import_file_by_path


def sync_workspaces():
	"""Sync Workspace documents from this app's workspace export folder.

	This makes workspace JSON exports the source-of-truth (instead of fixtures),
	and ensures production migrations always restore the workspaces.
	"""
	workspace_root = os.path.join(os.path.dirname(__file__), "workspace")
	if not os.path.isdir(workspace_root):
		return

	# Import every .json file under petrodiesel/petrodiesel/workspace/**
	for root, _dirs, files in os.walk(workspace_root):
		for fname in files:
			if not fname.endswith(".json"):
				continue
			path = os.path.join(root, fname)

			# Only import standard export files where filename matches scrub(doc.name)
			try:
				with open(path) as f:
					doc = frappe.parse_json(f.read())
			except Exception:
				continue

			if not isinstance(doc, dict) or doc.get("doctype") != "Workspace" or not doc.get("name"):
				continue
			if os.path.splitext(fname)[0] != frappe.scrub(doc.get("name")):
				continue

			try:
				import_file_by_path(
					path,
					force=True,
					ignore_version=True,
					reset_permissions=True,
				)
			except Exception:
				frappe.log_error(
					title="Petrodiesel Workspace Sync Failed",
					message=f"Failed importing workspace export: {path}",
				)
