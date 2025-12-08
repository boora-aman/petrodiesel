"""Portal profile APIs for Customer users."""
from __future__ import annotations

import frappe
from frappe import _
from frappe.contacts.doctype.address.address import get_default_address, get_address_display
from frappe.contacts.doctype.contact.contact import get_default_contact
from frappe.exceptions import PermissionError


def _session_customer() -> str | None:
	"""Resolve the Customer linked to the current user (email or contact link)."""
	user = frappe.session.user
	if user == "Guest":
		return None

	emails = {user}
	user_email = frappe.db.get_value("User", user, "email")
	if user_email:
		emails.add(user_email)

	for email in emails:
		customer = frappe.db.get_value("Customer", {"email_id": email}, "name")
		if customer:
			return customer
		customer = frappe.db.get_value("Customer", {"user_id": email}, "name")
		if customer:
			return customer

	contact = None
	if emails:
		contact = frappe.db.get_value("Contact", {"email_id": ["in", list(emails)]}, "name")
	if contact:
		link = frappe.db.get_value(
			"Dynamic Link",
			{
				"parenttype": "Contact",
				"parent": contact,
				"link_doctype": "Customer",
			},
			"link_name",
		)
		if link:
			return link

	return None


def _ensure_customer_owner(customer_name: str) -> None:
	"""Basic check that the logged-in user is linked to this customer."""
	if frappe.session.user == "Administrator":
		return
	linked = _session_customer()
	if linked and linked == customer_name:
		return
	frappe.throw(_("You are not allowed to update this profile."), PermissionError)


def _primary_address(customer_name: str):
	name = get_default_address("Customer", customer_name)
	if not name:
		return None
	address = frappe.get_doc("Address", name).as_dict()
	address["display"] = get_address_display(address)
	return address


def _contacts(customer_name: str):
	primary_contact_name = get_default_contact("Customer", customer_name)
	contacts = []
	link_rows = frappe.get_all(
		"Dynamic Link",
		filters={
			"link_doctype": "Customer",
			"link_name": customer_name,
			"parenttype": "Contact",
		},
		fields=["parent"],
	)
	for row in link_rows:
		contact = frappe.get_doc("Contact", row.parent).as_dict()
		contact["is_primary_contact"] = 1 if contact.get("name") == primary_contact_name else 0
		contacts.append(contact)
	return primary_contact_name, contacts


def _files(customer_name: str):
	return frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Customer", "attached_to_name": customer_name},
		fields=["name", "file_name", "file_url", "is_private", "attached_to_field"],
	)


def _indian_compliance(customer) -> bool:
	territory = (customer.territory or "").lower()
	country = (customer.country or "").lower()
	return "india" in territory or "india" in country


@frappe.whitelist(methods=["GET"])
def get_customer_profile():
	"""Return Customer with primary address/contact, documents, and compliance flags."""
	customer_name = _session_customer()
	if not customer_name:
		frappe.throw(_("No Customer is linked to this user."), PermissionError)

	customer = frappe.get_doc("Customer", customer_name)
	primary_contact_name, contact_persons = _contacts(customer_name)
	data = customer.as_dict()
	data.update(
		{
			"primary_address": _primary_address(customer_name),
			"primary_contact": frappe.get_doc("Contact", primary_contact_name).as_dict()
			if primary_contact_name
			else None,
			"contact_persons": contact_persons,
			"documents": _files(customer_name),
			"is_frozen": bool(customer.get("is_frozen") or customer.get("disabled")),
			"indian_compliance": _indian_compliance(customer),
		}
	)
	return data


def _upsert_primary_address(customer, address_text: str | None):
	if not address_text:
		return None

	existing_name = get_default_address("Customer", customer.name)
	if existing_name:
		addr = frappe.get_doc("Address", existing_name)
		addr.address_line1 = address_text
		addr.address_title = addr.address_title or customer.customer_name
		addr.address_type = addr.address_type or "Billing"
		addr.is_primary_address = 1
		addr.save(ignore_permissions=True)
	else:
		addr = frappe.get_doc(
			{
				"doctype": "Address",
				"address_title": customer.customer_name,
				"address_type": "Billing",
				"address_line1": address_text,
				"is_primary_address": 1,
				"links": [
					{"link_doctype": "Customer", "link_name": customer.name},
				],
			}
		)
		addr.insert(ignore_permissions=True)

	customer.customer_primary_address = addr.name
	return addr.name


@frappe.whitelist(methods=["POST"])
def update_customer_profile(**kwargs):
	"""Update Customer basic fields and primary address."""
	customer_name = kwargs.get("customer_name") or _session_customer()
	if not customer_name:
		frappe.throw(_("No Customer is linked to this user."), PermissionError)
	_ensure_customer_owner(customer_name)

	customer = frappe.get_doc("Customer", customer_name)

	field_map = {
		"mobile_no": "mobile_no",
		"phone": "phone",
		"email": "email_id",
		"email_id": "email_id",
		"website": "website",
		"customer_group": "customer_group",
		"territory": "territory",
		"customer_type": "customer_type",
	}

	for incoming, target in field_map.items():
		value = kwargs.get(incoming)
		if value is not None:
			customer.set(target, value)

	gst = kwargs.get("gst_number") or kwargs.get("gstin")
	if gst is not None:
		customer.gstin = gst

	address_text = kwargs.get("primary_address")

	customer.flags.ignore_mandatory = True
	customer.save(ignore_permissions=True)

	_upsert_primary_address(customer, address_text)

	return {"success": True, "customer": customer.name}
