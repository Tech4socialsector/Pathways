# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, getdate, now_datetime, today


def hourly():
	close_expired_job_openings()


def close_expired_job_openings():
	"""Advertised jobs whose Application Deadline has passed move to Closed.
	(Submissions are already refused at the deadline itself; this keeps the
	status honest for staff.)"""
	expired = frappe.get_all(
		"Job Opening",
		# "is set" matters: Frappe compares IFNULL(field, '0001-01-01'), so a
		# job without a deadline would otherwise count as expired.
		filters=[
			["status", "=", "Advertised"],
			["application_deadline", "is", "set"],
			["application_deadline", "<", now_datetime()],
		],
		pluck="name",
	)
	for name in expired:
		# The public posting only serves Advertised jobs, so drop its link too
		# (JobOpening.set_advertisement_url does this on a normal save).
		frappe.db.set_value("Job Opening", name, {"status": "Closed", "advertisement_url": None})
	if expired:
		frappe.db.commit()


def daily():
	flag_ads_closing_soon()
	expire_overdue_offers()
	send_interview_reminders()


def flag_ads_closing_soon():
	"""Confirmed source SLA: ad extension decision checked ~1 day before
	the ad's end date. Flags via ToDo rather than auto-extending, since
	extension is a human judgment call (Job Opening > Extend deadline)."""
	closing_soon = frappe.get_all(
		"Job Opening",
		filters=[
			["status", "=", "Advertised"],
			["application_deadline", "is", "set"],
			["application_deadline", "between", [now_datetime(), add_days(now_datetime(), 1)]],
		],
		fields=["name", "job_title", "owner"],
	)
	for job in closing_soon:
		if frappe.db.exists("ToDo", {"reference_type": "Job Opening", "reference_name": job.name, "status": "Open"}):
			continue
		todo = frappe.new_doc("ToDo")
		todo.description = (
			f"The advertisement for {job.job_title} ({job.name}) closes within 24 hours. "
			f"Decide whether to extend it (Extend deadline, which issues a Corrigendum) or let it close."
		)
		todo.reference_type = "Job Opening"
		todo.reference_name = job.name
		todo.allocated_to = job.owner if job.owner != "Guest" else None
		todo.insert(ignore_permissions=True)

		from pathways.utils.communication import job_email_context, send_event

		context = job_email_context(frappe.get_doc("Job Opening", job.name))
		context["application_count"] = frappe.db.count("Application", {"job_opening": job.name})
		send_event("ad_closing_soon", "Job Opening", job.name, context, job_opening=job.name)
	frappe.db.commit()


def expire_overdue_offers():
	overdue = frappe.get_all(
		"Offer Appointment Order",
		filters=[
			["status", "=", "Sent"],
			["acceptance_deadline", "is", "set"],
			["acceptance_deadline", "<", today()],
		],
		pluck="name",
	)
	for offer_name in overdue:
		frappe.db.set_value("Offer Appointment Order", offer_name, "status", "Expired")
		application = frappe.db.get_value("Offer Appointment Order", offer_name, "application")
		if application:
			frappe.db.set_value("Application", application, "status", "Not Selected")
	if overdue:
		frappe.db.commit()


def send_interview_reminders():
	"""T-1 day reminder for scheduled interviews (Email Setup > Interviews)."""
	from pathways.utils.communication import candidate_email_context, send_event

	tomorrow = add_days(today(), 1)
	upcoming = frappe.get_all(
		"Interview",
		filters={"status": "Scheduled", "scheduled_datetime": ["between", [today(), tomorrow]]},
		fields=["name", "application", "scheduled_datetime", "meeting_link"],
	)
	for interview in upcoming:
		context, candidate = candidate_email_context(interview.application)
		context.update(
			{
				"interview_date_time": frappe.utils.format_datetime(interview.scheduled_datetime, "dd MMM yyyy, h:mm a"),
				"meeting_link": interview.meeting_link,
			}
		)
		send_event("interview_reminder", "Interview", interview.name, context, candidate=candidate)
