# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from pathways.permissions import has_full_access


def require_pipeline_access():
	"""These endpoints aggregate with frappe.db.count/get_all, which skip
	permission checks — so gate them explicitly: only users who can see
	every Application (granted read via a non-scoped role) get pipeline
	numbers."""
	if not has_full_access("Application"):
		frappe.throw(_("You do not have access to recruitment pipeline data."), frappe.PermissionError)


def _application_filters(track=None, job_opening=None, department=None, from_date=None, to_date=None):
	filters = {}
	if job_opening:
		filters["job_opening"] = job_opening
	if from_date and to_date:
		filters["application_date"] = ["between", [from_date, to_date]]

	if track or department:
		job_filters = {}
		if track:
			job_filters["track"] = track
		if department:
			job_filters["department"] = department
		job_names = frappe.get_all("Job Opening", filters=job_filters, pluck="name")
		filters["job_opening"] = ["in", job_names]

	return filters


# Dashboard filters: every key optional; list values are "any of".
JOB_FILTER_FIELDS = (
	("tracks", "track"),
	("departments", "department"),
	("positions", "position"),
	("employment_types", "employment_type"),
	("job_openings", "name"),
)


def build_filters(filters):
	"""(application filters, job filters) from the dashboard filter bar."""
	f = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
	job_filters = {field: ["in", f[key]] for key, field in JOB_FILTER_FIELDS if f.get(key)}
	if f.get("deadline_from") and f.get("deadline_to"):
		job_filters["application_deadline"] = ["between", [f"{f['deadline_from']} 00:00:00", f"{f['deadline_to']} 23:59:59"]]

	app_filters = {}
	if job_filters:
		app_filters["job_opening"] = ["in", frappe.get_all("Job Opening", filters=job_filters, pluck="name") or [""]]
	if f.get("from_date") and f.get("to_date"):
		app_filters["application_date"] = ["between", [f["from_date"], f["to_date"]]]
	if f.get("statuses"):
		app_filters["status"] = ["in", f["statuses"]]
	if f.get("eligibility"):
		app_filters["eligibility_status"] = ["in", f["eligibility"]]
	return app_filters, job_filters


def _status_counts(app_filters):
	from collections import Counter

	return Counter(frappe.get_all("Application", filters=app_filters, pluck="status"))


@frappe.whitelist()
def get_admin_summary(track=None, job_opening=None, department=None, from_date=None, to_date=None):
	"""Server-side aggregated counts for the Admin Dashboard — never
	returns raw Application records, per brief §26/§41.
	"""
	require_pipeline_access()
	filters = _application_filters(track, job_opening, department, from_date, to_date)

	def count(**extra):
		f = {**filters, **extra}
		return frappe.db.count("Application", f)

	return {
		"total_applications": count(),
		"screening_pending": count(status="Submitted") + count(status="Under Review"),
		"shortlisted": count(status="Shortlisted"),
		"interviews_scheduled": count(status="Interview Scheduled"),
		"selected": count(status="Selected"),
		"offers_released": count(status="Offer Extended"),
		"offers_accepted": count(status="Offer Accepted"),
		"documents_pending": count(status="Documents Pending"),
		"joined": count(status="Joined"),
		"rejected": count(status="Not Selected"),
	}


FUNNEL_STAGES = [
	(
		"Applied",
		[
			"Submitted",
			"Under Review",
			"Shortlisted",
			"Interview Scheduled",
			"Interview Completed",
			"Selected",
			"Offer Extended",
			"Offer Accepted",
			"Offer Declined",
			"Documents Pending",
			"Documents Verified",
			"Joined",
			"Not Selected",
			"Withdrawn",
		],
	),
	(
		"Shortlisted",
		[
			"Shortlisted",
			"Interview Scheduled",
			"Interview Completed",
			"Selected",
			"Offer Extended",
			"Offer Accepted",
			"Offer Declined",
			"Documents Pending",
			"Documents Verified",
			"Joined",
		],
	),
	(
		"Interviewed",
		[
			"Interview Completed",
			"Selected",
			"Offer Extended",
			"Offer Accepted",
			"Offer Declined",
			"Documents Pending",
			"Documents Verified",
			"Joined",
		],
	),
	(
		"Selected",
		["Selected", "Offer Extended", "Offer Accepted", "Offer Declined", "Documents Pending", "Documents Verified", "Joined"],
	),
	("Joined", ["Joined"]),
]


