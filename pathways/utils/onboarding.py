# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Post-offer onboarding: from "offer accepted" to "joined".

Workflow steps 31 (finalise the joining date, new joiner's report) and 34
(onboarding email with the documents to bring), plus folder 12 (intimation
to IT & Facilities). The offer stage is owned elsewhere; this module only
listens to it (hooks.py doc_events on Offer Appointment Order) so that
accepting an offer, however it happens (portal, Desk, import), starts
onboarding exactly once:

	Offer Accepted  -> Document Collection (checklist) + draft Joining
	                   + "onboarding" email with the portal link
	Joining Confirmed -> IT Facilities Provisioning Request + "it_facilities"
	Joining Joined  -> Application "Joined" + Employee (once documents
	                   are verified; the Employee gate requires it)

Which documents go on the checklist is data: Document Type Master rows
with Used In = Onboarding/Both, optionally limited to a track. Who may
confirm a joining or verify a document is Role Permissions / the
Pathways Settings duty-role tables, never code.
"""

import frappe
from frappe.utils import format_date, format_time, get_url, now_datetime

from pathways.utils.communication import candidate_email_context, send_event

PORTAL_PATH = "/pathways/portal/applications"


def portal_link(application):
	return get_url(f"{PORTAL_PATH}/{application}")


def joining_link(joining):
	return get_url(f"/pathways/joinings/{joining}")


# ------------------------------------------------------------ offer hook


def on_offer_update(doc, method=None):
	"""doc_events: Offer Appointment Order on_update."""
	if doc.status != "Accepted" or not doc.application:
		return
	if not doc.has_value_changed("status"):
		return
	start_onboarding(doc)


def start_onboarding(offer):
	"""Idempotent: safe to call again for the same offer (e.g. from the
	"Start onboarding" button for offers accepted before this existed)."""
	if isinstance(offer, str):
		offer = frappe.get_doc("Offer Appointment Order", offer)
	collection = ensure_document_collection(offer.application)
	joining = ensure_joining(offer)
	if not collection.onboarding_email_sent_on:
		send_onboarding_email(joining)
		collection.db_set("onboarding_email_sent_on", now_datetime(), update_modified=False)
	return {"document_collection": collection.name, "joining": joining.name}


def ensure_document_collection(application):
	name = frappe.db.get_value("Document Collection", {"application": application}, "name")
	if name:
		return frappe.get_doc("Document Collection", name)
	collection = frappe.new_doc("Document Collection")
	collection.application = application
	# The controller fills the checklist from Document Type Master.
	collection.insert(ignore_permissions=True)
	return collection


def ensure_joining(offer):
	name = frappe.db.get_value("Joining", {"application": offer.application}, "name")
	# The date the candidate confirmed on accepting; else the offer's own.
	doj = offer.get("candidate_confirmed_doj") or offer.get("proposed_doj")
	if name:
		joining = frappe.get_doc("Joining", name)
		# A draft follows the date the candidate gave; once staff confirm
		# the date it is theirs to change.
		if joining.status == "Draft" and doj and str(joining.confirmed_doj or "") != str(doj):
			joining.confirmed_doj = doj
			joining.save(ignore_permissions=True)
		return joining
	settings = frappe.get_cached_doc("Pathways Settings")
	joining = frappe.new_doc("Joining")
	joining.application = offer.application
	joining.offer = offer.name
	joining.status = "Draft"
	joining.confirmed_doj = doj
	joining.reporting_location = settings.get("default_reporting_location")
	joining.reporting_time = settings.get("default_reporting_time")
	joining.reporting_manager = offer.get("reporting_to")
	joining.insert(ignore_permissions=True)
	return joining


# ---------------------------------------------------------------- emails


def joining_context(joining):
	context, candidate = candidate_email_context(joining.application)
	context.update(
		{
			"joining_date": format_date(joining.confirmed_doj, "dd MMM yyyy") if joining.confirmed_doj else "",
			"reporting_location": joining.reporting_location or "",
			"reporting_time": _time(joining.reporting_time),
			"portal_link": portal_link(joining.application),
			"department": joining.department or "",
		}
	)
	return context, candidate


def _time(value):
	if not value:
		return ""
	return format_time(value, "h:mm a").lower()


def send_onboarding_email(joining):
	context, candidate = joining_context(joining)
	send_event("onboarding", "Joining", joining.name, context=context, candidate=candidate)


def send_resubmission_email(collection, row):
	context, candidate = candidate_email_context(collection.application)
	context.update(
		{
			"document_name": row.document_type,
			"rejection_reason": row.rejection_reason or "",
			"portal_link": portal_link(collection.application),
		}
	)
	send_event("document_resubmission", "Document Collection", collection.name, context=context, candidate=candidate)


# ------------------------------------------------------- IT & Facilities


def ensure_it_request(joining):
	"""Create or refresh the IT/Facilities request from the joining."""
	context, _candidate = candidate_email_context(joining.application)
	values = {
		"application": joining.application,
		"employee_name": joining.candidate_name or context.get("candidate_name") or joining.application,
		"designation": joining.designation or context.get("job_title"),
		"department": joining.department,
		"date_of_joining": joining.confirmed_doj,
		"reporting_location": joining.reporting_location,
		"personal_email": context.get("candidate_email"),
		"mobile_number": context.get("candidate_mobile"),
	}
	name = joining.it_facilities_request or frappe.db.get_value(
		"IT Facilities Provisioning Request", {"joining": joining.name}, "name"
	)
	if name:
		request = frappe.get_doc("IT Facilities Provisioning Request", name)
		request.update(values)
		request.save(ignore_permissions=True)
	else:
		request = frappe.new_doc("IT Facilities Provisioning Request")
		request.joining = joining.name
		request.update(values)
		request.insert(ignore_permissions=True)
	if joining.it_facilities_request != request.name:
		joining.db_set("it_facilities_request", request.name, update_modified=False)
	return request


def notify_it_facilities(joining, request, updated=False):
	context, _candidate = joining_context(joining)
	context.update(
		{
			"job_title": joining.designation or context.get("job_title"),
			"request_link": get_url("/pathways/it-requests"),
			"updated": updated,
		}
	)
	send_event("it_facilities", "IT Facilities Provisioning Request", request.name, context=context)


def on_it_request_completed(request):
	"""Tell the recruitment team the joiner is set up: an email (Email
	Setup decides who) and a bell notification for whoever confirmed the
	joining."""
	joining = frappe.get_doc("Joining", request.joining)
	context = {
		"candidate_name": request.employee_name,
		"job_title": request.designation or "",
		"joining_date": format_date(request.date_of_joining, "dd MMM yyyy") if request.date_of_joining else "",
		"official_email": request.official_email or "",
		"completed_by": frappe.utils.get_fullname(request.completed_by or frappe.session.user),
		"joining_link": joining_link(joining.name),
	}
	send_event("it_facilities_completed", "Joining", joining.name, context=context)
	users = {u for u in (joining.confirmed_by, joining.owner) if u and u not in ("Administrator", "Guest")}
	users.discard(frappe.session.user)
	if not users:
		return
	try:
		from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification

		enqueue_create_notification(
			list(users),
			{
				"type": "Alert",
				"document_type": "Joining",
				"document_name": joining.name,
				"subject": f"IT & Facilities ready for {request.employee_name}",
				"from_user": frappe.session.user,
			},
		)
	except Exception:
		frappe.log_error(title=f"Pathways IT completion notification failed for {request.name}")


# ---------------------------------------------------------------- joined


def set_application_status(application, status):
	"""Status change with an Application Status History row, without
	running the Application's own validation (it may predate today's
	form rules)."""
	previous = frappe.db.get_value("Application", application, "status")
	if previous == status:
		return
	frappe.db.set_value("Application", application, "status", status)
	history = frappe.new_doc("Application Status History")
	history.application = application
	history.previous_status = previous
	history.new_status = status
	history.changed_by = frappe.session.user
	history.changed_on = now_datetime()
	history.source = "System"
	history.insert(ignore_permissions=True)


def on_joined(joining):
	set_application_status(joining.application, "Joined")
	ensure_employee(joining)


def ensure_employee(joining):
	"""Create the pathways Employee once the joiner has joined and every
	mandatory document is verified (the Employee doctype's own gate).
	Returns the Employee name, or None when documents are still pending:
	verifying the last document then creates it."""
	if joining.status != "Joined":
		return None
	existing = joining.employee or frappe.db.get_value("Employee", {"source_application": joining.application}, "name")
	if existing:
		if joining.employee != existing:
			joining.db_set("employee", existing, update_modified=False)
		return existing
	if frappe.db.get_value("Document Collection", {"application": joining.application}, "overall_status") != "Complete":
		return None

	app = frappe.db.get_value("Application", joining.application, ["candidate", "job_opening"], as_dict=True)
	candidate = frappe.db.get_value("Candidate", app.candidate, ["full_name", "email"], as_dict=True) or {}
	job = frappe.db.get_value(
		"Job Opening", app.job_opening, ["designation", "department", "employment_type"], as_dict=True
	) or {}
	employee = frappe.new_doc("Employee")
	employee.employee_name = candidate.get("full_name") or joining.candidate_name
	employee.designation = job.get("designation")
	employee.department = job.get("department")
	employee.date_of_joining = joining.actual_joining_date or joining.confirmed_doj
	employee.employment_type = job.get("employment_type") or None
	employee.status = "Active"
	employee.source_application = joining.application
	if candidate.get("email") and frappe.db.exists("User", candidate.get("email")):
		employee.user = candidate.get("email")
	employee.insert(ignore_permissions=True)
	joining.db_set("employee", employee.name, update_modified=False)
	return employee.name
