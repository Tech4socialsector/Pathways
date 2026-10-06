# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime, today

from pathways.permissions import CANDIDATE_ROLE, has_full_access
from pathways.utils.application_form import get_form_config, is_accepting_applications, validate_submission

PUBLIC_JOB_FIELDS = (
	"name",
	"job_title",
	"track",
	"department",
	"designation",
	"vacancies",
	"employment_type",
	"tenure_description",
	"pay_level",
	"application_deadline",
)


@frappe.whitelist(allow_guest=True)
def get_open_job_openings(track=None, department=None, search=None):
	"""Public job board: Advertised jobs whose deadline has not passed."""
	filters = [["status", "=", "Advertised"]]
	if track:
		filters.append(["track", "=", track])
	if department:
		filters.append(["department", "=", department])
	if search:
		filters.append(["job_title", "like", f"%{search}%"])

	jobs = frappe.get_all("Job Opening", filters=filters, fields=list(PUBLIC_JOB_FIELDS), order_by="creation desc")
	now = now_datetime()
	return [j for j in jobs if not j.application_deadline or frappe.utils.get_datetime(j.application_deadline) > now]


def _get_public_job(job_opening):
	if not frappe.db.exists("Job Opening", job_opening):
		frappe.throw(_("This position does not exist."), frappe.DoesNotExistError)
	job = frappe.get_doc("Job Opening", job_opening)
	if job.status != "Advertised":
		frappe.throw(_("This position is not currently open for applications."), frappe.DoesNotExistError)
	return job


def _current_candidate():
	user = frappe.session.user
	if user == "Guest":
		return None
	return frappe.db.get_value(
		"Candidate",
		{"email": user},
		["name", "full_name", "mobile_number", "date_of_birth", "gender", "address"],
		as_dict=True,
	)


@frappe.whitelist(allow_guest=True)
def get_job_opening_detail(job_opening):
	"""Public job detail plus the application form this job asks for."""
	job = _get_public_job(job_opening)
	detail = {field: job.get(field) for field in PUBLIC_JOB_FIELDS}
	detail.update({"jd_text": job.jd_text, "jd_attachment": job.jd_attachment})
	detail["form"] = get_form_config(job)

	user = frappe.session.user
	detail["viewer"] = {"logged_in": user != "Guest", "email": None, "is_staff": False, "already_applied": None}
	if user != "Guest":
		candidate = _current_candidate()
		detail["viewer"].update(
			{
				"email": user,
				"is_staff": frappe.db.get_value("User", user, "user_type") == "System User",
				"profile": candidate,
				"already_applied": candidate
				and frappe.db.get_value(
					"Application",
					{"candidate": candidate.name, "job_opening": job.name, "status": ["!=", "Withdrawn"]},
					"application_id",
				),
			}
		)
	return detail


@frappe.whitelist(methods=["POST"])
def submit_application(job_opening, data):
	"""Submit an application as the logged-in candidate.

	The candidate is always the session user — never an email typed into
	the form — so nobody can apply in someone else's name, and the
	"only once per position" rule is enforced per account under a row lock.
	"""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Please log in to apply."), frappe.PermissionError)
	if frappe.db.get_value("User", user, "user_type") != "Website User":
		frappe.throw(_("Staff accounts cannot apply. Please register with a personal email address."))

	if isinstance(data, str):
		data = frappe.parse_json(data)

	# Lock the job row: serialises concurrent submissions for this job and
	# makes the deadline/status check authoritative.
	if not frappe.db.exists("Job Opening", job_opening):
		frappe.throw(_("This position does not exist."))
	frappe.db.get_value("Job Opening", job_opening, "name", for_update=True)
	job = frappe.get_doc("Job Opening", job_opening)
	if not is_accepting_applications(job):
		frappe.throw(_("Applications for this position are closed."))

	candidate_name = frappe.db.get_value("Candidate", {"email": user}, "name", for_update=True)
	if candidate_name and frappe.db.exists(
		"Application", {"candidate": candidate_name, "job_opening": job.name, "status": ["!=", "Withdrawn"]}
	):
		frappe.throw(_("You have already applied for this position. An application can be submitted only once."))

	candidate_fields, application_fields, files = validate_submission(job, data, user)

	if candidate_name:
		candidate = frappe.get_doc("Candidate", candidate_name)
		candidate.update(candidate_fields)
		candidate.save(ignore_permissions=True)
	else:
		candidate = frappe.new_doc("Candidate")
		candidate.update(candidate_fields)
		candidate.email = user
		candidate.insert(ignore_permissions=True)

	application = frappe.new_doc("Application")
	application.update(application_fields)
	application.candidate = candidate.name
	application.application_date = today()
	application.status = "Submitted"
	application.insert(ignore_permissions=True)

	# Attach the uploads to the application: staff with access to it can
	# then open these private files; nobody else can.
	for file_name in set(files):
		frappe.db.set_value(
			"File",
			file_name,
			{"attached_to_doctype": "Application", "attached_to_name": application.name},
			update_modified=False,
		)

	if not frappe.db.exists("Has Role", {"parenttype": "User", "parent": user, "role": CANDIDATE_ROLE}):
		user_doc = frappe.get_doc("User", user)
		# roles is a permlevel-1 field: without this flag Frappe silently
		# discards role changes a user makes to their own record.
		user_doc.flags.ignore_permissions = True
		user_doc.add_roles(CANDIDATE_ROLE)

	frappe.enqueue(
		"pathways.api.application.send_acknowledgement",
		application_name=application.name,
		enqueue_after_commit=True,
	)
	return {"application_id": application.application_id, "application_name": application.name}


