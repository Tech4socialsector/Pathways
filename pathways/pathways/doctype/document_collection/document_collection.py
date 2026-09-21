# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class DocumentCollection(Document):
	def validate(self):
		self.populate_checklist()
		self.compute_overall_status()

	def populate_checklist(self):
		if self.checklist:
			return

		track = None
		if self.application:
			job_opening = frappe.db.get_value("Application", self.application, "job_opening")
			if job_opening:
				track = frappe.db.get_value("Job Opening", job_opening, "track")

		filters = {"used_in": ["in", ["Onboarding", "Both"]], "is_active": 1}
		doc_types = frappe.get_all(
			"Document Type Master", filters=filters, fields=["name", "track"]
		)
		for dt in doc_types:
			if dt.track and dt.track != track:
				continue
			self.append("checklist", {"document_type": dt.name, "status": "Requested"})

	def compute_overall_status(self):
		if not self.checklist:
			self.overall_status = "Pending"
			return

		mandatory_rows = [row for row in self.checklist if row.requirement == "Mandatory"]
		all_rows = self.checklist

		if all(row.status == "Verified" for row in mandatory_rows) and mandatory_rows:
			self.overall_status = "Complete"
		elif any(row.status == "Under Verification" for row in all_rows):
			self.overall_status = "Under Verification"
		elif any(row.status in ("Submitted", "Verified") for row in all_rows):
			self.overall_status = "Partially Submitted"
		else:
			self.overall_status = "Pending"

	def on_update(self):
		if self.overall_status == "Complete" and self.application:
			frappe.db.set_value("Application", self.application, "status", "Documents Verified")


@frappe.whitelist()
def upload_document(document_collection_name, document_type, attachment):
	"""Candidate-facing document upload, backing the Document Submission web form."""
	doc = frappe.get_doc("Document Collection", document_collection_name)
	row = next((r for r in doc.checklist if r.document_type == document_type), None)
	if not row:
		frappe.throw("This document type is not part of the checklist for this application.")

	row.attachment = attachment
	row.status = "Submitted"
	row.db_update()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return doc.overall_status


@frappe.whitelist()
def verify_document(document_collection_name, document_type, verified=True, rejection_reason=None):
	"""Staff-facing verification action."""
	doc = frappe.get_doc("Document Collection", document_collection_name)
	row = next((r for r in doc.checklist if r.document_type == document_type), None)
	if not row:
		frappe.throw("This document type is not part of the checklist for this application.")

	if verified in (True, "true", "1", 1):
		row.status = "Verified"
		row.verified_by = frappe.session.user
		row.verified_on = now_datetime()
	else:
		row.status = "Resubmission Requested"
		row.rejection_reason = rejection_reason

	row.db_update()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return doc.overall_status
