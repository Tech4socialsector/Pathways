# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Post-Interview ("selection") Green Sheet actions for the staff SPA.

Workflow steps 20, 24 and 25: once the Selection Committee's outcomes are
recorded on the consolidated score sheet, the recruiter raises this sheet
from the job page (or the score sheet), which drafts it from the job's
records — the recommended and waitlisted candidates, the process narrative
and a fee row per selected candidate. It is then edited on
/pathways/selection-green-sheets/<name>, submitted into the approval chain
configured for the job's track (Master Setup > Approval Chains) and, once
signed on paper, the scan is attached.

Mirrors pathways.api.green_sheet (the Pre-Recruitment sheet). Approving /
returning goes through pathways.api.approval.record_approval_action.
Insert/save/submit/cancel enforce the doctype's Role Permissions.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from pathways.api.approval import get_approval_chain_status
from pathways.pathways.doctype.job_opening.job_opening import can_override_status
from pathways.pathways.doctype.post_interview_green_sheet.post_interview_green_sheet import (
	DOCTYPE,
	OPEN_STATUSES,
	candidate_name,
	panel_recommendation,
)
from pathways.utils.approval import check_can_act, find_template, reset_for_amendment

# Fields the detail page may edit on a draft (everything else is derived).
EDITABLE_FIELDS = (
	"subject",
	"file_reference",
	"selection_note",
	"advertisement_published_on",
	"advertisement_closed_on",
	"applications_received",
	"candidates_shortlisted",
	"interview_date",
	"candidates_interviewed",
	"recommended_application",
	"waitlist_application",
	"verbal_acceptance",
	"reference_check_status",
	"date_of_appointment",
	"duration_of_appointment",
	"reports_to",
	"probation_period",
	"deliverables",
	"advertised_pay_level",
	"fixed_pay_level",
	"basic_pay",
	"current_basic_salary",
	"current_gross_salary",
	"ctc",
	"gross_salary",
	"pay_fixation_note",
	"project_name",
	"funding_source",
	"compensation_narrative",
	"panel_recommendation_attachment",
	"score_sheet_attachment",
	"reference_check_attachment",
	"salary_proof_attachment",
	"other_annexure_attachment",
)
ROW_FIELDS = (
	"application",
	"candidate_name",
	"years_experience",
	"highest_qualification",
	"recommended_salary",
	"position_offered",
	"medical_insurance",
	"leave_applicable",
)
ANNEXURES = (
	("panel_recommendation_attachment", "Panel Recommendation (signed by VC)"),
	("score_sheet_attachment", "Consolidated Score Sheet"),
	("reference_check_attachment", "Reference Check Forms"),
	("salary_proof_attachment", "Latest Payslip / Salary Proof"),
	("other_annexure_attachment", "Other Annexure"),
)
# Shortlisted at some point (Not Selected/Withdrawn are counted only if interviewed).
SHORTLISTED_STATUSES = (
	"Shortlisted", "Interview Scheduled", "Interview Completed", "Selected", "Offer Extended", "Offer Accepted",
	"Offer Declined", "Documents Pending", "Documents Verified", "Joined",
)
DEGREE_ORDER = {"Undergraduate": 1, "Postgraduate": 2, "Doctoral": 3}


# ------------------------------------------------------------------ helpers


def _get_sheet(name):
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("read")
	return doc


def _get_job(job_opening):
	job = frappe.get_doc("Job Opening", job_opening)
	job.check_permission("read")
	return job


def _find_open_sheet(job_opening):
	"""The job's draft or in-flight sheet, if any."""
	draft = frappe.db.get_value(DOCTYPE, {"job_opening": job_opening, "docstatus": 0}, "name")
	if draft:
		return draft
	return frappe.db.get_value(DOCTYPE, {"job_opening": job_opening, "docstatus": 1, "status": ("in", OPEN_STATUSES)}, "name")


def _can_upload_signed():
	return bool(frappe.has_permission(DOCTYPE, "create")) or can_override_status()


def _long_date(value):
	return getdate(value).strftime("%B %-d, %Y") if value else "____"


