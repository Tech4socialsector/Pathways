# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Reference checks (workflow step 21).

The recruiter opens the References panel on an application, creates one
Reference Check per referee (prefilled from the referees the candidate gave
in the application) and then either:

	* emails the referee a link to a public form (/pathways/referee/<token>), or
	* phones the referee and records the answers in the same question set.

Why tokens are handled the way they are: the referee is neither a candidate
nor a user, so the link itself is the credential. Only its SHA-256 hash is
stored, the link expires (Pathways Settings > Reference Checks) and accepts
one submission. A reminder re-issues a fresh link but keeps the previous one
working until the same expiry, so the referee can use either email; a
resend by the recruiter (e.g. a corrected email address) replaces both.

Who may do what is Role Permissions on Reference Check: read to see checks
and responses, write to create, send and record. Candidates have no
permission on it, so they never see what their referees said.
"""

import hashlib
import json
import secrets

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import add_days, cint, format_datetime, get_datetime, get_url, now_datetime

from pathways.permissions import has_full_access
from pathways.utils.db import commit

DOCTYPE = "Reference Check"
ANSWER_TYPES = ("Text", "Rating 1-5", "Yes-No")
MAX_ANSWER_LENGTH = 10000
REFEREE_FIELDS = ("referee_name", "referee_designation_org", "relationship_to_candidate", "referee_email", "referee_mobile")
CHECK_FIELDS = (
	"name",
	"application",
	"candidate_name",
	"template",
	*REFEREE_FIELDS,
	"status",
	"mode",
	"requested_by",
	"requested_on",
	"token_expires_on",
	"reminder_sent_on",
	"completed_on",
	"recorded_by",
	"overall_assessment_summary",
)


# ------------------------------------------------------------ permissions


def _can(ptype="read"):
	return bool(frappe.has_permission(DOCTYPE, ptype)) and has_full_access(DOCTYPE)


def _require(ptype="read"):
	if not _can(ptype):
		frappe.throw(_("You do not have permission to manage reference checks."), frappe.PermissionError)


def _get_application(application):
	app = frappe.get_doc("Application", application)
	app.check_permission("read")
	return app


def _get_check(name, ptype="write"):
	_require(ptype)
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission(ptype)
	return doc


# ------------------------------------------------------------ helpers


def _settings_days(fieldname, default):
	value = frappe.get_cached_doc("Pathways Settings").get(fieldname)
	return default if value is None or value == "" else cint(value)


def _hash(token):
	return hashlib.sha256((token or "").encode()).hexdigest()


def _form_link(token):
	return get_url(f"/pathways/referee/{token}")


def _job(application_or_doc):
	app = application_or_doc
	return frappe.db.get_value("Job Opening", app.job_opening, ["name", "job_title", "track"], as_dict=True) or frappe._dict()


def template_for_track(track):
	"""The active template for a track (the most recently updated one)."""
	if not track:
		return None
	names = frappe.get_all(
		"Reference Check Template", filters={"track": track, "is_active": 1}, pluck="name", order_by="modified desc", limit=1
	)
	return names[0] if names else None


def _fill(text, candidate_name, position):
	return (text or "").replace("{candidate_name}", candidate_name or "the candidate").replace("{position}", position or "the post")


def _normalise_email(value):
	value = (value or "").strip()
	if value and not frappe.utils.validate_email_address(value):
		frappe.throw(_("{0} is not a valid email address.").format(value))
	return value


def _new_check(app, referee, template, job):
	"""A Reference Check with the template's questions copied in, so later
	edits to the template do not change checks already in progress."""
	tpl = frappe.get_doc("Reference Check Template", template)
	doc = frappe.new_doc(DOCTYPE)
	doc.application = app.name
	doc.template = template
	doc.status = "Pending"
	for field in REFEREE_FIELDS:
		doc.set(field, (referee.get(field) or "").strip())
	doc.referee_email = _normalise_email(doc.referee_email)
	if not doc.referee_name:
		frappe.throw(_("Enter the referee's name."))
	candidate_name = frappe.db.get_value("Candidate", app.candidate, "full_name")
	doc.candidate_name = candidate_name
	for row in sorted(tpl.questions, key=lambda r: (cint(r.sequence), r.idx)):
		doc.append(
			"responses",
			{
				"section": row.section,
				"question_text": _fill(row.question, candidate_name, job.job_title),
				"answer_type": row.answer_type or "Text",
				"required": row.required,
			},
		)
	doc.insert()
	return doc


def _check_dict(doc_or_row, with_responses=True):
	data = {f: doc_or_row.get(f) for f in CHECK_FIELDS}
	data["link_active"] = bool(
		doc_or_row.get("status") != "Completed"
		and doc_or_row.get("mode") == "Referee form"
		and doc_or_row.get("token_expires_on")
		and get_datetime(doc_or_row.get("token_expires_on")) > now_datetime()
	)
	if with_responses:
		data["responses"] = frappe.get_all(
			"Reference Check Response Row",
			filters={"parent": doc_or_row.get("name"), "parenttype": DOCTYPE, "parentfield": "responses"},
			fields=["name", "section", "question_text", "answer_type", "required", "answer_text", "rating_value"],
			order_by="idx asc",
		)
	return data


def _parse(value, default=None):
	if value in (None, ""):
		return default
	return json.loads(value) if isinstance(value, str) else value


def _apply_answers(doc, answers, enforce_required):
	"""answers: {row name: {"answer_text", "rating_value"}} or a list of
	{"name", "answer_text", "rating_value"}."""
	answers = _parse(answers, {}) or {}
	if isinstance(answers, list):
		answers = {a.get("name"): a for a in answers if isinstance(a, dict)}
	missing = []
	for row in doc.responses:
		given = answers.get(row.name)
		if given is not None:
			if not isinstance(given, dict):
				given = {"answer_text": given}
			text = (str(given.get("answer_text") or "")).strip()
			if len(text) > MAX_ANSWER_LENGTH:
				frappe.throw(_("An answer is too long (at most {0} characters).").format(MAX_ANSWER_LENGTH))
			rating = given.get("rating_value")
			rating = cint(rating) if rating not in (None, "") else None
			if row.answer_type == "Rating 1-5":
				if rating is not None and not 1 <= rating <= 5:
					frappe.throw(_("Ratings go from 1 to 5."))
				row.rating_value = rating
				row.answer_text = text or None
			elif row.answer_type == "Yes-No":
				if text and text not in ("Yes", "No"):
					frappe.throw(_("Answer Yes or No."))
				row.answer_text = text or None
			else:
				row.answer_text = text or None
		answered = row.rating_value if row.answer_type == "Rating 1-5" else (row.answer_text or "").strip()
		if enforce_required and row.required and not answered:
			missing.append(row.question_text)
	if missing:
		frappe.throw(_("Please answer: {0}").format("; ".join(m[:80] for m in missing[:5])), title=_("Answers missing"))


# ------------------------------------------------------------ staff endpoints


@frappe.whitelist()
def get_application_checks(application):
	"""Everything the References panel shows for one application."""
	if not _can("read"):
		return {"can_view": False}
	app = _get_application(application)
	job = _job(app)
	names = frappe.get_all(DOCTYPE, filters={"application": app.name}, pluck="name", order_by="creation asc")
	checks = [_check_dict(frappe.get_doc(DOCTYPE, n)) for n in names]
	taken = {(c["referee_email"] or "").lower() for c in checks if c["referee_email"]} | {
		(c["referee_name"] or "").strip().lower() for c in checks
	}
	referees = []
	for idx, ref in enumerate(app.get("references") or []):
		referees.append(
			{
				"idx": idx,
				"referee_name": ref.referee_name,
				"referee_designation_org": ref.current_designation_org,
				"relationship_to_candidate": ref.relationship,
				"referee_email": ref.email,
				"referee_mobile": ref.mobile,
				"added": (ref.email or "").lower() in taken or (ref.referee_name or "").strip().lower() in taken,
			}
		)
	template = template_for_track(job.track)
	return {
		"can_view": True,
		"can_manage": _can("write"),
		"can_create": _can("create"),
		"application_status": app.status,
		"candidate_name": frappe.db.get_value("Candidate", app.candidate, "full_name"),
		"job_title": job.job_title,
		"track": job.track,
		"template": template,
		"checks": checks,
		"referees": referees,
		"link_valid_days": _settings_days("reference_link_expiry_days", 14),
		"email_enabled": bool(frappe.db.exists("Recruitment Email Rule", {"name": "reference_request", "enabled": 1})),
	}


@frappe.whitelist(methods=["POST"])
def create_checks(application, referees=None):
	"""Create checks for the given referees, or, with none given, for every
	referee in the application who does not have one yet."""
	_require("create")
	app = _get_application(application)
	job = _job(app)
	template = template_for_track(job.track)
	if not template:
		frappe.throw(
			_("There is no active Reference Check Template for the {0} track. Add one in Master Setup.").format(job.track or "")
		)
	referees = _parse(referees, None)
	if not referees:
		existing = frappe.get_all(DOCTYPE, filters={"application": app.name}, fields=["referee_email", "referee_name"])
		taken = {(e.referee_email or "").lower() for e in existing if e.referee_email} | {(e.referee_name or "").strip().lower() for e in existing}
		referees = [
			{
				"referee_name": r.referee_name,
				"referee_designation_org": r.current_designation_org,
				"relationship_to_candidate": r.relationship,
				"referee_email": r.email,
				"referee_mobile": r.mobile,
			}
			for r in app.get("references") or []
			if (r.email or "").lower() not in taken and (r.referee_name or "").strip().lower() not in taken
		]
	if not referees:
		frappe.throw(_("Every referee already has a reference check. Use Add referee for another one."))
	created = [_new_check(app, r, template, job).name for r in referees]
	return {"created": created}


@frappe.whitelist(methods=["POST"])
def update_referee(check, referee_name=None, referee_designation_org=None, relationship_to_candidate=None, referee_email=None, referee_mobile=None):
	"""Correct a referee's details. A changed email address cancels the link
	already sent, so the old address can no longer answer."""
	doc = _get_check(check, "write")
	if doc.status == "Completed":
		frappe.throw(_("This reference check is complete; its referee can no longer be changed."))
	old_email = (doc.referee_email or "").lower()
	given = {
		"referee_name": referee_name,
		"referee_designation_org": referee_designation_org,
		"relationship_to_candidate": relationship_to_candidate,
		"referee_email": referee_email,
		"referee_mobile": referee_mobile,
	}
	for field in REFEREE_FIELDS:
		if given.get(field) is not None:
			doc.set(field, (given.get(field) or "").strip())
	doc.referee_email = _normalise_email(doc.referee_email)
	if not doc.referee_name:
		frappe.throw(_("Enter the referee's name."))
	if (doc.referee_email or "").lower() != old_email and doc.access_token_hash:
		doc.access_token_hash = None
		doc.previous_token_hash = None
		doc.token_expires_on = None
		if doc.mode == "Referee form":
			doc.status = "Pending"
	doc.save()
	return _check_dict(doc)


def issue_token(doc, keep_previous=False):
	"""Give the check a new link; returns the raw token (never stored)."""
	token = secrets.token_urlsafe(32)
	doc.previous_token_hash = doc.access_token_hash if keep_previous else None
	doc.access_token_hash = _hash(token)
	return token


@frappe.whitelist(methods=["POST"])
def send_request(check):
	"""Email the referee a new form link (also "Resend link")."""
	doc = _get_check(check, "write")
	if doc.status == "Completed":
		frappe.throw(_("This reference check is already complete."))
	if not doc.referee_email:
		frappe.throw(_("Add the referee's email address first."))
	token = issue_token(doc)
	now = now_datetime()
	doc.token_expires_on = add_days(now, max(_settings_days("reference_link_expiry_days", 14), 1))
	doc.requested_on = now
	doc.requested_by = frappe.session.user
	doc.reminder_sent_on = None
	doc.mode = "Referee form"
	doc.recorded_by = None
	doc.status = "In Progress"
	doc.save()
	_email_referee(doc, token, "reference_request")
	return {"check": _check_dict(doc), "form_link": _form_link(token)}


def _email_referee(doc, token, event):
	from pathways.utils.communication import send_event

	app = frappe.get_doc("Application", doc.application)
	job = _job(app)
	context = {
		"candidate_name": doc.candidate_name,
		"job_title": job.job_title,
		"referee_name": doc.referee_name,
		"form_link": _form_link(token),
		"expires_on": format_datetime(doc.token_expires_on, "dd MMM yyyy"),
		"contact_email": frappe.get_cached_doc("Pathways Settings").recruitment_contact_email or "",
	}
	send_event(event, DOCTYPE, doc.name, context, recipients=[{"email": doc.referee_email, "name": doc.referee_name}])


@frappe.whitelist(methods=["POST"])
def record_responses(check, answers=None, overall_assessment_summary=None, complete=0):
	"""The recruiter records a referee's answers (e.g. a phone check).
	complete=1 marks the check Completed and needs every required answer."""
	doc = _get_check(check, "write")
	if doc.status == "Completed" and doc.mode == "Referee form":
		frappe.throw(_("The referee submitted this form themselves; their answers cannot be edited."))
	complete = cint(complete)
	_apply_answers(doc, answers, enforce_required=complete)
	if overall_assessment_summary is not None:
		doc.overall_assessment_summary = overall_assessment_summary
	doc.mode = "Recorded by recruiter"
	doc.recorded_by = frappe.session.user
	# A recorded check needs no live link.
	doc.access_token_hash = None
	doc.previous_token_hash = None
	doc.token_expires_on = None
	doc.status = "Completed" if complete else "In Progress"
	if not complete:
		doc.completed_on = None
	doc.save()
	return _check_dict(doc)


@frappe.whitelist(methods=["POST"])
def save_summary(check, overall_assessment_summary=None):
	"""The recruiter's overall assessment, editable at any time."""
	doc = _get_check(check, "write")
	doc.overall_assessment_summary = overall_assessment_summary
	doc.save()
	return _check_dict(doc)


