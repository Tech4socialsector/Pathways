# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Candidates menu: every person who has applied, with all their
applications.

One Candidate per email address. An application is linked to the
candidate whose email it was submitted with (the email is trimmed and
lower-cased first); a second application with the same email, to another
job, is added to the same candidate. The same email cannot apply twice to
the same job (unless the first was withdrawn). Imports follow the same
rule and never overwrite an existing profile."""

import frappe
from frappe import _

from pathways.permissions import has_full_access

STAGE_ORDER = (
	"Submitted", "Under Review", "Shortlisted", "Interview Scheduled", "Interview Completed", "Selected",
	"Offer Extended", "Offer Accepted", "Offer Declined", "Documents Pending", "Documents Verified", "Joined",
	"Not Selected", "Withdrawn",
)


def _require_access():
	if not has_full_access("Candidate"):
		frappe.throw(_("Not permitted."), frappe.PermissionError)


@frappe.whitelist()
def list_candidates():
	_require_access()
	rows = frappe.get_list(
		"Candidate",
		fields=["name", "full_name", "email", "mobile_number", "gender", "category", "date_of_birth", "creation"],
		order_by="creation desc",
		limit_page_length=0,
	)
	apps = frappe.get_all(
		"Application",
		filters={"candidate": ["in", [r.name for r in rows] or [""]]},
		fields=["candidate", "status", "application_date", "creation", "job_opening.job_title as job_title", "track"],
		order_by="creation desc",
	)
	by_candidate = {}
	for a in apps:
		by_candidate.setdefault(a.candidate, []).append(a)
	accounts = set(frappe.get_all("User", filters={"name": ["in", [r.email for r in rows if r.email] or [""]]}, pluck="name"))
	mobiles = {}
	for r in rows:
		if r.mobile_number:
			mobiles.setdefault(r.mobile_number.strip(), []).append(r.name)
	for r in rows:
		mine = by_candidate.get(r.name, [])
		latest = mine[0] if mine else None
		r.applications = len(mine)
		r.latest_job = latest.job_title if latest else ""
		r.latest_status = latest.status if latest else ""
		r.tracks = ", ".join(sorted({a.track for a in mine if a.track}))
		r.active = sum(1 for a in mine if a.status not in ("Not Selected", "Withdrawn", "Joined", "Offer Declined"))
		r.portal_account = "Yes" if r.email in accounts else "No"
		r.same_mobile = len(mobiles.get((r.mobile_number or "").strip(), [])) > 1
	return rows


@frappe.whitelist()
def get_candidate(name):
	_require_access()
	c = frappe.get_doc("Candidate", name)
	c.check_permission("read")
	apps = frappe.get_all(
		"Application",
		filters={"candidate": c.name},
		fields=[
			"name", "application_id", "status", "eligibility_status", "selection_outcome", "application_date", "track", "source",
			"job_opening", "job_opening.job_title as job_title", "job_opening.position as position",
		],
		order_by="creation desc",
	)
	interviews = frappe.get_all(
		"Interview",
		filters={"application": ["in", [a.name for a in apps] or [""]], "status": ["!=", "Cancelled"]},
		fields=["application", "round_type", "status", "scheduled_datetime"],
		order_by="scheduled_datetime asc",
	)
	for a in apps:
		a.interviews = [
			{"round": _("Round 1") if iv.round_type == "HR Interaction" else _("Final"), "status": iv.status, "date": iv.scheduled_datetime}
			for iv in interviews if iv.application == a.name
		]
	user = frappe.db.get_value("User", c.email, ["name", "enabled", "last_login"], as_dict=True) if c.email else None
	# Matching is by email only, so the same person applying with another
	# email becomes a second candidate: show records sharing the mobile number.
	similar = frappe.get_all(
		"Candidate",
		filters={"mobile_number": c.mobile_number, "name": ["!=", c.name]} if c.mobile_number else {"name": ""},
		fields=["name", "full_name", "email"],
	)
	return {
		"candidate": {
			"name": c.name, "full_name": c.full_name, "email": c.email, "mobile_number": c.mobile_number,
			"date_of_birth": c.date_of_birth, "gender": c.gender, "category": c.category, "address": c.address,
			"creation": c.creation,
		},
		"applications": apps,
		"portal": {"exists": 1, "enabled": user.enabled, "last_login": user.last_login} if user else {"exists": 0},
		"same_mobile": similar,
		"can_edit": 1 if frappe.has_permission("Candidate", "write", doc=c) else 0,
	}
