# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Tagging colleagues on a job (workflow step 7: "tag the relevant people").

A tagged colleague is listed in the job's "Shared with" table. They hold
the Pathways Tagged Colleague role, which by itself grants nothing beyond
read on the jobs they are tagged on and those jobs' applications and
documents (row-level rules in pathways.permissions). The role is added on
the first tag and removed once they are no longer tagged anywhere, so the
table stays the single source of truth."""

import frappe

from pathways.permissions import TAGGED_ROLE


def grant_tagged_role(user):
	if not frappe.db.exists("Role", TAGGED_ROLE):
		return
	doc = frappe.get_doc("User", user)
	if TAGGED_ROLE not in [r.role for r in doc.roles]:
		doc.append("roles", {"role": TAGGED_ROLE})
		doc.save(ignore_permissions=True)


def revoke_tagged_role_if_unused(user):
	if frappe.db.exists("Job Opening Colleague", {"user": user, "parenttype": "Job Opening"}):
		return
	doc = frappe.get_doc("User", user)
	if TAGGED_ROLE in [r.role for r in doc.roles]:
		doc.remove_roles(TAGGED_ROLE)


def notify_tagged(job, row):
	from pathways.utils.communication import job_email_context, send_event

	context = job_email_context(job)
	context.update(
		{
			"access_note": row.access_note or "",
			"tagged_by": frappe.utils.get_fullname(row.tagged_by or frappe.session.user),
			"applications_link": frappe.utils.get_url(f"/pathways/applications?job={job.name}"),
		}
	)
	send_event("colleague_tagged", "Job Opening", job.name, context, approvers=[row.user])
