# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, getdate, now_datetime, today
from pathways.utils.db import commit


def hourly():
	close_expired_job_openings()


def close_expired_job_openings():
	"""Advertised jobs whose Application Deadline has passed move to Closed.
	(Submissions are already refused at the deadline itself; this keeps the
	status honest for staff.) Workflow step 6: the job's notification is
	closed too, and Communications and the recruiters are asked to take the
	ad down. db.set_value skips JobOpening.on_update, so that side effect is
	done here, exactly once: the job is no longer Advertised next hour."""
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
	from pathways.api.job_notice import close_advertisement

	for name in expired:
		# The public posting only serves Advertised jobs, so drop its link too
		# (JobOpening.set_advertisement_url does this on a normal save).
		frappe.db.set_value("Job Opening", name, {"status": "Closed", "advertisement_url": None})
		try:
			close_advertisement(name)
		except Exception:
			frappe.log_error(title=f"Pathways: closing the advertisement for {name} failed")
		# One job at a time, so a later failure cannot undo an earlier close.
		commit()


def daily():
	flag_ads_closing_soon()
	expire_overdue_offers()
	send_interview_reminders()
	delete_stale_application_drafts()
	send_reference_check_reminders()


def send_reference_check_reminders():
	"""Referees who have not answered get one reminder (Pathways Settings >
	Reference Checks)."""
	from pathways.api.reference_checks import send_reminders

	send_reminders()


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
	commit()


def expire_overdue_offers():
	"""Sent offers past their acceptance deadline become Expired (and the
	application Not Selected). Each offer is saved normally so its history
	and doc_events hooks see the change."""
	from pathways.pathways.doctype.offer_appointment_order.offer_appointment_order import (
		expire_overdue_offers as _expire,
	)

	return _expire()


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
				"interview_date_time": frappe.utils.format_datetime(interview.scheduled_datetime, "dd MMM yyyy, h:mm a 'IST'"),
				"meeting_link": interview.meeting_link,
			}
		)
		send_event("interview_reminder", "Interview", interview.name, context, candidate=candidate)


def delete_stale_application_drafts():
	"""Drafts for jobs that are gone, or closed for a month (long enough for
	a deadline extension to reopen them)."""
	cutoff = add_days(now_datetime(), -30)
	for draft in frappe.get_all("Application Draft", fields=["name", "job_opening", "saved_at"]):
		status = frappe.db.get_value("Job Opening", draft.job_opening, "status")
		if not status or (status != "Advertised" and (not draft.saved_at or draft.saved_at < cutoff)):
			frappe.delete_doc("Application Draft", draft.name, ignore_permissions=True, force=True)
	commit()