def _join(names):
	names = [n for n in names if n]
	if len(names) < 2:
		return "".join(names)
	return ", ".join(names[:-1]) + " and " + names[-1]


def _member_names(parenttype, parent):
	rows = frappe.get_all(
		"Committee Member Row",
		filters={"parenttype": parenttype, "parent": parent},
		fields=["member", "designation_label", "is_external_expert"],
		order_by="idx asc",
	)
	out = []
	for r in rows:
		label = frappe.utils.get_fullname(r.member)
		if r.designation_label:
			label += f", {r.designation_label}"
		if r.is_external_expert:
			label += " (external expert)"
		out.append(label)
	return out


def _experience(app):
	years = flt(app.overall_experience_years) or (cint(app.overall_experience_months) / 12.0)
	if not years:
		return "Fresher"
	whole, months = int(years), round((years - int(years)) * 12)
	parts = [f"{whole} year{'s' if whole != 1 else ''}"] if whole else []
	if months:
		parts.append(f"{months} month{'s' if months != 1 else ''}")
	return " ".join(parts)


def _highest_qualification(application):
	quals = frappe.get_all("Application Qualification", filters={"parent": application, "parenttype": "Application"}, fields=["degree_level", "degree_name"])
	if not quals:
		return ""
	best = max(quals, key=lambda q: DEGREE_ORDER.get(q.degree_level, 0))
	return best.degree_name or best.degree_level or ""


def outcomes_for_job(job_opening):
	"""Selected and waitlisted candidates, best consolidated average first."""
	rec = panel_recommendation(job_opening)
	ranked = {r.application: r for r in rec.rows}
	apps = frappe.get_all(
		"Application",
		filters={"job_opening": job_opening, "selection_outcome": ["in", ["Selected", "Waitlisted"]]},
		fields=["name", "application_id", "selection_outcome", "status"],
	)
	out = {"Selected": [], "Waitlisted": []}
	for a in apps:
		r = ranked.get(a.name)
		out[a.selection_outcome].append(
			{
				"application": a.name,
				"application_id": a.application_id,
				"candidate_name": candidate_name(a.name),
				"status": a.status,
				"average": r.average if r else None,
				"percent": r.percent if r else None,
				"rank": r.rank if r else None,
			}
		)
	for rows in out.values():
		rows.sort(key=lambda x: (x["rank"] is None, x["rank"] or 0))
	return {"selected": out["Selected"], "waitlisted": out["Waitlisted"], "max_total": rec.max_total}