@frappe.whitelist()
def summary_for_applications(names):
	"""{application: {"total", "completed", "in_progress", "pending"}} for
	job-level views. Applications the user cannot read are left out."""
	if not _can("read"):
		return {}
	names = _parse(names, []) or []
	if isinstance(names, str):
		names = [names]
	allowed = [n for n in names if frappe.has_permission("Application", "read", doc=n)]
	out = {n: {"total": 0, "completed": 0, "in_progress": 0, "pending": 0} for n in allowed}
	if not allowed:
		return out
	key = {"Completed": "completed", "In Progress": "in_progress", "Pending": "pending"}
	for row in frappe.get_all(DOCTYPE, filters={"application": ["in", allowed]}, fields=["application", "status"]):
		bucket = out[row.application]
		bucket["total"] += 1
		if row.status in key:
			bucket[key[row.status]] += 1
	return out


# ------------------------------------------------------------ referee (guest) endpoints


def _check_from_token(token):
	"""(doc, state) where state is open | expired | submitted | invalid."""
	if not token or not isinstance(token, str) or len(token) > 128:
		return None, "invalid"
	digest = _hash(token)
	name = frappe.db.get_value(DOCTYPE, {"access_token_hash": digest}, "name") or frappe.db.get_value(
		DOCTYPE, {"previous_token_hash": digest}, "name"
	)
	if not name:
		return None, "invalid"
	doc = frappe.get_doc(DOCTYPE, name)
	if doc.status == "Completed":
		return doc, "submitted"
	if not doc.token_expires_on or get_datetime(doc.token_expires_on) <= now_datetime():
		return doc, "expired"
	return doc, "open"


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=60, seconds=10 * 60)
def get_referee_form(token):
	"""What the public referee form shows. Nothing beyond the candidate's
	name, the post, the intro and the questions."""
	doc, state = _check_from_token(token)
	contact = frappe.get_cached_doc("Pathways Settings").recruitment_contact_email or ""
	if state != "open":
		return {"state": state, "contact_email": contact}
	app = frappe.get_doc("Application", doc.application)
	job = _job(app)
	intro = ""
	if doc.template:
		intro = frappe.db.get_value("Reference Check Template", doc.template, "intro_text") or ""
	return {
		"state": state,
		"contact_email": contact,
		"referee_name": doc.referee_name,
		"candidate_name": doc.candidate_name,
		"position": job.job_title,
		"intro": _fill(intro, doc.candidate_name, job.job_title),
		"expires_on": doc.token_expires_on,
		"questions": [
			{"name": r.name, "section": r.section, "question": r.question_text, "answer_type": r.answer_type or "Text", "required": cint(r.required)}
			for r in doc.responses
		],
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60 * 60)
def submit_referee_form(token, answers):
	"""The referee's one submission."""
	doc, state = _check_from_token(token)
	if state == "submitted":
		frappe.throw(_("Your response has already been received. Thank you."), title=_("Already submitted"))
	if state == "expired":
		frappe.throw(_("This link has expired. Please contact the recruitment team for a new one."), title=_("Link expired"))
	if state != "open":
		frappe.throw(_("This link is not valid."), frappe.PermissionError)
	_apply_answers(doc, answers, enforce_required=True)
	doc.mode = "Referee form"
	doc.status = "Completed"
	doc.completed_on = now_datetime()
	doc.flags.ignore_permissions = True
	doc.save()

	from pathways.utils.communication import send_event

	app = frappe.get_doc("Application", doc.application)
	job = _job(app)
	send_event(
		"reference_received",
		DOCTYPE,
		doc.name,
		{
			"candidate_name": doc.candidate_name,
			"application_id": app.application_id,
			"job_title": job.job_title,
			"referee_name": doc.referee_name,
			"application_link": get_url(f"/pathways/applications/{app.name}"),
		},
		approvers=[doc.requested_by] if doc.requested_by else None,
	)
	return {"state": "submitted"}


# ------------------------------------------------------------ scheduler


def send_reminders():
	"""Daily (tasks.daily): one reminder to referees who have not answered
	`reference_reminder_after_days` after the link went out."""
	days = _settings_days("reference_reminder_after_days", 3)
	if days <= 0:
		return
	now = now_datetime()
	due = frappe.get_all(
		DOCTYPE,
		filters=[
			["status", "!=", "Completed"],
			["mode", "=", "Referee form"],
			["access_token_hash", "is", "set"],
			["reminder_sent_on", "is", "not set"],
			["requested_on", "<=", add_days(now, -days)],
			["token_expires_on", ">", now],
		],
		pluck="name",
	)
	for name in due:
		doc = frappe.get_doc(DOCTYPE, name)
		if not doc.referee_email:
			continue
		token = issue_token(doc, keep_previous=True)
		doc.reminder_sent_on = now
		doc.flags.ignore_permissions = True
		doc.save()
		_email_referee(doc, token, "reference_reminder")
	if due:
		commit()
