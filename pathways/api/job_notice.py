# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""The official notification for a Job Opening and its corrigenda
(workflow steps 4-5), for the Job Opening page and the public posting.

A job has one Recruitment Notification (number, date, link, PDF). Its
closing date always follows the job's Application Deadline, which is what
actually opens and closes applications; a "Closing Date" Corrigendum moves
that deadline (see Corrigendum.extend_deadline)."""

import frappe
from frappe import _

from pathways.permissions import has_duty

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