@frappe.whitelist()
def get_pipeline_funnel(track=None, job_opening=None, department=None, from_date=None, to_date=None):
	"""Cumulative recruitment funnel for the Admin Dashboard chart.

	Each stage counts every Application that has REACHED that stage or
	any later one — not just applications currently sitting in that
	status — so the bars are naturally non-increasing and read as a
	real funnel. (get_admin_summary's counts are point-in-time current
	status instead, which answers a different question: "what needs
	attention right now.")
	"""
	require_pipeline_access()
	filters = _application_filters(track, job_opening, department, from_date, to_date)

	stages = []
	for label, statuses in FUNNEL_STAGES:
		count = frappe.db.count("Application", {**filters, "status": ["in", statuses]})
		stages.append({"label": label, "value": count})

	return stages


@frappe.whitelist()
def get_recruiter_summary():
	"""Recruiter-scoped operational dashboard — pending action items
	across the pipeline for the logged-in recruiter's view.
	"""
	require_pipeline_access()
	open_jobs = frappe.db.count("Job Opening", {"status": "Advertised"})
	pending_screening = frappe.db.count("Application", {"status": ["in", ["Submitted", "Under Review"]]})

	upcoming_interviews = frappe.get_all(
		"Interview",
		filters={"status": "Scheduled"},
		fields=["name", "application", "round_type", "scheduled_datetime"],
		order_by="scheduled_datetime asc",
		limit_page_length=10,
	)

	feedback_pending = frappe.db.sql(
		"""
		select i.name, i.application
		from `tabInterview` i
		where i.status = 'Completed'
		and i.round_type = 'Final'
		and not exists (
			select 1 from `tabInterview Assessment` ia where ia.interview = i.name
		)
		limit 20
		""",
		as_dict=True,
	)

	documents_pending = frappe.db.count(
		"Document Collection", {"overall_status": ["in", ["Pending", "Partially Submitted", "Under Verification"]]}
	)

	offers_pending = frappe.db.count("Offer Appointment Order", {"status": "Sent"})

	return {
		"open_job_openings": open_jobs,
		"pending_screening": pending_screening,
		"upcoming_interviews": upcoming_interviews,
		"feedback_pending_count": len(feedback_pending),
		"documents_pending": documents_pending,
		"offers_pending": offers_pending,
	}


# Dashboard card / funnel bar -> the application statuses it counts. Must
# match get_admin_summary and FUNNEL_STAGES, so a drill-down always lists
# exactly what its number counted.
CARD_STATUSES = {
	"total_applications": None,
	"screening_pending": ["Submitted", "Under Review"],
	"shortlisted": ["Shortlisted"],
	"interviews_scheduled": ["Interview Scheduled"],
	"selected": ["Selected"],
	"offers_released": ["Offer Extended"],
	"offers_accepted": ["Offer Accepted"],
	"documents_pending": ["Documents Pending"],
	"joined": ["Joined"],
	"rejected": ["Not Selected"],
}
DRILLDOWN_LIMIT = 500