def send_acknowledgement(application_name):
	from pathways.utils.communication import send_templated_email

	if not frappe.db.exists("Email Template", "Application Acknowledgement"):
		return
	app = frappe.get_doc("Application", application_name)
	candidate = frappe.db.get_value("Candidate", app.candidate, ["full_name", "email"], as_dict=True)
	send_templated_email(
		"Application Acknowledgement",
		candidate.email,
		"Application",
		app.name,
		{
			"candidate_name": candidate.full_name,
			"job_title": frappe.db.get_value("Job Opening", app.job_opening, "job_title"),
			"application_id": app.application_id,
		},
	)


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
	data per brief §25/§42.

	frappe.get_doc() does not auto-check permissions on read (unlike
	doc.save() for writes) — the explicit check_permission call below is
	what actually enforces that only the owning candidate or privileged
	staff (has_application_permission, wired via hooks.py) can reach
	this; this function further trims the response shape on top of that.
	"""
	app = frappe.get_doc("Application", application_name)
	app.check_permission("read")

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


FINAL_STATUSES = ("Withdrawn", "Not Selected", "Joined", "Offer Accepted")


@frappe.whitelist(methods=["POST"])
def withdraw_application(application_name):
	"""The candidate, or staff who may edit every Application, can withdraw."""
	app = frappe.get_doc("Application", application_name)
	app.check_permission("read")
	candidate_email = frappe.db.get_value("Candidate", app.candidate, "email")
	is_owner = frappe.session.user == candidate_email
	if not is_owner and not (has_full_access("Application") and frappe.has_permission("Application", "write")):
		frappe.throw(_("You are not authorised to withdraw this application."), frappe.PermissionError)
	if app.status in FINAL_STATUSES:
		frappe.throw(_("An application that is {0} cannot be withdrawn.").format(_(app.status)))

	app.status = "Withdrawn"
	app.save(ignore_permissions=True)
	return app.status


@frappe.whitelist()
def get_application_detail(application_name):
	"""Full submitted application for staff (and assigned committee members)."""
	app = frappe.get_doc("Application", application_name)
	app.check_permission("read")
	if frappe.db.get_value("User", frappe.session.user, "user_type") != "System User":
		frappe.throw(_("Not permitted."), frappe.PermissionError)

	candidate = frappe.db.get_value(
		"Candidate",
		app.candidate,
		["full_name", "email", "mobile_number", "date_of_birth", "gender", "address"],
		as_dict=True,
	)
	out = app.as_dict(no_default_fields=True)
	out["candidate_details"] = candidate
	out["job_title"] = frappe.db.get_value("Job Opening", app.job_opening, "job_title")
	out["can_write"] = bool(frappe.has_permission("Application", "write", doc=app))
	out["can_delete"] = bool(frappe.has_permission("Application", "delete", doc=app))
	if not has_full_access("Application"):
		# Committee members review merit, not pay.
		for field in ("current_salary", "expected_salary"):
			out.pop(field, None)
	return out