def draft_values(job_opening):
	"""Everything the sheet can be drafted with from the job's records."""
	job = frappe.get_doc("Job Opening", job_opening)
	outcomes = outcomes_for_job(job_opening)
	selected, waitlisted = outcomes["selected"], outcomes["waitlisted"]
	if not selected:
		frappe.throw(_("Record at least one Selected candidate on the consolidated score sheet before raising the Selection Green Sheet."))

	apps = frappe.get_all("Application", filters={"job_opening": job_opening}, fields=["name", "status"])
	app_names = [a.name for a in apps] or [""]
	interviewed = set(frappe.get_all("Interview", filters={"application": ["in", app_names], "status": ["!=", "Cancelled"]}, pluck="application"))
	shortlisted = len({a.name for a in apps if a.status in SHORTLISTED_STATUSES} | interviewed)
	finals = frappe.get_all(
		"Interview",
		filters={"application": ["in", app_names], "round_type": "Final", "status": ["!=", "Cancelled"]},
		fields=["application", "status", "scheduled_datetime"],
		order_by="scheduled_datetime asc",
	)
	interviewed_final = [f for f in finals if f.status == "Completed"] or finals
	dates = sorted({f.scheduled_datetime.date() for f in interviewed_final if f.scheduled_datetime})

	committee = frappe.db.get_value("Selection Committee", {"job_opening": job_opening}, "name")
	shortlisters = frappe.db.get_value("Shortlisting Committee", {"job_opening": job_opening}, "name")
	vacancies = cint(job.vacancies) or 1
	title = job.job_title or job.designation or ""
	selected_names = [s["candidate_name"] for s in selected]
	wait_name = waitlisted[0]["candidate_name"] if waitlisted else None

	paragraphs = [
		f"NLSIU called for applications for the appointment of {vacancies} {title}. "
		f"The advertisement was published on {_long_date(job.application_start)}, and closed on {_long_date(job.application_deadline)}.",
		f"The advertisement received {len(apps)} applications, and {shortlisted} candidates were shortlisted for interviews."
		+ (f" Shortlisting was done by {_join(_member_names('Shortlisting Committee', shortlisters))}." if shortlisters else ""),
		f"The interview committee consisting of {_join(_member_names('Selection Committee', committee)) if committee else '____'}, "
		f"interviewed {len(interviewed_final)} candidate{'s' if len(interviewed_final) != 1 else ''} on {_join([_long_date(d) for d in dates]) or '____'}, "
		f"and recommended that {_join(selected_names)} may be appointed as {title}.",
	]
	if wait_name:
		paragraphs.append(
			f"In the event that {_join(selected_names) if len(selected_names) == 1 else 'any of the selected candidates'} "
			f"is unable to accept, the panel recommends {wait_name} be appointed as {title}."
		)

	is_permanent = job.employment_type == "Permanent"
	rows = []
	for s in selected:
		app = frappe.db.get_value(
			"Application", s["application"], ["overall_experience_years", "overall_experience_months", "expected_salary"], as_dict=True
		)
		rows.append(
			{
				"application": s["application"],
				"candidate_name": s["candidate_name"],
				"years_experience": _experience(app),
				"highest_qualification": _highest_qualification(s["application"]),
				"recommended_salary": None,
				"position_offered": title,
				"medical_insurance": 0 if is_permanent else 1,
				"leave_applicable": 0 if is_permanent else 1,
			}
		)

	return {
		"subject": f"Appointment of {title} ({vacancies} Vacanc{'ies' if vacancies != 1 else 'y'})",
		"selection_note": "\n\n".join(paragraphs),
		"advertisement_published_on": getdate(job.application_start) if job.application_start else None,
		"advertisement_closed_on": getdate(job.application_deadline) if job.application_deadline else None,
		"applications_received": len(apps),
		"candidates_shortlisted": shortlisted,
		"interview_date": dates[0] if dates else None,
		"candidates_interviewed": len(interviewed_final),
		"selection_committee": committee,
		"recommended_application": selected[0]["application"],
		"waitlist_application": waitlisted[0]["application"] if waitlisted else None,
		"reference_check_status": "Pending",
		"duration_of_appointment": job.tenure_description or None,
		"advertised_pay_level": job.pay_level or None,
		"compensation_table": rows,
	}


# ------------------------------------------------------------------- reads


def _permissions(sheet=None):
	can_act, reason = False, None
	if sheet and sheet.docstatus == 1 and sheet.status == "Under Approval":
		can_act, _override, reason = check_can_act(sheet)
	return {
		"can_create": bool(frappe.has_permission(DOCTYPE, "create")),
		"can_submit": bool(frappe.has_permission(DOCTYPE, "submit")),
		"can_cancel": bool(frappe.has_permission(DOCTYPE, "cancel")),
		"can_upload_signed": _can_upload_signed(),
		"can_act": can_act,
		"act_blocked_reason": reason,
		"can_override_status": can_override_status(),
	}


