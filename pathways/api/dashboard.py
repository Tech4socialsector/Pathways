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
def get_drilldown(bucket, track=None, job_opening=None, department=None, from_date=None, to_date=None):
	"""The applications behind one dashboard number.

	bucket: a get_admin_summary key, "funnel:<stage label>", or a Needs
	Attention item ("feedback_pending", "document_checklists",
	"offers_awaiting"). Rows: application name/id, candidate, job, status,
	date, plus a `detail` line where the bucket has one.
	"""
	require_pipeline_access()
	filters = _application_filters(track, job_opening, department, from_date, to_date)

	if bucket in CARD_STATUSES:
		statuses = CARD_STATUSES[bucket]
		if statuses:
			filters["status"] = ["in", statuses]
		return _application_rows(filters)

	if bucket.startswith("funnel:"):
		stage = dict(FUNNEL_STAGES).get(bucket.split(":", 1)[1])
		if stage is None:
			frappe.throw(_("Unknown pipeline stage."))
		return _application_rows({**filters, "status": ["in", stage]})

	details = _attention_details(bucket)
	if not details:
		return []
	rows = _application_rows({"name": ["in", list(details)]})
	for row in rows:
		row["detail"] = details.get(row["name"])
	return rows


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
