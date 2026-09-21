# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe

from pathways.pathways.doctype.document_collection.document_collection import (
	upload_document as _upload_document,
	verify_document as _verify_document,
)


@frappe.whitelist()
def get_my_document_checklist(application_name):
	app = frappe.get_doc("Application", application_name)  # permission-checked
	candidate_email = frappe.db.get_value("Candidate", app.candidate, "email")
	if frappe.session.user != candidate_email and "Pathways Admin" not in frappe.get_roles():
		frappe.throw("You are not authorised to view this document checklist.")

	doc_collection_name = frappe.db.get_value(
		"Document Collection", {"application": application_name}, "name"
	)
	if not doc_collection_name:
		return {"overall_status": "Pending", "checklist": []}

	doc = frappe.get_doc("Document Collection", doc_collection_name)
	return {
		"name": doc.name,
		"overall_status": doc.overall_status,
		"checklist": [
			{
				"document_type": row.document_type,
				"requirement": row.requirement,
				"status": row.status,
				"attachment": row.attachment,
				"rejection_reason": row.rejection_reason,
			}
			for row in doc.checklist
		],
	}


@frappe.whitelist()
def upload_document(document_collection_name, document_type, attachment):
	return _upload_document(document_collection_name, document_type, attachment)


@frappe.whitelist()
def verify_document(document_collection_name, document_type, verified=True, rejection_reason=None):
	if "Pathways Admin" not in frappe.get_roles() and "Pathways PNCO" not in frappe.get_roles():
		frappe.throw("You are not authorised to verify documents.")
	return _verify_document(document_collection_name, document_type, verified, rejection_reason)
