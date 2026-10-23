# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""A new joiner's onboarding documents (folder 11: the documents to bring
on the day of joining), uploaded on the candidate portal and verified by
staff in Documents > Onboarding Verification.

The checklist is built once, from Document Type Master rows marked Used In
Onboarding/Both (all tracks, or this application's track), so HR changes
the list from Master Setup without code. Each row carries the master's
requirement; the collection is Complete when every Mandatory row is
Verified.
"""

import os

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime

UPLOADABLE = ("Requested", "Submitted", "Resubmission Requested")


class DocumentCollection(Document):
	def validate(self):
		self.set_details()
		self.populate_checklist()
		self.compute_overall_status()

	def set_details(self):
		app = frappe.db.get_value("Application", self.application, ["candidate", "job_opening"], as_dict=True)
		if app:
			self.candidate_name = frappe.db.get_value("Candidate", app.candidate, "full_name")
			self.job_opening = app.job_opening

	def populate_checklist(self):
		if self.checklist:
			return
		for dt in onboarding_document_types(self.application):
			self.append(
				"checklist",
				{"document_type": dt.name, "requirement": dt.requirement or "Mandatory", "status": "Requested"},
			)

	def compute_overall_status(self):
		rows = self.checklist or []
		if not rows:
			self.overall_status = "Pending"
			return
		mandatory = [r for r in rows if (r.requirement or "Mandatory") == "Mandatory"]
		if mandatory and all(r.status == "Verified" for r in mandatory):
			self.overall_status = "Complete"
		elif any(r.status == "Resubmission Requested" for r in rows):
			self.overall_status = "Resubmission Requested"
		elif mandatory and all(r.status in ("Submitted", "Under Verification", "Verified") for r in mandatory):
			self.overall_status = "Under Verification"
		elif any(r.status in ("Submitted", "Under Verification", "Verified") for r in rows):
			self.overall_status = "Partially Submitted"
		else:
			self.overall_status = "Pending"

	def on_update(self):
		if self.overall_status != "Complete" or not self.application:
			return
		from pathways.utils.onboarding import ensure_employee, set_application_status

		# Never step a joined application back to "Documents Verified".
		if frappe.db.get_value("Application", self.application, "status") != "Joined":
			set_application_status(self.application, "Documents Verified")
		joining = frappe.db.get_value("Joining", {"application": self.application, "status": "Joined"}, "name")
		if joining:
			ensure_employee(frappe.get_doc("Joining", joining))


def onboarding_document_types(application):
	track = None
	if application:
		job_opening = frappe.db.get_value("Application", application, "job_opening")
		if job_opening:
			track = frappe.db.get_value("Job Opening", job_opening, "track")
	doc_types = frappe.get_all(
		"Document Type Master",
		filters={"used_in": ["in", ["Onboarding", "Both"]], "is_active": 1},
		fields=["name", "track", "requirement"],
		order_by="creation asc",
	)
	return [dt for dt in doc_types if not dt.track or dt.track == track]


def _row(doc, document_type):
	row = next((r for r in doc.checklist if r.document_type == document_type), None)
	if not row:
		frappe.throw(_("This document type is not part of the checklist for this application."))
	return row


def _check_upload(file_url, document_type):
	"""The file must be the uploader's own fresh private upload, in a format
	and size the Document Type allows — never someone else's file."""
	file = frappe.db.get_value(
		"File",
		{"file_url": file_url, "owner": frappe.session.user},
		["name", "file_size", "is_private", "attached_to_doctype", "attached_to_name"],
		as_dict=True,
	)
	if not file:
		frappe.throw(_("The uploaded file was not found. Please upload it again."))
	if file.attached_to_doctype and file.attached_to_doctype != "Document Collection":
		frappe.throw(_("This file is already used elsewhere. Please upload it again."))
	rule = frappe.db.get_value("Document Type Master", document_type, ["max_file_size_mb", "allowed_formats"], as_dict=True) or {}
	formats = [f.strip().lower().lstrip(".") for f in (rule.get("allowed_formats") or "").split(",") if f.strip()]
	extension = os.path.splitext(file_url)[1].lower().lstrip(".")
	if formats and extension not in formats:
		frappe.throw(_("{0}: allowed formats are {1}.").format(document_type, ", ".join(f.upper() for f in formats)))
	max_mb = flt(rule.get("max_file_size_mb"))
	if max_mb and cint(file.file_size) > max_mb * 1024 * 1024:
		frappe.throw(_("{0}: the file is larger than {1} MB.").format(document_type, max_mb))
	return file


@frappe.whitelist()
def upload_document(document_collection_name, document_type, attachment):
	"""Candidate-facing document upload (portal: Joining documents).

	check_permission restricts this to the owning candidate or privileged
	staff (has_document_collection_permission, wired via hooks.py) —
	frappe.get_doc() does not enforce this on its own.
	"""
	doc = frappe.get_doc("Document Collection", document_collection_name)
	doc.check_permission("write")
	row = _row(doc, document_type)
	if row.status not in UPLOADABLE:
		frappe.throw(_("{0} has already been verified and cannot be replaced.").format(document_type))
	file = _check_upload(attachment, document_type)

	row.attachment = attachment
	row.status = "Submitted"
	row.submitted_on = now_datetime()
	# The last rejection reason stays on the row, so the verifier sees
	# what the candidate was asked to correct.
	doc.save(ignore_permissions=True)
	# Attached to the collection, so staff who can open it can open the
	# private file; nobody else can.
	frappe.db.set_value(
		"File",
		file.name,
		{"attached_to_doctype": "Document Collection", "attached_to_name": doc.name},
		update_modified=False,
	)
	return doc.overall_status


@frappe.whitelist()
def verify_document(document_collection_name, document_type, verified=True, rejection_reason=None):
	"""Staff-facing verification action.

	This function carries its own @frappe.whitelist(), so it's reachable
	directly (not just through api.documents.verify_document) — the role
	check must live here, not only in that thin wrapper, or it can be
	bypassed by calling this path instead. check_permission("write")
	alone isn't enough either: a Candidate has write on their OWN
	Document Collection (to submit documents) but must never be able to
	verify them.
	"""
	from pathways.permissions import has_duty

	if not has_duty("document_verifier_roles"):
		frappe.throw("You are not authorised to verify documents.", frappe.PermissionError)

	doc = frappe.get_doc("Document Collection", document_collection_name)
	row = _row(doc, document_type)
	verified = verified in (True, "true", "True", "1", 1)

	if verified:
		if not row.attachment:
			frappe.throw(_("{0} has not been uploaded yet.").format(document_type))
		row.status = "Verified"
		row.verified_by = frappe.session.user
		row.verified_on = now_datetime()
		row.rejection_reason = None
	else:
		if not (rejection_reason or "").strip():
			frappe.throw(_("Please give the reason, so the candidate knows what to correct."))
		row.status = "Resubmission Requested"
		row.rejection_reason = rejection_reason.strip()
		row.verified_by = None
		row.verified_on = None

	doc.save(ignore_permissions=True)
	if not verified:
		from pathways.utils.onboarding import send_resubmission_email

		send_resubmission_email(doc, row)
	return doc.overall_status