@frappe.whitelist()
def get_job_selection(job_opening):
	"""The job page's Selection card: the outcomes recorded so far, every
	Selection Green Sheet raised for the job (newest first) and what the
	session user may do."""
	job = _get_job(job_opening)
	sheets = frappe.get_list(
		DOCTYPE,
		filters={"job_opening": job_opening},
		fields=[
			"name", "status", "docstatus", "subject", "recommended_application", "recommended_candidate_name",
			"waitlist_application", "waitlist_candidate_name", "signed_copy_attachment", "amended_from", "owner", "creation", "modified",
		],
		order_by="creation desc",
	)
	for sheet in sheets:
		if sheet.docstatus == 2:
			sheet.status = "Cancelled"
	current = next((s for s in sheets if s.docstatus != 2), None)
	chain = None
	current_doc = None
	if current and current.docstatus == 1:
		chain = get_approval_chain_status(DOCTYPE, current.name)
		current_doc = frappe.get_doc(DOCTYPE, current.name)
	open_sheet = _find_open_sheet(job_opening)
	return {
		"outcomes": outcomes_for_job(job_opening),
		"sheets": sheets,
		"current": current,
		"chain": chain,
		"open_sheet": open_sheet,
		"has_chain_template": bool(find_template(job.track, DOCTYPE, job.employment_type)),
		"permissions": _permissions(current_doc),
	}


@frappe.whitelist()
def get_sheet(name):
	"""Everything the detail page needs: the sheet, its job, the candidates
	who can be recommended, the annexures and the approval chain."""
	doc = _get_sheet(name)
	job = frappe.db.get_value(
		"Job Opening",
		doc.job_opening,
		["name", "job_title", "position", "department", "designation", "track", "employment_type", "vacancies", "pay_level", "status"],
		as_dict=True,
	)
	candidates = []
	for a in frappe.get_all(
		"Application",
		filters={"job_opening": doc.job_opening, "status": ["not in", ["Submitted", "Under Review"]]},
		fields=["name", "application_id", "selection_outcome", "status"],
		order_by="application_id asc",
	):
		candidates.append(
			{
				"value": a.name,
				"label": f"{candidate_name(a.name) or a.application_id} ({a.application_id}{', ' + a.selection_outcome if a.selection_outcome else ''})",
				"outcome": a.selection_outcome,
			}
		)
	data = doc.as_dict(convert_dates_to_str=True)
	if doc.docstatus == 2:
		data["status"] = "Cancelled"
	return {
		"doc": data,
		"job": job,
		"candidates": candidates,
		"annexures": [{"field": f, "label": label} for f, label in ANNEXURES],
		"chain": get_approval_chain_status(DOCTYPE, doc.name) if doc.docstatus == 1 else None,
		"has_chain_template": bool(find_template(job.track, DOCTYPE, job.employment_type)),
		"is_permanent": job.employment_type == "Permanent",
		"show_funding": job.track == "Research" or job.employment_type == "Grant-funded",
		"newer_sheet": frappe.db.get_value(DOCTYPE, {"amended_from": doc.name}, "name"),
		"permissions": _permissions(doc),
	}


# ----------------------------------------------------------------- actions


@frappe.whitelist(methods=["POST"])
def create_from_outcomes(job_opening):
	"""Raise the job's Selection Green Sheet as a draft, pre-filled from the
	committee's outcomes (or return the draft/in-flight one that exists)."""
	job = _get_job(job_opening)
	if not job.track:
		frappe.throw(_("Set a Recruitment Track on the Job Opening first."))
	existing = _find_open_sheet(job_opening)
	if existing:
		return existing
	doc = frappe.new_doc(DOCTYPE)
	doc.job_opening = job_opening
	values = draft_values(job_opening)
	rows = values.pop("compensation_table")
	doc.update(values)
	for row in rows:
		doc.append("compensation_table", row)
	doc.insert()
	return doc.name


@frappe.whitelist(methods=["POST"])
def refresh_from_outcomes(name):
	"""Re-draft a draft from the job's current outcomes (overwrites the
	recommendation, the process fields, the note and the fee rows)."""
	doc = _get_sheet(name)
	if doc.docstatus != 0:
		frappe.throw(_("Only a draft Selection Green Sheet can be refreshed."))
	values = draft_values(doc.job_opening)
	rows = values.pop("compensation_table")
	# Keep the fees already entered for candidates still selected.
	fees = {r.application: r.recommended_salary for r in doc.compensation_table if r.application}
	doc.update(values)
	doc.set("compensation_table", [])
	for row in rows:
		row["recommended_salary"] = fees.get(row["application"])
		doc.append("compensation_table", row)
	doc.save()
	return doc.name


