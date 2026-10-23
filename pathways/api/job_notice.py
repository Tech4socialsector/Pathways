# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""The official notification for a Job Opening and its corrigenda
(workflow steps 4-5), for the Job Opening page and the public posting.

A job has one Recruitment Notification (number, date, link, PDF). Its
closing date always follows the job's Application Deadline, which is what
actually opens and closes applications; a "Closing Date" Corrigendum moves
that deadline (see Corrigendum.extend_deadline).

Also the rest of step 3 and step 6 around the notification: asking the
Registrar's Office and Communications for the official notification once
the Green Sheet is approved, the publishing tracker (website, LinkedIn,
Indeed) that Communications fills in, and closing the notification and
asking for the ad to be taken down when the job closes."""

import frappe
from frappe import _

from pathways.permissions import has_duty

PUBLISHING_FIELDS = (
	"website_url",
	"website_published_on",
	"linkedin_url",
	"linkedin_published_on",
	"indeed_url",
	"indeed_published_on",
	"published_by",
)
NOTICE_FIELDS = ("notification_number", "publish_date", "notification_url", "notification_attachment")
CORRIGENDUM_FIELDS = (
	"name",
	"corrigendum_date",
	"changed_field",
	"previous_value",
	"new_value",
	"remarks",
	"corrigendum_attachment",
	"signed_by",
)


def _notification_name(job_opening):
	return frappe.db.get_value("Recruitment Notification", {"job_opening": job_opening}, "name", order_by="creation desc")


def notice_for(job_opening):
	"""{notification, corrigenda} — no permission check; callers decide."""
	name = _notification_name(job_opening)
	notification = frappe.db.get_value("Recruitment Notification", name, NOTICE_FIELDS, as_dict=True) if name else None
	corrigenda = frappe.get_all(
		"Corrigendum",
		filters={"job_opening": job_opening},
		fields=list(CORRIGENDUM_FIELDS),
		order_by="creation desc",
	)
	for row in corrigenda:
		row["signed_by_name"] = frappe.utils.get_fullname(row.signed_by) if row.signed_by else None
	return {"notification": notification, "corrigenda": corrigenda}


@frappe.whitelist()
def get_job_notice(job_opening):
	frappe.get_doc("Job Opening", job_opening).check_permission("read")
	out = notice_for(job_opening)
	out["can_edit"] = bool(frappe.has_permission("Job Opening", "write", doc=job_opening))
	out["can_issue_corrigendum"] = has_duty("corrigendum_signer_roles")
	job = frappe.db.get_value("Job Opening", job_opening, ["status", *PUBLISHING_FIELDS], as_dict=True)
	out["publishing"] = {f: job.get(f) for f in PUBLISHING_FIELDS}
	if job.published_by:
		out["publishing"]["published_by_name"] = frappe.utils.get_fullname(job.published_by)
	out["can_edit_publishing"] = can_edit_publishing(job_opening)
	return out


@frappe.whitelist(methods=["POST"])
def save_job_notice(job_opening, data):
	job = frappe.get_doc("Job Opening", job_opening)
	job.check_permission("write")
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = _notification_name(job_opening)
	doc = frappe.get_doc("Recruitment Notification", name) if name else frappe.new_doc("Recruitment Notification")
	doc.job_opening = job_opening
	doc.update({field: data.get(field) or None for field in NOTICE_FIELDS})
	doc.closing_datetime = job.application_deadline
	doc.status = "Published" if job.status == "Advertised" else "Closed" if job.status in ("Closed", "Filled", "Cancelled") else "Draft"
	doc.save(ignore_permissions=True)
	return get_job_notice(job_opening)


@frappe.whitelist(methods=["POST"])
def issue_corrigendum(job_opening, changed_field, new_value=None, remarks=None, corrigendum_attachment=None):
	"""Issue a corrigendum. Closing Date: extends the job's deadline (and
	re-advertises a job that already auto-closed). Other: recorded and
	published with its PDF. Corrigendum.validate enforces the signer roles."""
	job = frappe.get_doc("Job Opening", job_opening)
	job.check_permission("read")
	if changed_field not in ("Closing Date", "Other"):
		frappe.throw(_("Choose what the corrigendum changes."))
	if changed_field == "Other" and not (remarks or "").strip():
		frappe.throw(_("Describe what the corrigendum changes."))

	notification = _notification_name(job_opening)
	if not notification:
		notification = (
			frappe.get_doc(
				{
					"doctype": "Recruitment Notification",
					"job_opening": job_opening,
					"closing_datetime": job.application_deadline,
					"status": "Published" if job.status == "Advertised" else "Draft",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	frappe.get_doc(
		{
			"doctype": "Corrigendum",
			"recruitment_notification": notification,
			"job_opening": job_opening,
			"corrigendum_date": frappe.utils.today(),
			"changed_field": changed_field,
			"new_value": new_value if changed_field == "Closing Date" else (remarks or "").strip()[:140],
			"remarks": remarks,
			"corrigendum_attachment": corrigendum_attachment,
		}
	).insert(ignore_permissions=True)
	return get_job_notice(job_opening)


# ------------------------------------------------------------- publishing


def can_edit_publishing(job_opening):
	"""Whoever may edit the job, or the notification (Communications and the
	Registrar's Office by default: Role Permissions on Recruitment Notification)."""
	return bool(
		frappe.has_permission("Job Opening", "write", doc=job_opening)
		or frappe.has_permission("Recruitment Notification", "write")
	)


@frappe.whitelist(methods=["POST"])
def save_publishing(job_opening, data):
	"""Where and when the ad went live (workflow step 3). Saved with db_set:
	Communications usually has only read on Job Opening, and these fields
	change nothing else about the job."""
	job = frappe.get_doc("Job Opening", job_opening)
	job.check_permission("read")
	if not can_edit_publishing(job_opening):
		frappe.throw(_("You cannot update where this job is published."), frappe.PermissionError)
	if isinstance(data, str):
		data = frappe.parse_json(data)

	updates = {f: (data.get(f) or None) for f in PUBLISHING_FIELDS if f in data and f != "published_by"}
	for field in ("website_url", "linkedin_url", "indeed_url"):
		url = updates.get(field)
		if url and not url.lower().startswith(("http://", "https://")):
			frappe.throw(_("{0} must be a full link starting with https://").format(job.meta.get_label(field)))
	if any(updates.values()):
		updates["published_by"] = data.get("published_by") or job.published_by or frappe.session.user
	if updates:
		job.db_set(updates, notify=True)
		job.add_comment("Info", _("Publishing details updated."))
	return get_job_notice(job_opening)


# --------------------------------------------- notification lifecycle hooks


def request_official_notification(job_opening, green_sheet=None):
	"""Green Sheet approved (workflow step 3): ask the Registrar's Office and
	Communications to turn the draft into the official notification."""
	from pathways.utils.communication import job_email_context, send_event

	job = frappe.get_doc("Job Opening", job_opening)
	context = job_email_context(job)
	jd = job.jd_attachment or (frappe.db.get_value("Pre-Recruitment Green Sheet", green_sheet, "jd_attachment") if green_sheet else None)
	context.update(
		{
			"green_sheet": green_sheet or job.pre_recruitment_green_sheet or "",
			"jd_link": frappe.utils.get_url(jd) if jd else "",
			"track": job.track or "",
		}
	)
	send_event("notification_requested", "Job Opening", job.name, context, job_opening=job.name)


def sync_notification_status(job, previous_status=None):
	"""Keep the job's Recruitment Notification(s) in step with the job:
	Published while Advertised, Closed once it stops being advertised."""
	if job.status == "Advertised" and previous_status != "Advertised":
		for name in frappe.get_all(
			"Recruitment Notification", filters={"job_opening": job.name, "status": ["!=", "Published"]}, pluck="name"
		):
			frappe.db.set_value("Recruitment Notification", name, "status", "Published")
	elif previous_status == "Advertised" and job.status in ("Closed", "Filled", "Cancelled"):
		close_advertisement(job.name)


def close_advertisement(job_opening):
	"""The job stopped taking applications (workflow step 6): close its
	notification(s) and ask Communications and the recruiters to take the ad
	down. Callers call this once per Advertised -> closed transition."""
	from pathways.utils.communication import job_email_context, send_event

	for name in frappe.get_all(
		"Recruitment Notification", filters={"job_opening": job_opening, "status": ["!=", "Closed"]}, pluck="name"
	):
		frappe.db.set_value("Recruitment Notification", name, "status", "Closed")

	job = frappe.get_doc("Job Opening", job_opening)
	context = job_email_context(job)
	context.update(
		{
			"application_count": frappe.db.count("Application", {"job_opening": job.name, "status": ["!=", "Withdrawn"]}),
			"published_links": [
				{"label": label, "url": job.get(field)}
				for label, field in (("NLSIU website", "website_url"), ("LinkedIn", "linkedin_url"), ("Indeed", "indeed_url"))
				if job.get(field)
			],
		}
	)
	send_event("ad_closed", "Job Opening", job.name, context, job_opening=job.name)
