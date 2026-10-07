# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from pathways.utils.approval import (
	APPROVABLE_DOCTYPES,
	get_chain_status,
	get_pending_for_user,
)
from pathways.utils.approval import (
	record_approval_action as _record_approval_action,
)


@frappe.whitelist()
def get_my_pending_approvals():
	"""Documents currently sitting at an approval step this user may act on
	— backs the "My Approvals" page. Who that is comes entirely from the
	Approval Chain Templates and Pathways Settings."""
	return get_pending_for_user()


@frappe.whitelist()
def record_approval_action(doctype, docname, action, remarks=None, channel="Digital"):
	return _record_approval_action(doctype, docname, action, remarks, channel)


@frappe.whitelist()
def get_approval_chain_status(doctype, docname):
	if doctype not in APPROVABLE_DOCTYPES:
		frappe.throw(_("{0} is not an approvable document type.").format(doctype))

	# frappe.get_doc() does not check permissions on its own; without this
	# a Candidate or unrelated staff role could read any Green Sheet.
	doc = frappe.get_doc(doctype, docname)
	doc.check_permission("read")
	return get_chain_status(doc)


# Fields the review dialog shows elsewhere (job summary, chain) or never.
_REVIEW_SKIP = {"naming_series", "job_opening", "track", "approval_chain_template", "current_approval_level", "status", "amended_from"}
_JOB_SUMMARY = ("job_title", "position", "department", "designation", "employment_type", "vacancies", "pay_level", "tenure_description", "application_deadline", "status")


@frappe.whitelist()
def get_approval_document(doctype, docname):
	"""Everything an approver needs to decide, for the My Approvals review
	dialog: the job, the document's own fields and files, and the chain."""
	if doctype not in APPROVABLE_DOCTYPES:
		frappe.throw(_("{0} is not an approvable document type.").format(doctype))
	doc = frappe.get_doc(doctype, docname)
	doc.check_permission("read")

	job = None
	if doc.get("job_opening"):
		values = frappe.db.get_value("Job Opening", doc.job_opening, _JOB_SUMMARY, as_dict=True) or {}
		meta = frappe.get_meta("Job Opening")
		job = {
			"name": doc.job_opening,
			"title": values.get("job_title"),
			"fields": [
				{"label": _(meta.get_label(f)), "value": frappe.format(values.get(f), meta.get_field(f))}
				for f in _JOB_SUMMARY
				if f != "job_title" and values.get(f) not in (None, "")
			],
		}

	fields, files, tables = [], [], []
	for df in frappe.get_meta(doctype).fields:
		if df.fieldname in _REVIEW_SKIP or df.fieldtype in ("Section Break", "Column Break", "Tab Break"):
			continue
		value = doc.get(df.fieldname)
		if df.fieldtype == "Table":
			if df.fieldname in ("approval_steps", "approval_log") or not value:
				continue
			child = frappe.get_meta(df.options)
			cols = [c for c in child.fields if c.in_list_view] or [c for c in child.fields if c.fieldtype not in ("Section Break", "Column Break")][:5]
			tables.append(
				{
					"label": _(df.label),
					"columns": [_(c.label) for c in cols],
					"rows": [[frappe.format(row.get(c.fieldname), c) for c in cols] for row in value],
				}
			)
		elif df.fieldtype in ("Attach", "Attach Image"):
			files.append({"label": _(df.label), "url": value})
		elif value not in (None, ""):
			display = frappe.format(value, df)
			if df.fieldtype == "Link" and df.options == "Application":
				display = f"{value} · {_candidate_name(value)}".strip(" ·")
			fields.append({"label": _(df.label), "value": display, "html": df.fieldtype in ("Text Editor", "HTML Editor")})

	return {
		"doctype": doctype,
		"name": doc.name,
		"raised_by": frappe.utils.get_fullname(doc.owner),
		"raised_on": doc.creation,
		"job": job,
		"fields": fields,
		"files": files,
		"tables": tables,
		"chain": get_chain_status(doc),
	}


def _candidate_name(application):
	candidate = frappe.db.get_value("Application", application, "candidate")
	return (candidate and frappe.db.get_value("Candidate", candidate, "full_name")) or ""