@frappe.whitelist(methods=["POST"])
def save_sheet(name, data, submit=0):
	"""Update a draft from the detail page and optionally submit it."""
	doc = _get_sheet(name)
	if doc.docstatus != 0:
		frappe.throw(_("Only a draft Selection Green Sheet can be edited."))
	data = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	for field in EDITABLE_FIELDS:
		if field in data:
			value = data[field]
			doc.set(field, None if value == "" else value)
	if "compensation_table" in data:
		doc.set("compensation_table", [])
		for row in data.get("compensation_table") or []:
			doc.append("compensation_table", {k: row.get(k) for k in ROW_FIELDS if k in row})
	doc.save()
	if cint(submit):
		doc.submit()
	return doc.name


@frappe.whitelist(methods=["POST"])
def submit_sheet(name):
	doc = _get_sheet(name)
	if doc.docstatus != 0:
		frappe.throw(_("This Selection Green Sheet has already been submitted."))
	doc.submit()
	return doc.name


@frappe.whitelist(methods=["POST"])
def withdraw_sheet(name):
	doc = _get_sheet(name)
	if doc.docstatus != 1 or doc.status not in OPEN_STATUSES:
		frappe.throw(_("Only a Selection Green Sheet that is under approval or returned can be withdrawn."))
	doc.cancel()
	return doc.name


@frappe.whitelist(methods=["POST"])
def revise_sheet(name):
	"""Cancel a sheet Returned for Revision and open an amended draft with
	the same content, to be edited and resubmitted."""
	doc = _get_sheet(name)
	if doc.docstatus != 1 or doc.status != "Returned for Revision":
		frappe.throw(_("Only a Selection Green Sheet that was returned for revision can be revised."))
	doc.cancel()
	amended = frappe.copy_doc(doc)
	# copy_doc keeps the source's docstatus (2 here).
	amended.docstatus = 0
	amended.amended_from = doc.name
	amended.signed_copy_attachment = None
	reset_for_amendment(amended)
	amended.insert()
	return amended.name


@frappe.whitelist(methods=["POST"])
def delete_draft(name):
	doc = _get_sheet(name)
	if doc.docstatus != 0:
		frappe.throw(_("Only a draft Selection Green Sheet can be deleted."))
	# Whoever may raise sheets may discard an unsubmitted draft; Pathways
	# Recruiter has create but not the general delete right.
	if not frappe.has_permission(DOCTYPE, "create"):
		raise frappe.PermissionError
	frappe.delete_doc(DOCTYPE, name, ignore_permissions=True)
	return name


@frappe.whitelist(methods=["POST"])
def attach_signed_copy(name, file_url=None):
	"""Workflow step 25: keep the physically signed copy with the sheet
	(allowed after submission; an empty file_url removes it)."""
	doc = _get_sheet(name)
	if doc.docstatus != 1:
		frappe.throw(_("Upload the signed copy after the Selection Green Sheet has been submitted."))
	if not _can_upload_signed():
		frappe.throw(_("You cannot upload the signed Selection Green Sheet."), frappe.PermissionError)
	doc.db_set("signed_copy_attachment", file_url or None)
	doc.add_comment("Info", _("Signed copy uploaded.") if file_url else _("Signed copy removed."))
	return doc.signed_copy_attachment


# ------------------------------------------------------- for other modules


def get_approved_sheet_for_application(application):
	"""Name of the latest Approved Selection Green Sheet that recommends
	(or waitlists, or lists in its fee table) this application, else None.
	Offers use it to require an approved sheet before an offer goes out."""
	if not application:
		return None
	filters = {"docstatus": 1, "status": "Approved"}
	for field in ("recommended_application", "waitlist_application"):
		name = frappe.db.get_value(DOCTYPE, {**filters, field: application}, "name", order_by="creation desc")
		if name:
			return name
	parents = frappe.get_all("Compensation Table Row", filters={"parenttype": DOCTYPE, "application": application}, pluck="parent")
	if parents:
		return frappe.db.get_value(DOCTYPE, {**filters, "name": ["in", parents]}, "name", order_by="creation desc")
	return None
