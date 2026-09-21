# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Staff-facing Job Opening CRUD — backs the internal /jobs pages.

Unlike pathways.api.application.get_open_job_openings/get_job_opening_detail
(guest-facing, hardcoded to status=Advertised for the public job board),
these functions serve the internal recruiter/admin UI: no status filter,
no allow_guest, and no manual role re-checks. Job Opening's Role
Permissions (see job_opening.json) are the single source of truth —
frappe.get_doc/get_all/new_doc/delete_doc already enforce them, so
duplicating that logic here would only risk drifting out of sync.
"""

import frappe


@frappe.whitelist()
def get_job_opening(job_opening):
	"""Full detail for one Job Opening, for staff — any status, not just
	Advertised. frappe.get_doc runs the standard read permission check.
	"""
	doc = frappe.get_doc("Job Opening", job_opening)
	return doc.as_dict()


@frappe.whitelist()
def list_job_openings(filters=None, limit_start=0, limit_page_length=20):
	"""Internal Job Openings list — all statuses, scoped only by the
	caller's real Role Permissions (frappe.get_all applies these
	automatically). filters may narrow by status/track/department.
	"""
	if isinstance(filters, str):
		filters = frappe.parse_json(filters)
	filters = filters or {}

	return frappe.get_all(
		"Job Opening",
		filters=filters,
		fields=[
			"name",
			"job_title",
			"track",
			"department",
			"designation",
			"employment_type",
			"vacancies",
			"tenure_description",
			"pay_level",
			"status",
			"modified",
		],
		order_by="creation desc",
		limit_start=frappe.utils.cint(limit_start),
		limit_page_length=frappe.utils.cint(limit_page_length),
	)


@frappe.whitelist()
def create_job_opening(data):
	"""Creates a Job Opening. Field validation (required fields, Select
	options, Link integrity) and the create permission check are both
	handled declaratively by Frappe from the doctype JSON on insert.
	"""
	if isinstance(data, str):
		data = frappe.parse_json(data)

	doc = frappe.new_doc("Job Opening")
	doc.update(data)
	doc.insert()
	return doc.as_dict()


@frappe.whitelist()
def update_job_opening(job_opening, data):
	"""Updates a Job Opening. get_doc/save enforce read+write permission;
	no manual role check needed.
	"""
	if isinstance(data, str):
		data = frappe.parse_json(data)

	doc = frappe.get_doc("Job Opening", job_opening)
	doc.update(data)
	doc.save()
	return doc.as_dict()


@frappe.whitelist()
def delete_job_opening(job_opening):
	"""Deletes a Job Opening. delete_doc enforces delete permission on
	its own — Pathways Recruiter lacks delete on this doctype and will
	naturally get a PermissionError here without any extra check.
	"""
	frappe.delete_doc("Job Opening", job_opening)
	return {"deleted": job_opening}


@frappe.whitelist()
def get_job_opening_permissions(job_opening):
	"""Lets the frontend decide whether to show Edit/Delete buttons,
	without duplicating the permission logic itself — just reports what
	Frappe's own has_permission already says for this user and doc.
	"""
	return {
		"can_write": frappe.has_permission("Job Opening", "write", doc=job_opening),
		"can_delete": frappe.has_permission("Job Opening", "delete", doc=job_opening),
	}
