# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Joinings page (workflow step 31: finalise the joining date with the
selected candidate, new joiner's report).

Who may see or change a joining is Role Permissions on the Joining
DocType (plus the candidate row rule in pathways.permissions); nothing
here names a role.
"""

import frappe
from frappe import _

from pathways.utils import onboarding

EDITABLE = (
	"confirmed_doj",
	"reporting_location",
	"reporting_time",
	"reporting_manager",
	"reschedule_reason",
	"bio_writeup_attachment",
	"directory_photo_attachment",
	"remarks",
)
STATUSES = ("Draft", "Confirmed", "Joined", "No-show")


@frappe.whitelist()
def list_joinings():
	"""Joinings plus accepted offers that have none yet (accepted before
	onboarding was automatic), so staff can start those."""
	rows = frappe.get_list(
		"Joining",
		fields=[
			"name", "application", "candidate_name", "designation", "department", "status", "confirmed_doj",
			"reporting_location", "reporting_time", "reporting_manager", "reschedule_count", "it_facilities_request", "employee",
		],
		order_by="confirmed_doj desc, modified desc",
		limit_page_length=0,
	)
	apps = [r.application for r in rows]
	ids = {a.name: a.application_id for a in frappe.get_all("Application", filters={"name": ["in", apps or [""]]}, fields=["name", "application_id"])}
	docs = {d.application: d.overall_status for d in frappe.get_all("Document Collection", filters={"application": ["in", apps or [""]]}, fields=["application", "overall_status"])}
	it = {
		r.name: r.status
		for r in frappe.get_all(
			"IT Facilities Provisioning Request",
			filters={"name": ["in", [r.it_facilities_request for r in rows if r.it_facilities_request] or [""]]},
			fields=["name", "status"],
		)
	}
	for r in rows:
		r.application_id = ids.get(r.application) or r.application
		r.document_status = docs.get(r.application) or "Not started"
		r.it_status = it.get(r.it_facilities_request) or ""

	pending = []
	if frappe.has_permission("Joining", "create"):
		have = set(apps) | set(frappe.get_all("Joining", pluck="application"))
		for offer in frappe.get_all(
			"Offer Appointment Order",
			filters={"status": "Accepted"},
			fields=["name", "application", "candidate_confirmed_doj"],
		):
			if offer.application in have:
				continue
			app = frappe.db.get_value("Application", offer.application, ["application_id", "candidate"], as_dict=True) or {}
			pending.append(
				{
					"offer": offer.name,
					"application": offer.application,
					"application_id": app.get("application_id"),
					"candidate_name": frappe.db.get_value("Candidate", app.get("candidate"), "full_name") if app else "",
					"candidate_confirmed_doj": offer.candidate_confirmed_doj,
				}
			)
	return {"joinings": rows, "pending_offers": pending}


@frappe.whitelist()
def start_onboarding(offer):
	"""Backfill for an offer accepted before onboarding was automatic."""
	if not frappe.has_permission("Joining", "create"):
		frappe.throw(_("You are not allowed to create joinings."), frappe.PermissionError)
	if frappe.db.get_value("Offer Appointment Order", offer, "status") != "Accepted":
		frappe.throw(_("Onboarding starts only once the offer has been accepted."))
	return onboarding.start_onboarding(offer)


@frappe.whitelist()
def get_joining(name):
	doc = frappe.get_doc("Joining", name)
	doc.check_permission("read")
	app = frappe.db.get_value("Application", doc.application, ["application_id", "candidate", "job_opening", "status"], as_dict=True) or {}
	candidate = frappe.db.get_value("Candidate", app.get("candidate"), ["full_name", "email", "mobile_number"], as_dict=True) or {}
	collection = frappe.db.get_value(
		"Document Collection", {"application": doc.application}, ["name", "overall_status", "onboarding_email_sent_on"], as_dict=True
	)
	it_request = None
	if doc.it_facilities_request:
		it_request = frappe.db.get_value(
			"IT Facilities Provisioning Request",
			doc.it_facilities_request,
			["name", "status", "laptop_arranged", "official_email_created", "official_email", "access_card_issued", "seating_arranged", "completed_on"],
			as_dict=True,
		)
	return {
		**doc.as_dict(),
		"application_id": app.get("application_id"),
		"application_status": app.get("status"),
		"job_title": frappe.db.get_value("Job Opening", app.get("job_opening"), "job_title") if app.get("job_opening") else "",
		"candidate_email": candidate.get("email"),
		"candidate_mobile": candidate.get("mobile_number"),
		"document_collection": collection,
		"it_request": it_request,
		"confirmed_by_name": frappe.utils.get_fullname(doc.confirmed_by) if doc.confirmed_by else "",
		"can_write": bool(doc.has_permission("write")),
	}


@frappe.whitelist()
def save_joining(name, values):
	doc = frappe.get_doc("Joining", name)
	doc.check_permission("write")
	values = frappe.parse_json(values) or {}
	for field in EDITABLE:
		if field in values:
			doc.set(field, values.get(field) or None)
	doc.save()
	return get_joining(name)


@frappe.whitelist()
def set_status(name, status, values=None):
	"""Confirm / mark Joined / No-show / back to Draft. `values` may carry
	the edited fields so "Save & confirm" is one step."""
	if status not in STATUSES:
		frappe.throw(_("Unknown status {0}.").format(status))
	doc = frappe.get_doc("Joining", name)
	doc.check_permission("write")
	values = frappe.parse_json(values) if values else {}
	for field in EDITABLE:
		if field in values:
			doc.set(field, values.get(field) or None)
	doc.status = status
	doc.save()
	return get_joining(name)
