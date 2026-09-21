# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe


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


@frappe.whitelist()
def get_recruiter_summary():
	"""Recruiter-scoped operational dashboard — pending action items
	across the pipeline for the logged-in recruiter's view.
	"""
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
