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


# ------------------------------------------------------------ Selection module
#
# The recruitment team's view of everything after the final interviews, per
# job: scores and decisions, regrets and panel thanks, the Selection (Post-
# Interview) Green Sheet and the offers. The Interview Panel stays the
# panellists' area for scoring.

STEPS = ("scores", "regrets", "green_sheet", "offers")
LIVE_SHEET = ("Draft", "Under Approval", "Returned for Revision", "Approved")


def _final_interviews(job_opening=None):
	filters = {"round_type": "Final", "status": ["!=", "Cancelled"]}
	rows = frappe.get_all(
		"Interview",
		filters=filters,
		fields=["name", "application", "status", "application.job_opening as job_opening"],
	)
	return [r for r in rows if r.job_opening and (not job_opening or r.job_opening == job_opening)]


def _job_summary(job, interviews):
	"""Where one job stands after its final interviews, and which step is next."""
	from pathways.api.honorarium import panel_thanks_pending

	apps = sorted({iv.application for iv in interviews})
	committee = frappe.db.get_value("Selection Committee", {"job_opening": job.name}, "name")
	panel_size = frappe.db.count("Committee Member Row", {"parent": committee, "parenttype": "Selection Committee"}) if committee else 0
	scored_by = {}
	for a in frappe.get_all("Interview Assessment", filters={"interview": ["in", [iv.name for iv in interviews] or [""]]}, fields=["interview"]):
		scored_by[a.interview] = scored_by.get(a.interview, 0) + 1
	fully_scored = sum(1 for iv in interviews if panel_size and scored_by.get(iv.name, 0) >= panel_size)

	outcomes = {"Selected": 0, "Waitlisted": 0, "Not Selected": 0}
	for o in frappe.get_all("Application", filters={"name": ["in", apps or [""]]}, pluck="selection_outcome"):
		if o in outcomes:
			outcomes[o] += 1
	undecided = len(apps) - sum(outcomes.values())

	pending = _candidates(job.name)
	regrets = {
		"pending": sum(1 for r in pending if r.group == "not_selected"),
		"waitlisted": sum(1 for r in pending if r.group == "waitlisted"),
		"sent": frappe.db.count("Application", {"job_opening": job.name, "interview_regret_sent_on": ["is", "set"]}),
	}
	thanks = panel_thanks_pending(job.name)

	sheet = frappe.db.get_value(
		"Post-Interview Green Sheet",
		{"job_opening": job.name, "docstatus": ["!=", 2]},
		["name", "status"],
		as_dict=True,
		order_by="creation desc",
	)
	offers = frappe.get_all(
		"Offer Appointment Order", filters={"application": ["in", apps or [""]]}, fields=["name", "application", "status"]
	)
	offer_counts = {}
	for o in offers:
		offer_counts[o.status] = offer_counts.get(o.status, 0) + 1

	done = {
		"scores": bool(apps) and undecided == 0,
		"regrets": bool(apps) and undecided == 0 and regrets["pending"] == 0 and (not thanks["committee"] or thanks["pending"] == 0),
		"green_sheet": bool(sheet) and sheet.status == "Approved",
		"offers": outcomes["Selected"] > 0 and offer_counts.get("Accepted", 0) >= outcomes["Selected"],
	}
	if not outcomes["Selected"]:
		# Nobody selected: there is no green sheet or offer to prepare.
		done["green_sheet"] = done["offers"] = done["scores"]
	next_step = next((s for s in STEPS if not done[s]), None)

	return {
		"name": job.name,
		"job_title": job.job_title,
		"position": job.position,
		"track": job.track,
		"employment_type": job.employment_type,
		"job_status": job.status,
		"candidates": len(apps),
		"panel_size": panel_size,
		"fully_scored": fully_scored,
		"outcomes": outcomes,
		"undecided": undecided,
		"regrets": regrets,
		"thanks": {"pending": thanks["pending"], "panel_size": thanks["panel_size"], "committee": thanks["committee"]},
		"green_sheet": sheet,
		"offers": {"total": len(offers), **offer_counts},
		"done": done,
		"next_step": next_step,
	}


def _jobs(names):
	return frappe.get_all(
		"Job Opening",
		filters={"name": ["in", list(names) or [""]]},
		fields=["name", "job_title", "position", "track", "employment_type", "status", "modified"],
	)


@frappe.whitelist()
def list_selection_jobs():
	"""Selection module list: every job with final interviews, with its
	progress through the post-interview steps."""
	_require_manage()
	interviews = _final_interviews()
	by_job = {}
	for iv in interviews:
		by_job.setdefault(iv.job_opening, []).append(iv)
	rows = [_job_summary(job, by_job[job.name]) for job in _jobs(by_job)]
	# Unfinished work first, then by job title.
	rows.sort(key=lambda r: (r["next_step"] is None, r["job_title"] or ""))
	return rows


@frappe.whitelist()
def get_selection_job(job_opening):
	"""Selection module job page: the summary, plus the selected and
	waitlisted candidates with their offers (the Offers step)."""
	_require_manage()
	job = _jobs([job_opening])
	if not job:
		frappe.throw(_("Job Opening {0} not found.").format(job_opening))
	interviews = _final_interviews(job_opening)
	summary = _job_summary(job[0], interviews)
	apps = frappe.get_all(
		"Application",
		filters={"name": ["in", sorted({iv.application for iv in interviews}) or [""]], "selection_outcome": ["in", ["Selected", "Waitlisted"]]},
		fields=["name", "application_id", "candidate", "selection_outcome", "status"],
		order_by="selection_outcome asc, application_id asc",
	)
	names = dict(frappe.get_all("Candidate", filters={"name": ["in", [a.candidate for a in apps] or [""]]}, fields=["name", "full_name"], as_list=True))
	offers = {
		o.application: o
		for o in frappe.get_all(
			"Offer Appointment Order",
			filters={"application": ["in", [a.name for a in apps] or [""]]},
			fields=["name", "application", "status", "candidate_confirmed_doj"],
			order_by="creation asc",
		)
	}
	summary["candidates_for_offer"] = [
		{
			"application": a.name,
			"application_id": a.application_id,
			"candidate_name": names.get(a.candidate) or a.candidate,
			"outcome": a.selection_outcome,
			"application_status": a.status,
			"offer": offers.get(a.name),
		}
		for a in apps
	]
	return summary