@frappe.whitelist()
def get_drilldown(bucket, track=None, job_opening=None, department=None, from_date=None, to_date=None, filters=None):
	"""The applications behind one dashboard number.

	bucket: a get_admin_summary key, "funnel:<stage label>", or a Needs
	Attention item ("feedback_pending", "document_checklists",
	"offers_awaiting"). Rows: application name/id, candidate, job, status,
	date, plus a `detail` line where the bucket has one.
	"""
	require_pipeline_access()
	if filters:
		filters, _ = build_filters(filters)
	else:
		filters = _application_filters(track, job_opening, department, from_date, to_date)

	def with_statuses(statuses):
		"""Bucket statuses, narrowed by a status filter if one is set."""
		chosen = filters.get("status", [None, None])[1]
		return [s for s in statuses if s in chosen] if chosen else statuses

	if bucket in CARD_STATUSES:
		statuses = CARD_STATUSES[bucket]
		if statuses:
			filters["status"] = ["in", with_statuses(statuses) or [""]]
		return _application_rows(filters)

	if bucket.startswith("pipeline:"):
		# Recruitment Pipeline table: one job's count for one stage, counted
		# the same way as the Recruitment Pipeline report.
		if not job_opening:
			frappe.throw(_("Choose a job opening."))
		names = _pipeline_applications(job_opening, bucket.split(":", 1)[1])
		return _application_rows({"name": ["in", names or [""]]})

	if bucket.startswith("funnel:"):
		stage = dict(FUNNEL_STAGES).get(bucket.split(":", 1)[1])
		if stage is None:
			frappe.throw(_("Unknown pipeline stage."))
		return _application_rows({**filters, "status": ["in", with_statuses(stage) or [""]]})

	details = _attention_details(bucket)
	if not details:
		return []
	rows = _application_rows({**filters, "name": ["in", list(details)]})
	for row in rows:
		row["detail"] = details.get(row["name"])
	return rows


PIPELINE_STATUSES = {
	"selected": ["Selected"],
	"offered": ["Offer Extended", "Offer Accepted", "Offer Declined"],
	"joined": ["Joined"],
}


def _pipeline_applications(job_opening, stage):
	apps = frappe.get_all("Application", filters={"job_opening": job_opening}, pluck="name")
	if not apps or stage == "applied":
		return apps
	if stage == "eligible":
		return frappe.get_all("Eligibility Check", filters={"application": ["in", apps], "is_eligible": 1}, pluck="application")
	if stage == "shortlisted":
		return frappe.get_all("Shortlisting Score", filters={"application": ["in", apps], "is_shortlisted": 1}, pluck="application")
	if stage == "interviewed":
		return frappe.get_all("Interview", filters={"application": ["in", apps], "status": "Completed"}, pluck="application")
	if stage in PIPELINE_STATUSES:
		return frappe.get_all("Application", filters={"name": ["in", apps], "status": ["in", PIPELINE_STATUSES[stage]]}, pluck="name")
	frappe.throw(_("Unknown pipeline stage."))


def _attention_details(bucket):
	"""{application: detail line} for a Needs Attention item, using the same
	conditions as get_recruiter_summary."""
	if bucket == "feedback_pending":
		rows = frappe.db.sql(
			"""
			select i.application, i.round_type
			from `tabInterview` i
			where i.status = 'Completed' and i.round_type = 'Final'
			and not exists (select 1 from `tabInterview Assessment` ia where ia.interview = i.name)
			""",
			as_dict=True,
		)
		return {r.application: _("{0} interview awaiting feedback").format(r.round_type) for r in rows}
	if bucket == "document_checklists":
		rows = frappe.get_all(
			"Document Collection",
			filters={"overall_status": ["in", ["Pending", "Partially Submitted", "Under Verification"]]},
			fields=["application", "overall_status"],
		)
		return {r.application: _("Documents: {0}").format(r.overall_status) for r in rows}
	if bucket == "offers_awaiting":
		rows = frappe.get_all("Offer Appointment Order", filters={"status": "Sent"}, fields=["application", "name"])
		return {r.application: _("Offer {0} sent, awaiting response").format(r.name) for r in rows}
	frappe.throw(_("Unknown dashboard item."))


