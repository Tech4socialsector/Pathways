# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Onboarding documents: the candidate's checklist on the portal and the
staff verification screen (Documents > Onboarding Verification).

Reading is Role Permissions plus the row-level rules in
pathways.permissions (a candidate sees only their own collection);
verifying is the Pathways Settings "Document Verifier Roles" duty.
"""

import os

import frappe

from pathways.permissions import has_duty, has_full_access
from pathways.pathways.doctype.document_collection.document_collection import (
	upload_document as _upload_document,
	verify_document as _verify_document,
)

IMAGE_EXTENSIONS = ("jpg", "jpeg", "png", "gif", "webp")


def _file_info(file_url):
	if not file_url:
		return {}
	extension = os.path.splitext(file_url)[1].lower().lstrip(".")
	kind = "pdf" if extension == "pdf" else "image" if extension in IMAGE_EXTENSIONS else "other"
	return {"file_url": file_url, "file_name": file_url.rsplit("/", 1)[-1], "kind": kind}


def _checklist(doc):
	rules = {
		r.name: r
		for r in frappe.get_all(
			"Document Type Master",
			filters={"name": ["in", [row.document_type for row in doc.checklist] or [""]]},
			fields=["name", "max_file_size_mb", "allowed_formats"],
		)
	}
	out = []
	for row in doc.checklist:
		rule = rules.get(row.document_type) or {}
		out.append(
			{
				"document_type": row.document_type,
				"requirement": row.requirement or "Mandatory",
				"status": row.status,
				"attachment": row.attachment,
				"submitted_on": row.submitted_on,
				"rejection_reason": row.rejection_reason,
				"verified_by": frappe.utils.get_fullname(row.verified_by) if row.verified_by else None,
				"verified_on": row.verified_on,
				"max_size_mb": rule.get("max_file_size_mb") or 5,
				"formats": [
					f.strip().lower().lstrip(".") for f in (rule.get("allowed_formats") or "").split(",") if f.strip()
				]
				or ["pdf", "jpg", "jpeg", "png"],
				**_file_info(row.attachment),
			}
		)
	return out


def _summary(rows):
	return {
		"total": len(rows),
		"mandatory": sum(1 for r in rows if r["requirement"] == "Mandatory"),
		"submitted": sum(1 for r in rows if r["status"] in ("Submitted", "Under Verification")),
		"verified": sum(1 for r in rows if r["status"] == "Verified"),
		"resubmission": sum(1 for r in rows if r["status"] == "Resubmission Requested"),
		"requested": sum(1 for r in rows if r["status"] == "Requested"),
	}


@frappe.whitelist()
def get_my_document_checklist(application_name):
	app = frappe.get_doc("Application", application_name)
	app.check_permission("read")
	candidate_email = frappe.db.get_value("Candidate", app.candidate, "email")
	if frappe.session.user != candidate_email and not has_full_access("Document Collection"):
		frappe.throw("You are not authorised to view this document checklist.", frappe.PermissionError)

	doc_collection_name = frappe.db.get_value(
		"Document Collection", {"application": application_name}, "name"
	)
	if not doc_collection_name:
		return {"overall_status": "Pending", "checklist": []}

	doc = frappe.get_doc("Document Collection", doc_collection_name)
	rows = _checklist(doc)
	joining = frappe.db.get_value(
		"Joining",
		{"application": application_name},
		["status", "confirmed_doj", "reporting_location", "reporting_time"],
		as_dict=True,
	)
	return {
		"name": doc.name,
		"overall_status": doc.overall_status,
		"checklist": rows,
		"summary": _summary(rows),
		"joining": joining,
	}


@frappe.whitelist()
def upload_document(document_collection_name, document_type, attachment):
	return _upload_document(document_collection_name, document_type, attachment)


@frappe.whitelist()
def verify_document(document_collection_name, document_type, verified=True, rejection_reason=None):
	return _verify_document(document_collection_name, document_type, verified, rejection_reason)


# ----------------------------------------------------------- staff screen


@frappe.whitelist()
def list_onboarding_collections():
	"""Rows for Documents > Onboarding Verification (permission-scoped)."""
	collections = frappe.get_list(
		"Document Collection",
		fields=["name", "application", "candidate_name", "job_opening", "overall_status", "onboarding_email_sent_on", "modified"],
		order_by="modified desc",
		limit_page_length=0,
	)
	if not collections:
		return []
	names = [c.name for c in collections]
	counts = {}
	for row in frappe.get_all(
		"Document Collection Row",
		filters={"parent": ["in", names], "parenttype": "Document Collection"},
		fields=["parent", "status", "requirement"],
	):
		c = counts.setdefault(row.parent, {"total": 0, "verified": 0, "submitted": 0, "resubmission": 0})
		c["total"] += 1
		if row.status == "Verified":
			c["verified"] += 1
		elif row.status in ("Submitted", "Under Verification"):
			c["submitted"] += 1
		elif row.status == "Resubmission Requested":
			c["resubmission"] += 1
	apps = {a.name: a for a in frappe.get_all("Application", filters={"name": ["in", [c.application for c in collections]]}, fields=["name", "application_id"])}
	jobs = {j.name: j.job_title for j in frappe.get_all("Job Opening", filters={"name": ["in", list({c.job_opening for c in collections if c.job_opening})] or [""]}, fields=["name", "job_title"])}
	joinings = {
		j.application: j
		for j in frappe.get_all(
			"Joining", filters={"application": ["in", [c.application for c in collections]]}, fields=["application", "confirmed_doj", "status"]
		)
	}
	out = []
	for c in collections:
		count = counts.get(c.name, {"total": 0, "verified": 0, "submitted": 0, "resubmission": 0})
		joining = joinings.get(c.application) or {}
		out.append(
			{
				**c,
				**count,
				"application_id": (apps.get(c.application) or {}).get("application_id") or c.application,
				"job_title": jobs.get(c.job_opening) or "",
				"progress": f"{count['verified']}/{count['total']} verified",
				"joining_date": joining.get("confirmed_doj"),
				"joining_status": joining.get("status"),
			}
		)
	return out


@frappe.whitelist()
def get_collection(name):
	doc = frappe.get_doc("Document Collection", name)
	doc.check_permission("read")
	rows = _checklist(doc)
	app = frappe.db.get_value("Application", doc.application, ["application_id", "candidate"], as_dict=True) or {}
	return {
		"name": doc.name,
		"application": doc.application,
		"application_id": app.get("application_id"),
		"candidate_name": doc.candidate_name,
		"candidate_email": frappe.db.get_value("Candidate", app.get("candidate"), "email") if app else None,
		"job_title": frappe.db.get_value("Job Opening", doc.job_opening, "job_title") if doc.job_opening else "",
		"overall_status": doc.overall_status,
		"onboarding_email_sent_on": doc.onboarding_email_sent_on,
		"checklist": rows,
		"summary": _summary(rows),
		"can_verify": has_duty("document_verifier_roles"),
	}
