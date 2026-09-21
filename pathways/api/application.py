# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today

from pathways.pathways.doctype.application.application import check_duplicate as _check_duplicate


@frappe.whitelist(allow_guest=True)
def get_open_job_openings(track=None, department=None, search=None):
	"""Public job board listing — backs the Job Board web form / candidate portal."""
	filters = {"status": "Advertised"}
	if track:
		filters["track"] = track
	if department:
		filters["department"] = department

	jobs = frappe.get_all(
		"Job Opening",
		filters=filters,
		fields=[
			"name",
			"job_title",
			"track",
			"department",
			"designation",
			"vacancies",
			"employment_type",
			"tenure_description",
			"pay_level",
		],
		order_by="creation desc",
	)

	if search:
		search_lower = search.lower()
		jobs = [j for j in jobs if search_lower in (j.job_title or "").lower()]

	return jobs


@frappe.whitelist(allow_guest=True)
def get_job_opening_detail(job_opening):
	job = frappe.get_doc("Job Opening", job_opening)
	if job.status != "Advertised":
		frappe.throw("This position is not currently open for applications.")
	return {
		"name": job.name,
		"job_title": job.job_title,
		"track": job.track,
		"department": job.department,
		"designation": job.designation,
		"vacancies": job.vacancies,
		"employment_type": job.employment_type,
		"tenure_description": job.tenure_description,
		"pay_level": job.pay_level,
		"jd_text": job.jd_text,
		"jd_attachment": job.jd_attachment,
	}


@frappe.whitelist(allow_guest=True)
def check_duplicate(email, mobile_number, job_opening):
	return _check_duplicate(email, mobile_number, job_opening)


@frappe.whitelist(allow_guest=True)
def submit_application(candidate_data, application_data):
	"""Creates (or reuses) a Candidate, then creates the Application with
	its child-table data, backing the public Candidate Application web
	form. Server-side duplicate check runs unconditionally before insert
	— frontend validation is UX-only, per policy.
	"""
	if isinstance(candidate_data, str):
		candidate_data = frappe.parse_json(candidate_data)
	if isinstance(application_data, str):
		application_data = frappe.parse_json(application_data)

	email = (candidate_data.get("email") or "").strip().lower()
	if not email:
		frappe.throw("Email is required.")

	job_opening = application_data.get("job_opening")
	if not job_opening:
		frappe.throw("Job Opening is required.")

	dup = _check_duplicate(email, candidate_data.get("mobile_number"), job_opening)
	if dup.get("duplicate"):
		frappe.throw("An application from this candidate for this position already exists.")

	candidate_name = dup.get("candidate")
	if not candidate_name:
		candidate = frappe.new_doc("Candidate")
		candidate.update(candidate_data)
		candidate.email = email
		candidate.insert(ignore_permissions=True)
		candidate_name = candidate.name

	application = frappe.new_doc("Application")
	application.update(application_data)
	application.candidate = candidate_name
	application.application_date = today()
	application.insert(ignore_permissions=True)
	frappe.db.commit()

	return {"application_id": application.application_id, "application_name": application.name}


@frappe.whitelist()
def get_my_applications():
	"""Applications belonging to the current logged-in candidate —
	server-side scoped via the Candidate's email == session user.
	"""
	candidate = frappe.db.get_value("Candidate", {"email": frappe.session.user}, "name")
	if not candidate:
		return []

	return frappe.get_all(
		"Application",
		filters={"candidate": candidate},
		fields=["name", "application_id", "job_opening", "status", "application_date"],
		order_by="creation desc",
	)


@frappe.whitelist()
def get_application_status(application_name):
	"""Candidate-facing status view — deliberately excludes internal
	notes, interviewer feedback, compensation and other confidential
	data per brief §25/§42. has_permission on Application (wired via
	hooks.py) already enforces that only the owning candidate (or staff)
	can reach this; this function further trims the response shape.
	"""
	app = frappe.get_doc("Application", application_name)  # raises PermissionError if not allowed

	job = frappe.db.get_value(
		"Job Opening", app.job_opening, ["job_title", "department", "track"], as_dict=True
	)

	interviews = frappe.get_all(
		"Interview",
		filters={"application": application_name},
		fields=["round_type", "status", "scheduled_datetime", "mode", "meeting_link", "rsvp_status"],
		order_by="scheduled_datetime asc",
	)

	offer = frappe.db.get_value(
		"Offer Appointment Order",
		{"application": application_name},
		["status", "acceptance_deadline", "candidate_confirmed_doj"],
		as_dict=True,
	)

	doc_collection = frappe.db.get_value(
		"Document Collection", {"application": application_name}, "overall_status"
	)

	return {
		"application_id": app.application_id,
		"status": app.status,
		"job_title": job.job_title if job else None,
		"department": job.department if job else None,
		"application_date": app.application_date,
		"interviews": interviews,
		"offer_status": offer.status if offer else None,
		"acceptance_deadline": offer.acceptance_deadline if offer else None,
		"document_status": doc_collection,
	}


@frappe.whitelist()
def delete_application(application):
	"""Deletes an Application. delete_doc enforces delete permission on
	its own — only Pathways Admin/System Manager hold delete on this
	doctype (see application.json); Recruiter naturally gets a
	PermissionError here without any extra check.
	"""
	frappe.delete_doc("Application", application)
	return {"deleted": application}


@frappe.whitelist()
def withdraw_application(application_name):
	app = frappe.get_doc("Application", application_name)  # permission-checked
	candidate_email = frappe.db.get_value("Candidate", app.candidate, "email")
	if frappe.session.user != candidate_email and "Pathways Admin" not in frappe.get_roles():
		frappe.throw("You are not authorised to withdraw this application.")

	app.status = "Withdrawn"
	app.save(ignore_permissions=True)
	frappe.db.commit()
	return app.status
