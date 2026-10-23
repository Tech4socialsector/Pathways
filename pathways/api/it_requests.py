# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""IT Requests page for IT & Facilities (folder 12: laptop, NLS email ID,
access card / seating for a new joiner). Access is Role Permissions on
IT Facilities Provisioning Request (read to see, write to tick and
complete); nothing here names a role.
"""

import frappe
from frappe import _

TICKS = ("laptop_arranged", "official_email_created", "access_card_issued", "seating_arranged")
FIELDS = [
	"name", "joining", "application", "employee_name", "designation", "department", "date_of_joining", "reporting_location",
	"personal_email", "official_email", "mobile_number", *TICKS, "status", "remarks", "completed_by", "completed_on",
]


@frappe.whitelist()
def list_requests():
	rows = frappe.get_list(
		"IT Facilities Provisioning Request", fields=FIELDS, order_by="date_of_joining asc, modified desc", limit_page_length=0
	)
	for r in rows:
		r.completed_by_name = frappe.utils.get_fullname(r.completed_by) if r.completed_by else ""
	return {"requests": rows, "can_write": bool(frappe.has_permission("IT Facilities Provisioning Request", "write"))}


@frappe.whitelist()
def save_request(name, values, complete=False):
	doc = frappe.get_doc("IT Facilities Provisioning Request", name)
	doc.check_permission("write")
	if doc.status == "Completed":
		frappe.throw(_("This request is already completed."))
	values = frappe.parse_json(values) or {}
	for field in TICKS:
		if field in values:
			doc.set(field, 1 if values.get(field) else 0)
	for field in ("official_email", "remarks"):
		if field in values:
			doc.set(field, (values.get(field) or "").strip() or None)
	if complete in (True, 1, "1", "true", "True"):
		doc.complete()
	else:
		doc.save()
	return frappe.get_list(
		"IT Facilities Provisioning Request", filters={"name": name}, fields=FIELDS, limit_page_length=1
	)[0]
