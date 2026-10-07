# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Pre-Recruitment Green Sheet actions for the staff Job Opening page.

Lets recruiters raise, submit, withdraw and revise a job's Green Sheet
from /pathways/jobs/<id> instead of the Desk. Approving/returning still
goes through pathways.api.approval.record_approval_action. Permission
checks are left to Frappe (insert/save/submit/cancel/delete all enforce
the doctype's Role Permissions on their own).
"""

import frappe

from pathways.api.approval import get_approval_chain_status
from pathways.pathways.doctype.job_opening.job_opening import can_override_status
from pathways.utils.approval import check_can_act, find_template, reset_for_amendment

DOCTYPE = "Pre-Recruitment Green Sheet"
# Sheets that block raising another one for the same job.
ACTIVE_STATUSES = ("Under Approval", "Approved", "Returned for Revision")


def _get_sheet(name):
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("read")
	return doc


def _find_open_sheet(job_opening):
	"""The job's draft or in-flight sheet, if any (ignores cancelled ones)."""
	draft = frappe.db.get_value(DOCTYPE, {"job_opening": job_opening, "docstatus": 0}, "name")
	if draft:
		return draft
	return frappe.db.get_value(
		DOCTYPE,
		{"job_opening": job_opening, "docstatus": 1, "status": ("in", ACTIVE_STATUSES)},
		"name",
	)


@frappe.whitelist()
def get_job_green_sheets(job_opening):
	"""All Green Sheets raised for a job (newest first), the approval chain
	of the current one, and what the session user may do with them.
	"""
	job = frappe.get_doc("Job Opening", job_opening)
	job.check_permission("read")

	sheets = frappe.get_list(
		DOCTYPE,
		filters={"job_opening": job_opening},
		fields=[
			"name",
			"status",
			"docstatus",
			"track",
			"approval_chain_template",
			"current_approval_level",
			"justification_note",
			"duration_of_ad_days",
			"jd_attachment",
			"supporting_attachment",
			"signed_copy_attachment",
			"amended_from",
			"owner",
			"creation",
		],
		order_by="creation desc",
	)
	for sheet in sheets:
		if sheet.docstatus == 2:
			sheet.status = "Cancelled"

	current = next((s for s in sheets if s.docstatus != 2), None)
	chain = None
	can_act = False
	act_blocked_reason = None
	if current and current.docstatus == 1:
		chain = get_approval_chain_status(DOCTYPE, current.name)
		if current.status == "Under Approval":
			can_act, _is_override, act_blocked_reason = check_can_act(frappe.get_doc(DOCTYPE, current.name))

	return {
		"sheets": sheets,
		"current": current,
		"chain": chain,
		"has_chain_template": bool(find_template(job.track, DOCTYPE, job.employment_type)),
		"act_blocked_reason": act_blocked_reason,
		"permissions": {
			"can_create": frappe.has_permission(DOCTYPE, "create"),
			"can_submit": frappe.has_permission(DOCTYPE, "submit"),
			"can_cancel": frappe.has_permission(DOCTYPE, "cancel"),
			"can_act": can_act,
			"can_override_status": can_override_status(),
		},
	}


@frappe.whitelist()
def save_green_sheet(
	job_opening, justification_note, duration_of_ad_days=None, name=None, submit=0, jd_attachment=None, supporting_attachment=None
):
	"""Create the job's Green Sheet, or update its draft, and optionally
	submit it for approval in the same call.
	"""
	job = frappe.get_doc("Job Opening", job_opening)
	job.check_permission("read")
	if not job.track:
		frappe.throw("Set a Recruitment Track on the Job Opening first.")

	if name:
		doc = _get_sheet(name)
		if doc.job_opening != job_opening:
			frappe.throw("This Green Sheet belongs to a different Job Opening.")
		if doc.docstatus != 0:
			frappe.throw("Only a draft Green Sheet can be edited.")
	else:
		existing = _find_open_sheet(job_opening)
		if existing:
			frappe.throw(f"This Job Opening already has an open Green Sheet ({existing}).")
		doc = frappe.new_doc(DOCTYPE)
		doc.job_opening = job_opening

	doc.justification_note = justification_note
	doc.duration_of_ad_days = frappe.utils.cint(duration_of_ad_days) or None
	doc.jd_attachment = jd_attachment or None
	doc.supporting_attachment = supporting_attachment or None
	doc.save()

	if frappe.utils.cint(submit):
		doc.submit()

	return doc.name


@frappe.whitelist()
def submit_green_sheet(name):
	doc = _get_sheet(name)
	if doc.docstatus != 0:
		frappe.throw("This Green Sheet has already been submitted.")
	doc.submit()
	return doc.name


@frappe.whitelist()
def withdraw_green_sheet(name):
	"""Cancel a sheet that is still Under Approval (or was returned), which
	moves its job back to Draft.
	"""
	doc = _get_sheet(name)
	if doc.docstatus != 1 or doc.status not in ("Under Approval", "Returned for Revision"):
		frappe.throw("Only a Green Sheet that is under approval or returned can be withdrawn.")
	doc.cancel()
	return doc.name


@frappe.whitelist()
def revise_green_sheet(name):
	"""Cancel a sheet that was Returned for Revision and open an amended
	draft carrying the same content, ready to be edited and resubmitted.
	"""
	doc = _get_sheet(name)
	if doc.docstatus != 1 or doc.status != "Returned for Revision":
		frappe.throw("Only a Green Sheet that was returned for revision can be revised.")
	doc.cancel()

	amended = frappe.copy_doc(doc)
	amended.amended_from = doc.name
	reset_for_amendment(amended)
	amended.insert()
	return amended.name


@frappe.whitelist()
def delete_green_sheet_draft(name):
	doc = _get_sheet(name)
	if doc.docstatus != 0:
		frappe.throw("Only a draft Green Sheet can be deleted.")
	# Whoever may raise Green Sheets may discard an unsubmitted draft;
	# Pathways Recruiter has create but not the (general) delete right.
	if not frappe.has_permission(DOCTYPE, "create"):
		raise frappe.PermissionError
	frappe.delete_doc(DOCTYPE, name, ignore_permissions=True)
	return name


@frappe.whitelist(methods=["POST"])
def attach_signed_green_sheet(name, file_url=None):
	"""Workflow step 25: keep the physically signed copy with the approved
	sheet (allowed after submission; empty file_url removes it)."""
	doc = _get_sheet(name)
	if doc.docstatus != 1:
		frappe.throw("Upload the signed copy after the Green Sheet has been submitted.")
	if not frappe.has_permission(DOCTYPE, "create") and not can_override_status():
		frappe.throw("You cannot upload the signed Green Sheet.", frappe.PermissionError)
	doc.db_set("signed_copy_attachment", file_url or None)
	doc.add_comment("Info", "Signed copy uploaded." if file_url else "Signed copy removed.")
	return doc.signed_copy_attachment
