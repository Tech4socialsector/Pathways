# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Regret after the final interview (workflow step 32).

Interviewed candidates the committee did not select get one regret, sent
together from the consolidated score sheet once the decisions are made,
never automatically on "Not selected" (the decision can still change).
Waitlisted candidates are held back while the waitlist may still be used:
they are included once the job is Filled or Cancelled (the waitlist is
released), or when the recruitment team ticks "include waitlisted".

interview_regret_sent_on guards against a second regret; it is separate
from regret_sent_on, which belongs to the screening regret."""

import frappe
from frappe import _
from frappe.utils import cint

from pathways.api.interviews import _can_manage

EVENT = "regret_after_interview"
# The post is taken (or will not be): nobody is held on the waitlist any more.
WAITLIST_RELEASED = ("Filled", "Cancelled")
# A Not selected / waitlisted candidate whose application has since moved
# on (e.g. selected from the waitlist, or withdrew) never gets a regret.
REGRET_FROM = ("Interview Scheduled", "Interview Completed", "Not Selected")


def _require_manage():
	if not _can_manage():
		frappe.throw(_("Only the recruitment team can send post-interview regrets."), frappe.PermissionError)


def waitlist_released(job_opening):
	return frappe.db.get_value("Job Opening", job_opening, "status") in WAITLIST_RELEASED


def _interviewed(job_opening):
	"""Applications of the job whose final interview is completed."""
	return set(
		frappe.get_all(
			"Interview",
			filters={
				"round_type": "Final",
				"status": "Completed",
				"application": ["in", frappe.get_all("Application", filters={"job_opening": job_opening}, pluck="name") or [""]],
			},
			pluck="application",
		)
	)


def _candidates(job_opening):
	"""Interviewed applications without a post-interview regret yet, as
	{name, application_id, outcome, group}: group is "not_selected" or
	"waitlisted"."""
	interviewed = _interviewed(job_opening)
	if not interviewed:
		return []
	rows = frappe.get_all(
		"Application",
		filters={
			"name": ["in", list(interviewed)],
			"interview_regret_sent_on": ["is", "not set"],
			"status": ["in", REGRET_FROM],
			"selection_outcome": ["in", ["Not Selected", "Waitlisted"]],
		},
		fields=["name", "application_id", "selection_outcome", "status"],
		order_by="application_id asc",
	)
	for r in rows:
		r.group = "waitlisted" if r.selection_outcome == "Waitlisted" else "not_selected"
	return rows


@frappe.whitelist()
def post_interview_regret_pending(job_opening):
	"""Counts for the "Send regrets" button on the consolidated score sheet."""
	_require_manage()
	rows = _candidates(job_opening)
	return {
		"not_selected": sum(1 for r in rows if r.group == "not_selected"),
		"waitlisted": sum(1 for r in rows if r.group == "waitlisted"),
		"waitlist_released": waitlist_released(job_opening),
		"sent": frappe.db.count("Application", {"job_opening": job_opening, "interview_regret_sent_on": ["is", "set"]}),
		"enabled": bool(frappe.db.get_value("Recruitment Email Rule", EVENT, "enabled")),
	}


@frappe.whitelist(methods=["POST"])
def send_post_interview_regrets(job_opening, include_waitlisted=0):
	"""Send the post-interview regret to every interviewed candidate marked
	Not selected who has not had one. Waitlisted candidates are included
	only when the waitlist is released (job Filled or Cancelled) or
	include_waitlisted is set; they are then recorded as Not selected."""
	_require_manage()
	if not frappe.db.get_value("Recruitment Email Rule", EVENT, "enabled"):
		frappe.throw(_("The 'Regret after interview' email is switched off in Email Setup."))
	from pathways.utils.communication import candidate_email_context, send_event

	with_waitlist = cint(include_waitlisted) or waitlist_released(job_opening)
	sent, held = [], 0
	for row in _candidates(job_opening):
		if row.group == "waitlisted" and not with_waitlist:
			held += 1
			continue
		# Re-check under a row lock: two people clicking at once send one regret.
		if frappe.db.get_value("Application", row.name, "interview_regret_sent_on", for_update=True):
			continue
		app = frappe.get_doc("Application", row.name)
		note = _("Post-interview regret email sent by {0}.").format(frappe.utils.get_fullname(frappe.session.user))
		if app.selection_outcome == "Waitlisted":
			# The waitlist is over for this candidate: the record says so too.
			app.selection_outcome = "Not Selected"
			app.selection_decided_on = frappe.utils.now_datetime()
			app.status = "Not Selected"
			app.save(ignore_permissions=True)
			note += " " + _("Released from the waitlist: outcome changed from Waitlisted to Not Selected.")
		app.db_set("interview_regret_sent_on", frappe.utils.now_datetime(), update_modified=False)
		context, candidate = candidate_email_context(app)
		send_event(EVENT, "Application", app.name, context, candidate=candidate)
		app.add_comment("Info", note)
		sent.append(row.name)
	return {"sent": len(sent), "applications": sent, "waitlisted_held": held}


@frappe.whitelist()
def get_post_interview_summary(job_opening):
	"""Both post-interview actions of the consolidated score sheet at once:
	regrets to send and panellists to thank."""
	from pathways.api.honorarium import panel_thanks_pending

	_require_manage()
	return {"regret": post_interview_regret_pending(job_opening), "thanks": panel_thanks_pending(job_opening)}