def _application_rows(filters):
	apps = frappe.get_all(
		"Application",
		filters=filters,
		fields=["name", "application_id", "candidate", "job_opening", "status", "application_date"],
		order_by="creation desc",
		limit_page_length=DRILLDOWN_LIMIT,
	)
	if not apps:
		return []
	names = dict(
		frappe.get_all(
			"Candidate", filters={"name": ["in", {a.candidate for a in apps}]}, fields=["name", "full_name"], as_list=True
		)
	)
	titles = dict(
		frappe.get_all(
			"Job Opening", filters={"name": ["in", {a.job_opening for a in apps}]}, fields=["name", "job_title"], as_list=True
		)
	)
	return [
		{
			"name": a.name,
			"application_id": a.application_id,
			"candidate_name": names.get(a.candidate) or a.candidate,
			"job_title": titles.get(a.job_opening) or a.job_opening,
			"status": a.status,
			"application_date": a.application_date,
		}
		for a in apps
	]


# ------------------------------------------------------------ dashboard page
# Lists rather than charts: what is due, what is new, what needs a decision.


@frappe.whitelist()
def get_dashboard(filters=None):
	require_pipeline_access()
	from frappe.utils import getdate, now_datetime

	from pathways.api.scoring import shortlisting_summary

	app_filters, job_filters = build_filters(filters)
	jobs = frappe.get_all(
		"Job Opening",
		filters={**job_filters, "status": ["not in", ["Cancelled", "Filled"]]},
		fields=["name", "job_title", "position", "department", "track", "status", "vacancies", "application_deadline", "shortlisting_ratio"],
		order_by="application_deadline asc",
	)
	now = now_datetime()

	# Jobs at a glance (with the 1:N target)
	glance = []
	for job in jobs:
		s = shortlisting_summary(frappe._dict(job))
		days = (getdate(job.application_deadline) - getdate(now)).days if job.application_deadline else None
		glance.append({**job, **{k: s[k] for k in ("applications", "pending", "eligible", "not_eligible", "shortlisted", "target", "ratio")},
			"days_left": days, "has_committee": bool(s["committee"])})

	# Deadlines: the next ad closing dates and committee deadlines, soonest first
	deadlines = [
		{"kind": "Ad closes", "job": j["name"], "title": j["job_title"], "date": j["application_deadline"], "days_left": j["days_left"],
			"detail": f"{j['applications']} application(s)"}
		for j in glance
		if j["status"] == "Advertised" and j["days_left"] is not None and j["days_left"] >= 0
	]
	for c in frappe.get_all("Shortlisting Committee", filters={"shortlisting_deadline": [">=", getdate(now)]},
		fields=["job_opening", "shortlisting_deadline"]):
		job = next((j for j in glance if j["name"] == c.job_opening), None)
		if job:
			deadlines.append({"kind": "Shortlisting due", "job": job["name"], "title": job["job_title"], "date": c.shortlisting_deadline,
				"days_left": (getdate(c.shortlisting_deadline) - getdate(now)).days,
				"detail": f"{job['shortlisted']} of {job['target']} shortlisted"})
	deadlines.sort(key=lambda d: str(d["date"]))

	# Needs attention
	pending_sheets = frappe.get_all("Pre-Recruitment Green Sheet", filters={"docstatus": 1, "status": "Under Approval",
		**({"job_opening": ["in", [j.name for j in jobs]]} if job_filters else {})}, pluck="job_opening")
	attention = [
		{"key": "eligibility_pending", "count": frappe.db.count("Application", {**app_filters, "eligibility_status": "Pending",
			"status": ["not in", ["Withdrawn", "Not Selected"]]}), "label": "application(s) awaiting eligibility check", "link": "/applications"},
		{"key": "green_sheets", "count": len(pending_sheets), "label": "green sheet(s) awaiting approval", "link": "/approvals"},
		{"key": "closing_soon", "count": sum(1 for j in glance if j["status"] == "Advertised" and j["days_left"] is not None and 0 <= j["days_left"] <= 3),
			"label": "ad(s) closing within 3 days", "link": "/jobs"},
		{"key": "no_committee", "count": sum(1 for j in glance if j["applications"] and not j["has_committee"]),
			"label": "job(s) with applications but no shortlisting committee", "link": "/jobs"},
		{"key": "below_target", "count": sum(1 for j in glance if j["status"] == "Closed" and j["shortlisted"] < j["target"] and j["eligible"] > j["shortlisted"]),
			"label": "closed ad(s) still below the shortlisting target", "link": "/jobs"},
	]

	# Recent applications
	recent_apps = frappe.get_all("Application", filters=app_filters,
		fields=["name", "application_id", "candidate.full_name as candidate_name", "job_opening.job_title as job_title", "status",
			"eligibility_status", "application_date", "creation"],
		order_by="creation desc", limit_page_length=10)

	# Recent activity: status changes, eligibility notes, corrigenda, approvals
	app_names = frappe.get_all("Application", filters=app_filters, pluck="name") if (app_filters or job_filters) else None
	hist_filters = {"application": ["in", app_names or [""]]} if app_names is not None else {}
	activity = [
		{"at": h.changed_on, "kind": "status", "text": f"{h.previous_status} → {h.new_status}", "who": frappe.utils.get_fullname(h.changed_by),
			"link": f"/applications/{h.application}", "ref": h.application}
		for h in frappe.get_all("Application Status History", filters=hist_filters,
			fields=["application", "previous_status", "new_status", "changed_by", "changed_on"], order_by="changed_on desc", limit_page_length=10)
	]
	corr_filters = {"job_opening": ["in", [j.name for j in jobs]]} if job_filters else {}
	activity += [
		{"at": c.creation, "kind": "corrigendum", "text": f"Corrigendum: {'deadline extended' if c.changed_field == 'Closing Date' else c.new_value}",
			"who": frappe.utils.get_fullname(c.signed_by), "link": f"/jobs/{c.job_opening}", "ref": c.job_opening}
		for c in frappe.get_all("Corrigendum", filters=corr_filters, fields=["creation", "changed_field", "new_value", "signed_by", "job_opening"],
			order_by="creation desc", limit_page_length=5)
	]
	names = {a.name: a for a in frappe.get_all("Application", filters={"name": ["in", [x["ref"] for x in activity if x["kind"] == "status"] or [""]]},
		fields=["name", "application_id", "candidate.full_name as candidate_name", "job_opening.job_title as job_title"])}
	for item in activity:
		if item["kind"] == "status" and item["ref"] in names:
			a = names[item["ref"]]
			item["subject"] = f"{a.candidate_name} · {a.job_title}"
		elif item["kind"] == "corrigendum":
			item["subject"] = frappe.db.get_value("Job Opening", item["ref"], "job_title")
	activity.sort(key=lambda x: str(x["at"]), reverse=True)

	counts = _status_counts(app_filters)
	summary = {
		"total_applications": sum(counts.values()),
		**{key: sum(counts.get(s, 0) for s in statuses) for key, statuses in CARD_STATUSES.items() if statuses},
	}
	positions = frappe.get_all("Position", filters={"is_active": 1}, fields=["name", "position_title"], order_by="name asc")
	return {
		"summary": summary,
		"attention": attention,
		"deadlines": deadlines[:12],
		"jobs": glance,
		"recent_applications": recent_apps,
		"activity": activity[:10],
		"options": {
			"tracks": frappe.get_all("Recruitment Track", filters={"is_active": 1}, pluck="name", order_by="name asc"),
			"departments": frappe.get_all("Department", filters={"is_active": 1}, pluck="name", order_by="name asc"),
			"positions": [{"value": p.name, "label": f"{p.name} · {p.position_title}"} for p in positions],
			"employment_types": [o for o in frappe.get_meta("Job Opening").get_field("employment_type").options.split("\n") if o],
			"statuses": [o for o in frappe.get_meta("Application").get_field("status").options.split("\n") if o],
			"eligibility": ["Pending", "Eligible", "Not Eligible"],
			# All jobs with their attributes, so the page can narrow the list to the other filters.
			"jobs": frappe.get_all("Job Opening", fields=["name", "job_title", "track", "department", "position", "employment_type"], order_by="job_title asc"),
		},
	}
