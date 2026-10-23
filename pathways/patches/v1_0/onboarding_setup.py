# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Onboarding and joining (workflow steps 31, 34, folder 12).

- Email templates staff have not edited pick up the portal upload link
  (onboarding), the "details changed" note (IT intimation) and the portal
  link (document resubmission); the new events are created.
- Joining-day defaults in Pathways Settings.
- Existing checklists get each row's requirement from the Document Type
  master (it was never copied, so no collection could become Complete),
  and existing joinings get a status.
Idempotent."""

import frappe

REFRESH = ("Onboarding Documents", "IT & Facilities Intimation", "Document Resubmission Request")


def execute():
	from pathways.utils.email_events import TEMPLATES, ensure_email_events

	for name in REFRESH:
		row = frappe.db.get_value("Email Template", name, ["creation", "modified"], as_dict=True)
		if row and (row.modified - row.creation).total_seconds() <= 5:
			subject, response = TEMPLATES[name]
			frappe.db.set_value(
				"Email Template",
				name,
				{"subject": subject, "response": response, "response_html": response, "use_html": 1},
				update_modified=False,
			)
	ensure_email_events()

	settings = frappe.get_single("Pathways Settings")
	if not settings.get("default_reporting_location"):
		frappe.db.set_single_value("Pathways Settings", "default_reporting_location", "Ground Floor, Training Centre Room No. 004")
	if not settings.get("default_reporting_time"):
		frappe.db.set_single_value("Pathways Settings", "default_reporting_time", "10:00:00")

	for row in frappe.get_all(
		"Document Collection Row",
		filters={"parenttype": "Document Collection", "requirement": ["in", ["", None]]},
		fields=["name", "document_type"],
	):
		requirement = frappe.db.get_value("Document Type Master", row.document_type, "requirement") or "Mandatory"
		frappe.db.set_value("Document Collection Row", row.name, "requirement", requirement, update_modified=False)

	frappe.db.sql("update `tabJoining` set status='Draft' where ifnull(status, '')=''")
