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

from collections import Counter

import frappe

from pathways.pathways.doctype.job_opening.job_opening import can_override_status


@frappe.whitelist()
def get_job_opening(job_opening):
	"""Full detail for one Job Opening, for staff — any status, not just
	Advertised.

	frappe.get_doc() does NOT check permissions on read by default (that
	requires an explicit check_permission call) — without the line
	below, any logged-in user, including a Candidate with zero role
	grant on this doctype, could read Draft/internal Job Openings.
	"""
	doc = frappe.get_doc("Job Opening", job_opening)
	doc.check_permission("read")
	detail = doc.as_dict()

	# Summary only: counts are shown to anyone who can read the job; the
	# applications themselves stay behind Application permissions.
	statuses = frappe.get_all(
		"Application", filters={"job_opening": doc.name}, pluck="status", ignore_permissions=True
	)
	detail["application_counts"] = dict(Counter(statuses))
	from pathways.api.scoring import shortlisting_summary

	detail["shortlisting"] = shortlisting_summary(doc)
	detail["position_detail"] = (
		frappe.db.get_value(
			"Position", doc.position, ["job_code", "position_title", "reports_to", "hiring_manager_role"], as_dict=True
		)
		if doc.position
		else None
	)
	return detail


@frappe.whitelist()
def list_job_openings(filters=None, limit_start=0, limit_page_length=20):
	"""Internal Job Openings list — all statuses, scoped only by the
	caller's real Role Permissions (frappe.get_all applies these
	automatically). filters may narrow by status/track/department.
	"""
	if isinstance(filters, str):
		filters = frappe.parse_json(filters)
	filters = filters or {}

	# get_list, not get_all: a tagged colleague sees only the jobs shared
	# with them (pathways.permissions). Without read on Job Opening (e.g. a
	# committee member searching from the top bar) the list is just empty.
	if not frappe.has_permission("Job Opening", "read"):
		return []
	jobs = frappe.get_list(
		"Job Opening",
		filters=filters,
		fields=[
			"name",
			"position",
			"application_start",
			"shortlisting_ratio",
			"creation",
			"job_title",
			"track",
			"department",
			"designation",
			"employment_type",
			"vacancies",
			"tenure_description",
			"pay_level",
			"status",
			"application_deadline",
			"modified",
		],
		order_by="creation desc",
		limit_start=frappe.utils.cint(limit_start),
		limit_page_length=frappe.utils.cint(limit_page_length),
	)
	# Optional list columns (Columns menu): applications and committee.
	names = [j.name for j in jobs]
	if names:
		counts = dict(
			frappe.db.sql(
				"select job_opening, count(*) from `tabApplication` where job_opening in %s and status != 'Withdrawn' group by job_opening",
				(names,),
			)
		)
		committees = set(frappe.get_all("Shortlisting Committee", filters={"job_opening": ["in", names]}, pluck="job_opening"))
		for j in jobs:
			j.applications = counts.get(j.name, 0)
			j.has_committee = "Yes" if j.name in committees else "No"
	return jobs


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
		# System Managers may set any status without Green Sheet approval
		# (see JobOpening.validate_status_transition).
		"can_override_status": can_override_status(),
	}


@frappe.whitelist(methods=["POST"])
def bulk_set_job_status(names, status):
	"""Change Status for several Job Openings; each keeps its own rules
	(e.g. Advertised needs an approved Green Sheet and a deadline)."""
	from pathways.utils.bulk import run_bulk

	return run_bulk(names, lambda name: update_job_opening(name, {"status": status}))


@frappe.whitelist(methods=["POST"])
def bulk_delete_job_openings(names):
	from pathways.utils.bulk import run_bulk

	return run_bulk(names, lambda name: frappe.delete_doc("Job Opening", name))


# ----------------------------------------------- folder and "Shared with"
# Workflow step 7: the job's department folder, and colleagues tagged on the
# job (they get read access to its applications and documents).


@frappe.whitelist()
def get_job_sharing(job_opening):
	doc = frappe.get_doc("Job Opening", job_opening)
	doc.check_permission("read")
	can_edit = bool(doc.has_permission("write"))
	return {
		"files_folder": doc.files_folder,
		"folder_link": f"/app/file/view/{doc.files_folder}" if doc.files_folder else None,
		"shared_with": [
			{
				"user": row.user,
				"full_name": row.full_name or frappe.utils.get_fullname(row.user),
				"access_note": row.access_note,
				"tagged_by": frappe.utils.get_fullname(row.tagged_by) if row.tagged_by else None,
				"tagged_on": row.tagged_on,
			}
			for row in doc.shared_with
		],
		"can_edit": can_edit,
		"users": frappe.get_all(
			"User",
			filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Guest", "Administrator"]]},
			fields=["name", "full_name"],
			order_by="full_name asc",
		)
		if can_edit
		else [],
	}


@frappe.whitelist(methods=["POST"])
def set_job_colleagues(job_opening, colleagues):
	"""Replace the job's "Shared with" list: [{user, access_note}]. save()
	enforces write permission; JobOpening.sync_shared_with grants access and
	emails the newly tagged."""
	if isinstance(colleagues, str):
		colleagues = frappe.parse_json(colleagues)
	doc = frappe.get_doc("Job Opening", job_opening)
	existing = {row.user: row for row in doc.shared_with}
	rows = []
	for c in colleagues or []:
		user = (c.get("user") or "").strip()
		if not user:
			continue
		# Any colleague with a login, but never a candidate: the Tagged
		# Colleague role gives desk access, which would make them staff.
		from pathways.permissions import CANDIDATE_ROLE

		if not frappe.db.exists("User", {"name": user, "enabled": 1}) or CANDIDATE_ROLE in frappe.get_roles(user):
			frappe.throw(frappe._("{0} is not a staff user.").format(user))
		old = existing.get(user)
		rows.append(
			{
				"user": user,
				"access_note": (c.get("access_note") or "").strip() or None,
				"tagged_by": old.tagged_by if old else None,
				"tagged_on": old.tagged_on if old else None,
			}
		)
	doc.set("shared_with", rows)
	doc.save()
	return get_job_sharing(job_opening)


@frappe.whitelist(methods=["POST"])
def ensure_job_folder(job_opening):
	"""Create (or find) the job's folder now, e.g. for jobs created before
	folders existed."""
	doc = frappe.get_doc("Job Opening", job_opening)
	doc.check_permission("write")
	from pathways.utils.folders import ensure_job_folder as _ensure

	_ensure(doc)
	return get_job_sharing(job_opening)
