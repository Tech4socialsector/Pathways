# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Interview stage (workflow steps 13-16): the job's Selection Committee
(and its calendar block), scheduling Round 1 (HR interaction) with its HR
assessors and Final interviews with the invite emails, the candidate's
RSVP, the final shortlist with the job's Shortlisting Note, and the
interview schedule for the panel."""

import frappe
from frappe import _
from frappe.utils import add_to_date, cint, flt, get_datetime, get_url

from pathways.permissions import CANDIDATE_ROLE, SELECTION_ROLE, has_full_access

ROUNDS = ("HR Interaction", "Final")
# Applications that can be invited: shortlisted, or already in the interview stage.
INTERVIEW_POOL = ("Shortlisted", "Interview Scheduled", "Interview Completed", "Selected")
INVITE_EVENT = {"HR Interaction": "interview_invite_round1", "Final": "interview_call_letter"}


def _can_manage(job_opening=None):
	return bool(frappe.has_permission("Interview", "create")) and has_full_access("Interview")


def _require_manage():
	if not _can_manage():
		frappe.throw(_("Only the recruitment team can schedule interviews."), frappe.PermissionError)


def _committee(job_opening):
	name = frappe.db.get_value("Selection Committee", {"job_opening": job_opening}, "name")
	if not name:
		return None
	doc = frappe.get_doc("Selection Committee", name)
	return {
		"name": doc.name,
		"scheduled_date": doc.scheduled_date,
		"scheduled_time": str(doc.scheduled_time) if doc.scheduled_time else None,
		"calendar_event": doc.get("calendar_event"),
		"calendar_block": _block_participants(doc) if doc.scheduled_date else [],
		"members": [
			{
				"member": m.member,
				"full_name": frappe.utils.get_fullname(m.member),
				"designation_label": m.designation_label,
				"is_external_expert": cint(m.is_external_expert),
			}
			for m in doc.members
		],
	}


def _is_panel_member(job_opening, user=None):
	return bool(
		frappe.db.exists(
			"Selection Committee",
			[["Committee Member Row", "member", "=", user or frappe.session.user], ["job_opening", "=", job_opening]],
		)
	)


@frappe.whitelist()
def get_job_interviews(job_opening):
	"""Job page > Interviews: the candidates in the interview stage, each
	with their rounds, and the job's Selection Committee."""
	manage = _can_manage()
	if not manage and not _is_panel_member(job_opening):
		frappe.throw(_("You cannot see this job's interviews."), frappe.PermissionError)

	apps = frappe.get_all(
		"Application",
		filters={"job_opening": job_opening, "status": ["in", INTERVIEW_POOL + ("Not Selected",)]},
		fields=["name", "application_id", "status", "candidate.full_name as candidate_name", "candidate.email as email"],
		order_by="creation asc",
	)
	# Not Selected only counts here if they were interviewed (rejected after interview).
	interviews = frappe.get_all(
		"Interview",
		filters={"application": ["in", [a.name for a in apps] or [""]]},
		fields=["name", "application", "round_type", "status", "scheduled_datetime", "mode", "meeting_platform", "meeting_link", "location", "rsvp_status", "calendar_event"],
		order_by="scheduled_datetime asc",
	)
	from pathways.api.panel import hr_outcome_summary, score_summary

	scores = score_summary([iv.name for iv in interviews])
	assessors = _assessors_by_interview([iv.name for iv in interviews if iv.round_type == "HR Interaction"])
	hr = hr_outcome_summary([iv.name for iv in interviews if iv.round_type == "HR Interaction"])
	by_app = {}
	for iv in interviews:
		iv.scores = scores.get(iv.name)
		if iv.round_type == "HR Interaction":
			iv.hr_assessors = assessors.get(iv.name, [])
			iv.hr_outcomes = hr.get(iv.name, [])
		by_app.setdefault(iv.application, {})[iv.round_type] = iv
	final_list = _final_shortlist(job_opening)
	rows = []
	for a in apps:
		rounds = by_app.get(a.name, {})
		if a.status == "Not Selected" and not rounds:
			continue
		row = final_list.get(a.name)
		rows.append({**a, "rounds": {r: rounds.get(r) for r in ROUNDS}, "final_shortlisted": 1 if row else 0, "final_shortlist_remarks": (row or {}).get("remarks") or ""})

	settings = frappe.get_cached_doc("Pathways Settings")
	return {
		"candidates": rows,
		"committee": _committee(job_opening),
		"committee_size": {
			"min": cint(settings.get("min_selection_committee_size")) or 3,
			"max": cint(settings.get("max_selection_committee_size")) or 5,
		},
		"can_manage": manage,
		"can_shortlist": 1 if _can_shortlist() else 0,
		"hr_assessor_limit": cint(settings.get("hr_assessors_per_interview")) or 2,
		"shortlisting_note": frappe.db.get_value("Shortlisting Note", {"job_opening": job_opening}, "name"),
	}


# ----------------------------------------------------------- HR assessors (step 13)


def _assessors_by_interview(interviews):
	"""{interview: [{assessor, assessor_name}]}"""
	if not interviews:
		return {}
	out = {}
	for r in frappe.get_all(
		"Interview HR Assessor",
		filters={"parenttype": "Interview", "parent": ["in", list(interviews)]},
		fields=["parent", "assessor", "assessor_name"],
		order_by="idx asc",
	):
		out.setdefault(r.parent, []).append({"assessor": r.assessor, "assessor_name": r.assessor_name or frappe.utils.get_fullname(r.assessor)})
	return out


def _parse_users(value):
	if value is None:
		return None
	if isinstance(value, str):
		value = frappe.parse_json(value) if value.strip() else []
	users = []
	for u in value or []:
		u = (u.get("assessor") if isinstance(u, dict) else u) or ""
		u = u.strip()
		if u and u not in users:
			if not frappe.db.exists("User", {"name": u, "enabled": 1}):
				frappe.throw(_("User {0} does not exist or is disabled.").format(u))
			users.append(u)
	return users


def _set_hr_assessors(iv, users):
	"""Replace the interview's HR assessors (not saved). Returns the people
	who are new to it. Assessors get the Selection Committee role, which
	(see pathways.permissions) only opens the interviews they take and those
	candidates' applications."""
	before = set(iv.hr_assessor_list())
	iv.set("hr_assessors", [{"assessor": u} for u in users])
	return [u for u in users if u not in before]


def _grant_panel_role(users):
	for user in users:
		if user in ("Administrator", "Guest"):
			continue
		doc = frappe.get_doc("User", user)
		if SELECTION_ROLE not in [r.role for r in doc.roles]:
			doc.append("roles", {"role": SELECTION_ROLE})
			doc.save(ignore_permissions=True)


def _notify_hr_assessors(iv, app, users, updated=False):
	if not users:
		return
	from pathways.utils.communication import candidate_email_context, send_event

	context, _candidate = candidate_email_context(app)
	context.update(
		{
			"interview_date_time": frappe.utils.format_datetime(iv.scheduled_datetime, "EEEE, MMMM d, yyyy 'at' h:mm a 'IST'"),
			"meeting_platform": iv.get("meeting_platform") or "",
			"meeting_link": iv.get("meeting_link") or "",
			"interview_location": iv.get("location") or "",
			"assessment_link": get_url(f"/pathways/panel/{iv.name}"),
			"updated": 1 if updated else 0,
		}
	)
	# The rule's "approvers" are the assessors; the candidate is never emailed this.
	send_event("hr_assessor_assigned", "Interview", iv.name, context, approvers=list(users))


def is_hr_assessor(interview, user=None):
	return bool(frappe.db.exists("Interview HR Assessor", {"parenttype": "Interview", "parent": interview, "assessor": user or frappe.session.user}))


# ----------------------------------------------------------- committee


@frappe.whitelist()
def get_panel_options():
	_require_manage()
	return frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Guest", "Administrator"]]},
		fields=["name", "full_name", "email"],
		order_by="full_name asc",
	)


@frappe.whitelist(methods=["POST"])
def save_selection_committee(job_opening, members, scheduled_date=None, scheduled_time=None):
	"""Create or update the job's Selection Committee (workflow step 15).
	members: [{member, designation_label, is_external_expert}]. The doctype
	enforces the 3-5 size; members get the Selection Committee role."""
	_require_manage()
	if isinstance(members, str):
		members = frappe.parse_json(members)
	rows, seen = [], set()
	for m in members or []:
		user = (m.get("member") or "").strip()
		if not user or user in seen:
			continue
		if not frappe.db.exists("User", user):
			frappe.throw(_("User {0} does not exist.").format(user))
		seen.add(user)
		rows.append(
			{"member": user, "designation_label": (m.get("designation_label") or "").strip(), "is_external_expert": cint(m.get("is_external_expert"))}
		)

	name = frappe.db.get_value("Selection Committee", {"job_opening": job_opening}, "name")
	doc = frappe.get_doc("Selection Committee", name) if name else frappe.new_doc("Selection Committee")
	before = {r.member for r in doc.get("members") or []}
	doc.job_opening = job_opening
	doc.scheduled_date = scheduled_date or None
	doc.scheduled_time = scheduled_time or None
	doc.set("members", rows)
	doc.save(ignore_permissions=True)

	# Invite the panellists who are new to this committee.
	new_members = [r["member"] for r in rows if r["member"] not in before]
	if new_members:
		from pathways.utils.communication import job_email_context, send_event

		job = frappe.get_doc("Job Opening", job_opening)
		context = job_email_context(job)
		context.update(
			{
				"interview_date": get_datetime(doc.scheduled_date).strftime("%A, %d %b %Y") if doc.scheduled_date else "",
				"interview_time": _time_label(doc.scheduled_time),
				"panel": ", ".join(frappe.utils.get_fullname(r["member"]) for r in rows),
				"candidate_count": frappe.db.count("Application", {"job_opening": job_opening, "status": ["in", INTERVIEW_POOL]}),
			}
		)
		send_event("selection_committee_assigned", "Selection Committee", doc.name, context, approvers=new_members)
	sync_committee_block(doc)
	return _committee(job_opening)


def _time_label(value):
	if not value:
		return ""
	return frappe.utils.format_time(value, "h:mm a 'IST'")


# ----------------------------------------------------------- scheduling


@frappe.whitelist(methods=["POST"])
def schedule_interviews(
	job_opening, applications, round_type, start, slot_minutes=0, mode="Video Conference", meeting_link=None,
	meeting_platform=None, rsvp_deadline=None, send_invite=1, location=None, create_meet=0, cc=None, hr_assessors=None,
):
	"""Schedule (or reschedule) one round for several candidates. Each
	candidate gets the next slot: start, start + slot, ... The invite (Round
	1) or call letter (Final) goes to each candidate. For Round 1,
	hr_assessors (user IDs) take every one of these interviews: they are
	added to the Meet event and emailed; None keeps a rescheduled
	interview's assessors."""
	_require_manage()
	if round_type not in ROUNDS:
		frappe.throw(_("Unknown interview round."))
	assessors = _parse_users(hr_assessors) if round_type == "HR Interaction" else None
	if isinstance(applications, str):
		applications = frappe.parse_json(applications)
	applications = list(dict.fromkeys(applications or []))
	if not applications:
		frappe.throw(_("Choose at least one candidate."))
	in_person = mode == "In-Person"
	if in_person and not (location or "").strip():
		frappe.throw(_("Enter the location for an in-person interview."))
	create_meet = cint(create_meet) and not in_person
	if create_meet and not _meet_calendar():
		frappe.throw(_("Google Meet is not set up: {0}").format(get_meet_status()["reason"]))
	start_at = get_datetime(start)
	if start_at < frappe.utils.now_datetime():
		frappe.throw(_("The interview time must be in the future."))
	committee = frappe.db.get_value("Selection Committee", {"job_opening": job_opening}, "name")
	if round_type == "Final" and not committee:
		frappe.throw(_("Set up the Selection Committee before scheduling final interviews."))

	done = []
	for i, app_name in enumerate(applications):
		app = frappe.get_doc("Application", app_name)
		if app.job_opening != job_opening:
			frappe.throw(_("{0} is not an application for this job.").format(app_name))
		if app.status not in INTERVIEW_POOL:
			frappe.throw(_("{0} is not shortlisted ({1}).").format(app.application_id, app.status))
		when = add_to_date(start_at, minutes=cint(slot_minutes) * i)

		existing = frappe.db.get_value(
			"Interview", {"application": app_name, "round_type": round_type, "status": ["in", ["Scheduled", "Rescheduled"]]}, "name"
		)
		iv = frappe.get_doc("Interview", existing) if existing else frappe.new_doc("Interview")
		if existing:
			_record_change(iv, when)
		iv.update(
			{
				"application": app_name,
				"round_type": round_type,
				"selection_committee": committee if round_type == "Final" else iv.get("selection_committee"),
				"scheduled_datetime": when,
				"mode": mode or "Video Conference",
				"meeting_link": None if in_person else ((meeting_link or "").strip() or None),
				"meeting_platform": None if in_person else (_platform(meeting_platform, meeting_link) or None),
				"location": (location or "").strip() or None if in_person else None,
				"status": "Rescheduled" if existing else "Scheduled",
				"rsvp_status": "Pending",
			}
		)
		new_assessors = _set_hr_assessors(iv, assessors) if assessors is not None else []
		iv.save(ignore_permissions=True)
		_grant_panel_role(new_assessors)
		# A new Meet link, or move the event a Meet link was made with before.
		if create_meet or (iv.get("calendar_event") and not in_person and _meet_calendar()):
			_sync_meet_event(iv, app, slot_minutes or 30, committee)
		elif in_person:
			_cancel_meet_event(iv)
		if round_type == "HR Interaction":
			# New assessors get the assignment; on a reschedule, everyone gets the new time.
			kept = [u for u in iv.hr_assessor_list() if u not in new_assessors] if existing else []
			_notify_hr_assessors(iv, app, new_assessors)
			_notify_hr_assessors(iv, app, kept, updated=True)

		if app.status == "Shortlisted":
			app.status = "Interview Scheduled"
			app.save(ignore_permissions=True)
		app.add_comment(
			"Info",
			_("{0} interview {1} for {2} by {3}.").format(
				_(round_type), _("rescheduled") if existing else _("scheduled"),
				frappe.utils.format_datetime(when, "dd MMM yyyy, h:mm a 'IST'"), frappe.utils.get_fullname(frappe.session.user),
			),
		)
		if cint(send_invite):
			_send_invite(iv, app, meeting_platform, rsvp_deadline, cc=cc)
		done.append(iv.name)
	return {"scheduled": len(done), "interviews": done}


PLATFORM_HOSTS = (("meet.google.com", "Google Meet"), ("zoom.us", "Zoom"), ("teams.microsoft.com", "Microsoft Teams"), ("teams.live.com", "Microsoft Teams"))


def _platform(name=None, link=None):
	"""The platform as chosen, else recognised from the meeting link."""
	name = (name or "").strip()
	if name:
		return name
	link = (link or "").lower()
	return next((label for host, label in PLATFORM_HOSTS if host in link), "")


# ----------------------------------------------------------- Google Meet
# Uses Frappe's Google Calendar integration (Desk: Google Settings, Google
# Calendar). An Event synced to the chosen calendar with video conferencing
# gets a Meet link from Google; the interview keeps a link to that Event.


def _meet_calendar():
	"""The Google Calendar set for interview meetings, if it can be used."""
	name = frappe.get_cached_doc("Pathways Settings").get("interview_google_calendar")
	if not name or not frappe.db.get_single_value("Google Settings", "enable"):
		return None
	cal = frappe.db.get_value("Google Calendar", name, ["name", "enable", "push_to_google_calendar"], as_dict=True)
	if not cal or not cal.enable or not cal.push_to_google_calendar:
		return None
	doc = frappe.get_doc("Google Calendar", name)
	return name if doc.get_password("refresh_token", raise_exception=False) else None


@frappe.whitelist()
def get_meet_status():
	"""Settings > Google Meet, and the schedule dialog: is automatic Meet
	link creation ready, and if not, what is missing."""
	if not (_can_manage() or frappe.has_permission("Pathways Settings", "write")):
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	google_on = bool(frappe.db.get_single_value("Google Settings", "enable"))
	calendars = []
	for c in frappe.get_all("Google Calendar", fields=["name", "calendar_name", "user", "enable", "push_to_google_calendar"]):
		authorised = bool(frappe.get_doc("Google Calendar", c.name).get_password("refresh_token", raise_exception=False))
		calendars.append({**c, "authorised": authorised})
	selected = frappe.get_cached_doc("Pathways Settings").get("interview_google_calendar")
	ready = bool(_meet_calendar())
	if ready:
		reason = ""
	elif not google_on:
		reason = _("Google Settings is not enabled (Client ID and Client Secret from a Google Cloud project).")
	elif not calendars:
		reason = _("No Google Calendar is connected yet.")
	elif not selected:
		reason = _("Choose the calendar for interview meetings.")
	else:
		reason = _("The chosen calendar is not authorised, enabled, or set to push events to Google.")
	return {"ready": ready, "reason": reason, "google_enabled": google_on, "calendars": calendars, "selected": selected}


def _sync_meet_event(iv, app, minutes, committee=None):
	"""Create or move the interview's Google Calendar event (with a Meet
	link) and copy the link onto the interview."""
	calendar = _meet_calendar()
	if not calendar:
		frappe.throw(_("Google Meet is not set up: {0}").format(get_meet_status()["reason"]))
	calendar_id = _google_calendar_id(calendar)
	candidate = frappe.db.get_value("Candidate", app.candidate, ["full_name", "email"], as_dict=True) or {}
	job_title = frappe.db.get_value("Job Opening", app.job_opening, "job_title")
	start = get_datetime(iv.scheduled_datetime)
	end = add_to_date(start, minutes=max(cint(minutes), 15))
	emails = [candidate.get("email")]
	if iv.round_type == "Final" and committee:
		emails += frappe.get_all("Committee Member Row", filters={"parent": committee, "parenttype": "Selection Committee"}, pluck="member")
	if iv.round_type == "HR Interaction":
		emails += [frappe.db.get_value("User", u, "email") or u for u in iv.hr_assessor_list()]
	participants = [
		{"reference_doctype": "Interview", "reference_docname": iv.name, "email": e}
		for e in dict.fromkeys(e for e in emails if e and e != "Administrator" and "@" in e)
	]
	subject = _("{0} interview: {1}, {2}").format(
		_("Round 1 (HR)") if iv.round_type == "HR Interaction" else _("Final"), candidate.get("full_name") or app.application_id, job_title
	)
	if iv.get("calendar_event") and frappe.db.exists("Event", iv.calendar_event):
		ev = frappe.get_doc("Event", iv.calendar_event)
		ev.update({"subject": subject, "starts_on": start, "ends_on": end, "status": "Open", "google_calendar_id": calendar_id})
		ev.set("event_participants", participants)
		ev.save(ignore_permissions=True)
	else:
		ev = frappe.get_doc(
			{
				"doctype": "Event",
				"subject": subject,
				"event_category": "Meeting",
				"event_type": "Private",
				"starts_on": start,
				"ends_on": end,
				"description": _("NLSIU recruitment interview for {0} ({1}).").format(job_title, app.application_id),
				"sync_with_google_calendar": 1,
				"google_calendar": calendar,
				# Desk fills this from the Google Calendar; a script must set it.
				"google_calendar_id": calendar_id,
				"add_video_conferencing": 1,
				"event_participants": participants,
				"reference_doctype": "Interview",
				"reference_docname": iv.name,
			}
		).insert(ignore_permissions=True)
	link = frappe.db.get_value("Event", ev.name, "google_meet_link")
	if not link:
		frappe.throw(_("Google Calendar did not return a Meet link for {0}. Check the calendar connection.").format(app.application_id))
	iv.db_set({"calendar_event": ev.name, "meeting_link": link, "meeting_platform": "Google Meet"}, update_modified=False)
	iv.reload()


def _google_calendar_id(calendar):
	"""The calendar's id in Google; connecting it the first time creates the
	calendar in the Google account and stores the id."""
	calendar_id = frappe.db.get_value("Google Calendar", calendar, "google_calendar_id")
	if not calendar_id:
		from frappe.integrations.doctype.google_calendar.google_calendar import get_google_calendar_object

		get_google_calendar_object(calendar)
		calendar_id = frappe.db.get_value("Google Calendar", calendar, "google_calendar_id")
	if not calendar_id:
		frappe.throw(_("Google Calendar {0} has no calendar in Google yet. Authorise it again in Desk.").format(calendar))
	return calendar_id


def _cancel_meet_event(iv):
	if iv.get("calendar_event") and frappe.db.exists("Event", iv.calendar_event):
		ev = frappe.get_doc("Event", iv.calendar_event)
		ev.status = "Cancelled"
		ev.save(ignore_permissions=True)


def _send_invite(iv, app, meeting_platform=None, rsvp_deadline=None, updated=False, note=None, cc=None):
	from pathways.utils.communication import candidate_email_context, send_event

	when = get_datetime(iv.scheduled_datetime)
	context, candidate = candidate_email_context(app)
	context.update(
		{
			"interview_date_time": frappe.utils.format_datetime(when, "EEEE, MMMM d, yyyy 'at' h:mm a 'IST'"),
			"interview_date": when.strftime("%d %b %Y"),
			"interview_day": when.strftime("%A"),
			"interview_time": when.strftime("%I:%M %p").lstrip("0") + " IST",
			"login_time": add_to_date(when, minutes=-20).strftime("%I:%M %p").lstrip("0") + " IST",
			"interview_mode": "Online" if iv.mode == "Video Conference" else "In person",
			"meeting_platform": meeting_platform or iv.get("meeting_platform") or "Microsoft Teams",
			"meeting_link": iv.meeting_link or "",
			"interview_location": iv.get("location") or "",
			"rsvp_deadline": frappe.utils.format_datetime(rsvp_deadline, "MMMM d, yyyy '–' h:mm a 'IST'") if rsvp_deadline else "",
			"rsvp_link": get_url(f"/pathways/portal/applications/{app.name}"),
			# The buttons open the portal; the candidate signs in and replies there.
			"rsvp_respond_link": portal_rsvp_link(app.name, iv.name),
			# Rescheduled / edited: the email says it replaces the earlier one.
			"updated": 1 if updated else 0,
			"change_note": (note or "").strip(),
		}
	)
	send_event(INVITE_EVENT[iv.round_type], "Interview", iv.name, context, candidate=candidate, cc=cc)


@frappe.whitelist(methods=["POST"])
def resend_invite(interview, meeting_platform=None, rsvp_deadline=None, cc=None):
	_require_manage()
	iv = frappe.get_doc("Interview", interview)
	_send_invite(iv, frappe.get_doc("Application", iv.application), meeting_platform, rsvp_deadline, cc=cc)
	return True


@frappe.whitelist(methods=["POST"])
def set_interview_status(interview, status, reason=None, notify=0, cc=None):
	"""Mark an interview Completed or Cancelled. A completed Final moves the
	application to Interview Completed. Cancelling can email the candidate."""
	_require_manage()
	if status not in ("Completed", "Cancelled"):
		frappe.throw(_("Unknown interview status."))
	iv = frappe.get_doc("Interview", interview)
	iv.status = status
	iv.save(ignore_permissions=True)
	if status == "Cancelled":
		_cancel_meet_event(iv)
	app = frappe.get_doc("Application", iv.application)
	if status == "Completed" and iv.round_type == "Final" and app.status == "Interview Scheduled":
		app.status = "Interview Completed"
		app.save(ignore_permissions=True)
	if status == "Cancelled" and app.status == "Interview Scheduled":
		other = frappe.db.exists("Interview", {"application": app.name, "name": ["!=", iv.name], "status": ["in", ["Scheduled", "Rescheduled"]]})
		if not other:
			app.status = "Shortlisted"
			app.save(ignore_permissions=True)
	note = _("{0} interview marked {1} by {2}.").format(_(iv.round_type), _(status).lower(), frappe.utils.get_fullname(frappe.session.user))
	if reason:
		note += " " + _("Reason: {0}").format(frappe.utils.escape_html(reason))
	app.add_comment("Info", note)
	if status == "Cancelled" and cint(notify):
		from pathways.utils.communication import candidate_email_context, send_event

		context, candidate = candidate_email_context(app)
		context.update(
			{
				"interview_round": _("Round 1 (HR interaction)") if iv.round_type == "HR Interaction" else _("final interview"),
				"interview_date_time": frappe.utils.format_datetime(iv.scheduled_datetime, "EEEE, MMMM d, yyyy 'at' h:mm a 'IST'"),
				"reason": (reason or "").strip(),
			}
		)
		send_event("interview_cancelled", "Interview", iv.name, context, candidate=candidate, cc=cc)
	return {"status": iv.status, "application_status": app.status}


@frappe.whitelist()
def get_email_recipients(round_type=None, job_openings=None, cancelled=0):
	"""Who an interview email goes to, for the dialogs: the candidate, the
	rule's other recipients and CC (Email Setup), and people worth copying
	(the jobs' Selection Committee, the recruitment contact)."""
	_require_manage()
	from pathways.utils.communication import event_recipients

	event = "interview_cancelled" if cint(cancelled) else INVITE_EVENT.get(round_type or "HR Interaction")
	if not frappe.db.exists("Recruitment Email Rule", event):
		return {"enabled": 0, "label": event, "to_candidate": 0, "to": [], "cc": [], "suggestions": []}
	rule = frappe.get_doc("Recruitment Email Rule", event)
	jobs = frappe.parse_json(job_openings) if job_openings else []
	if isinstance(jobs, str):
		jobs = [jobs]

	suggestions, seen = [], set()

	def suggest(email, name, tag):
		if email and email.lower() not in seen:
			seen.add(email.lower())
			suggestions.append({"email": email, "name": name or email, "tag": tag})

	for job in jobs:
		committee = frappe.db.get_value("Selection Committee", {"job_opening": job}, "name")
		if committee:
			for user in frappe.get_all("Committee Member Row", filters={"parent": committee, "parenttype": "Selection Committee"}, pluck="member"):
				row = frappe.db.get_value("User", user, ["email", "full_name"], as_dict=True)
				if row:
					suggest(row.email, row.full_name, _("Selection Committee"))
	suggest(frappe.get_cached_doc("Pathways Settings").get("recruitment_contact_email"), None, _("Recruitment team"))
	return {
		"enabled": cint(rule.enabled),
		"label": rule.label,
		"to_candidate": cint(rule.send_to_candidate),
		# Everyone besides the candidate (roles, approvers, extra recipients).
		"to": [{"email": e, "name": n} for e, n in event_recipients(rule)],
		"cc": [e.strip() for e in (rule.cc or "").split(",") if e.strip()],
		"suggestions": suggestions,
	}


def _record_change(iv, new_start, note=None):
	"""Interviews > Rescheduled / edited: what changed last, and when. Call
	before the new time is set on `iv`."""
	before = get_datetime(iv.scheduled_datetime) if iv.scheduled_datetime else None
	if before and get_datetime(new_start) != before:
		iv.change_type = "Rescheduled"
		iv.previous_datetime = before
	else:
		iv.change_type = "Details edited"
	iv.change_count = cint(iv.get("change_count")) + 1
	iv.last_changed_on = frappe.utils.now_datetime()
	iv.last_changed_by = frappe.session.user
	iv.change_note = (note or "").strip() or None


@frappe.whitelist(methods=["POST"])
def update_interview(
	interview, start=None, minutes=None, mode=None, meeting_platform=None, meeting_link=None, location=None,
	rsvp_deadline=None, create_meet=0, send_invite=1, note=None, cc=None, hr_assessors=None,
):
	"""Reschedule or edit one open interview. A new time marks it Rescheduled
	and asks the candidate to reply again; the updated invite says it
	replaces the earlier one. Round 1: hr_assessors replaces the assessors
	(None keeps them); new ones are emailed, and on a new time the others
	get the updated details."""
	_require_manage()
	iv = frappe.get_doc("Interview", interview)
	if iv.status not in ("Scheduled", "Rescheduled"):
		frappe.throw(_("Only scheduled interviews can be changed (this one is {0}).").format(iv.status))
	app = frappe.get_doc("Application", iv.application)
	before = get_datetime(iv.scheduled_datetime)
	new_start = get_datetime(start) if start else before
	time_changed = new_start != before
	if time_changed and new_start < frappe.utils.now_datetime():
		frappe.throw(_("The new interview time must be in the future."))

	mode = mode or iv.mode
	in_person = mode == "In-Person"
	if in_person and not (location if location is not None else iv.get("location") or "").strip():
		frappe.throw(_("Enter the location for an in-person interview."))
	create_meet = cint(create_meet) and not in_person
	if create_meet and not _meet_calendar():
		frappe.throw(_("Google Meet is not set up: {0}").format(get_meet_status()["reason"]))

	_record_change(iv, new_start, note)
	iv.update(
		{
			"scheduled_datetime": new_start,
			"mode": mode,
			"location": ((location or "").strip() or None) if in_person else None,
			"meeting_link": None if in_person else ((meeting_link or "").strip() or iv.meeting_link),
			"meeting_platform": None if in_person else (_platform(meeting_platform, meeting_link) or iv.get("meeting_platform")),
		}
	)
	if time_changed:
		iv.status = "Rescheduled"
		iv.rsvp_status = "Pending"
	assessors = _parse_users(hr_assessors) if iv.round_type == "HR Interaction" else None
	new_assessors = _set_hr_assessors(iv, assessors) if assessors is not None else []
	iv.save(ignore_permissions=True)
	_grant_panel_role(new_assessors)

	committee = frappe.db.get_value("Selection Committee", {"job_opening": app.job_opening}, "name")
	if in_person:
		_cancel_meet_event(iv)
	elif create_meet or (iv.get("calendar_event") and _meet_calendar()):
		_sync_meet_event(iv, app, minutes or 30, committee)

	what = _("rescheduled to {0}").format(frappe.utils.format_datetime(new_start, "dd MMM yyyy, h:mm a 'IST'")) if time_changed else _("details updated")
	comment = _("{0} interview {1} by {2}.").format(_(iv.round_type), what, frappe.utils.get_fullname(frappe.session.user))
	if note:
		comment += " " + _("Note: {0}").format(frappe.utils.escape_html(note))
	app.add_comment("Info", comment)
	if cint(send_invite):
		_send_invite(iv, app, meeting_platform, rsvp_deadline, updated=True, note=note, cc=cc)
	if iv.round_type == "HR Interaction":
		_notify_hr_assessors(iv, app, new_assessors)
		if time_changed:
			_notify_hr_assessors(iv, app, [u for u in iv.hr_assessor_list() if u not in new_assessors], updated=True)
	return {"status": iv.status, "scheduled_datetime": iv.scheduled_datetime}


# ----------------------------------------------------------- RSVP


def portal_rsvp_link(application, interview, response=None):
	"""The application page on the candidate portal, opened on this
	interview; with a response, its Confirm / Decline question too."""
	url = get_url(f"/pathways/portal/applications/{application}?interview={interview}")
	return f"{url}&rsvp={response}" if response else url


def _record_rsvp(iv, response, via):
	iv.db_set("rsvp_status", response)
	frappe.get_doc("Application", iv.application).add_comment(
		"Info", _("Candidate {0} the {1} interview on {2} ({3}).").format(
			_("confirmed") if response == "Confirmed" else _("declined"), _(iv.round_type),
			frappe.utils.format_datetime(iv.scheduled_datetime, "dd MMM yyyy, h:mm a 'IST'"), via,
		),
	)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def rsvp_from_email(interview=None, response=None, token=None):
	"""Links in invites sent before replies moved to the portal: nothing is
	recorded here; the candidate is sent to the portal to sign in and reply."""
	application = frappe.db.get_value("Interview", interview, "application") if interview else None
	if not application:
		frappe.respond_as_web_page(_("Link not valid"), _("Please sign in to the candidate portal to reply to your interview invitation."), http_status_code=400, indicator_color="red")
		return
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = portal_rsvp_link(application, interview, response if response in ("Confirmed", "Declined") else "Confirmed")


@frappe.whitelist(methods=["POST"])
def respond_rsvp(interview, response):
	"""Candidate portal: confirm or decline an interview."""
	if response not in ("Confirmed", "Declined"):
		frappe.throw(_("Choose Confirm or Decline."))
	iv = frappe.get_doc("Interview", interview)
	candidate = frappe.db.get_value("Application", iv.application, "candidate")
	if CANDIDATE_ROLE not in frappe.get_roles() or frappe.db.get_value("Candidate", candidate, "email") != frappe.session.user:
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	if iv.status not in ("Scheduled", "Rescheduled"):
		frappe.throw(_("This interview is no longer open for a reply."))
	_record_rsvp(iv, response, _("in the portal"))
	return response


# ----------------------------------------------------------- all interviews


@frappe.whitelist()
def list_interviews():
	"""Interviews page: every interview the user may see, with names."""
	rows = frappe.get_list(
		"Interview",
		fields=[
			"name", "application", "round_type", "status", "scheduled_datetime", "mode", "meeting_platform", "meeting_link", "location", "rsvp_status", "calendar_event", "modified",
			"change_type", "previous_datetime", "change_count", "last_changed_on", "last_changed_by", "change_note",
			"application.application_id as application_id", "application.job_opening as job_opening",
		],
		order_by="scheduled_datetime desc",
		limit_page_length=0,
	)
	if not rows:
		return []
	apps = {
		a.name: a
		for a in frappe.get_all(
			"Application",
			filters={"name": ["in", list({r.application for r in rows})]},
			fields=["name", "candidate.full_name as candidate_name", "job_opening.job_title as job_title"],
		)
	}
	from pathways.api.panel import score_summary

	scores = score_summary([r.name for r in rows])
	assessors = _assessors_by_interview([r.name for r in rows if r.round_type == "HR Interaction"])
	limit = cint(frappe.get_cached_doc("Pathways Settings").get("hr_assessors_per_interview")) or 2
	for r in rows:
		r.hr_assessor_limit = limit
		a = apps.get(r.application) or {}
		r.candidate_name = a.get("candidate_name")
		r.job_title = a.get("job_title")
		r.scores = scores.get(r.name)
		r.hr_assessors = assessors.get(r.name, []) if r.round_type == "HR Interaction" else []
		r.last_changed_by_name = frappe.utils.get_fullname(r.last_changed_by) if r.last_changed_by else ""
	return rows


@frappe.whitelist()
def list_to_schedule():
	"""Interviews page > To schedule, grouped by job, for the recruitment
	team: shortlisted candidates with no open interview (next: Round 1), and
	candidates whose Round 1 is completed (next: the final interview)."""
	if not _can_manage():
		return []
	apps = frappe.get_all(
		"Application",
		filters={"status": ["in", ["Shortlisted", "Interview Scheduled", "Interview Completed"]]},
		fields=[
			"name", "application_id", "job_opening", "status", "eligibility_status", "candidate.full_name as candidate_name",
			"job_opening.job_title as job_title", "job_opening.position as position", "job_opening.track as track",
		],
		order_by="creation asc",
	)
	if not apps:
		return []
	booked = set(
		frappe.get_all(
			"Interview",
			filters={"application": ["in", [a.name for a in apps]], "status": ["in", ["Scheduled", "Rescheduled"]]},
			pluck="application",
		)
	)
	# Earlier interviews that did not go ahead (cancelled) or are done.
	history = {}
	done_rounds = {}
	for iv in frappe.get_all(
		"Interview",
		filters={"application": ["in", [a.name for a in apps]], "status": ["in", ["Cancelled", "Completed"]]},
		fields=["application", "round_type", "status"],
		order_by="scheduled_datetime asc",
	):
		label = _("Round 1") if iv.round_type == "HR Interaction" else _("Final")
		history.setdefault(iv.application, []).append(f"{label} {_(iv.status).lower()}")
		if iv.status == "Completed":
			done_rounds.setdefault(iv.application, set()).add(iv.round_type)
	committees = {
		c.job_opening: c
		for c in frappe.get_all(
			"Selection Committee",
			filters={"job_opening": ["in", list({a.job_opening for a in apps})]},
			fields=["job_opening", "scheduled_date", "scheduled_time"],
		)
	}
	final_listed = set(
		frappe.get_all("Final Shortlist Row", filters={"parenttype": "Shortlisting Note", "application": ["in", [a.name for a in apps]]}, pluck="application")
	)
	jobs = {}
	for a in apps:
		if a.name in booked:
			continue
		done = done_rounds.get(a.name, set())
		if "Final" in done:
			continue
		# On the final shortlist (step 14), with or without a Round 1.
		if "HR Interaction" in done or a.name in final_listed:
			next_round = "Final"
		elif a.status == "Shortlisted":
			next_round = "HR Interaction"
		else:
			# Nothing open and no round completed: left as it is.
			continue
		job = jobs.setdefault(
			a.job_opening,
			{"job_opening": a.job_opening, "job_title": a.job_title, "position": a.position, "track": a.track,
				"has_committee": a.job_opening in committees,
				"committee_date": (committees.get(a.job_opening) or {}).get("scheduled_date"),
				"committee_time": str((committees.get(a.job_opening) or {}).get("scheduled_time") or "") or None,
				"candidates": []},
		)
		job["candidates"].append(
			{
				"name": a.name, "application_id": a.application_id, "candidate_name": a.candidate_name,
				"status": a.status, "eligibility_status": a.eligibility_status, "interview_history": ", ".join(history.get(a.name, [])),
				"next_round": next_round, "final_shortlisted": 1 if a.name in final_listed else 0,
			}
		)
	return sorted(jobs.values(), key=lambda j: (-len(j["candidates"]), j["job_title"] or ""))


# ----------------------------------------------------------- calendar block (step 15)
# "Check the schedule of the VC and Registrar and block the calendar with
# the VC Office": one Event per Selection Committee for its sitting, with
# the panel and the users of Pathways Settings > Calendar block roles. It is
# moved (never duplicated) when the date or time changes, and synced to
# Google Calendar like the interview Meet events when Google is set up.


def _block_users(committee):
	"""The panel, then everyone holding a calendar block role."""
	users = [m.member for m in committee.members]
	settings = frappe.get_cached_doc("Pathways Settings")
	roles = [r.role for r in settings.get("calendar_block_roles") or [] if r.role]
	if roles:
		holders = frappe.get_all("Has Role", filters={"role": ["in", roles], "parenttype": "User"}, pluck="parent", distinct=True)
		enabled = set(
			frappe.get_all("User", filters={"name": ["in", holders or [""]], "enabled": 1, "user_type": "System User"}, pluck="name")
		)
		users += sorted(u for u in enabled if u not in users)
	return [u for u in dict.fromkeys(users) if u not in ("Administrator", "Guest")]


def _block_participants(committee):
	return [{"user": u, "full_name": frappe.utils.get_fullname(u)} for u in _block_users(committee)]


def sync_committee_block(committee):
	"""Create, move or cancel the committee sitting's calendar Event."""
	event_name = committee.get("calendar_event") if frappe.db.exists("Event", committee.get("calendar_event") or "") else None
	if not committee.scheduled_date:
		if event_name:
			frappe.db.set_value("Event", event_name, "status", "Cancelled")
		return None
	timed = bool(committee.scheduled_time)
	start = get_datetime(f"{committee.scheduled_date} {committee.scheduled_time if timed else '00:00:00'}")
	hours = flt(frappe.get_cached_doc("Pathways Settings").get("committee_block_hours")) or 3
	users = _block_users(committee)
	emails = [frappe.db.get_value("User", u, "email") or u for u in users]
	job_title = frappe.db.get_value("Job Opening", committee.job_opening, "job_title")
	panel = ", ".join(frappe.utils.get_fullname(m.member) for m in committee.members)
	values = {
		"subject": _("Selection Committee: {0}").format(job_title),
		"event_category": "Meeting",
		"event_type": "Private",
		"starts_on": start,
		"ends_on": add_to_date(start, hours=hours) if timed else None,
		"all_day": 0 if timed else 1,
		"status": "Open",
		"description": _("NLSIU recruitment: Selection Committee interviews for {0}. Panel: {1}.").format(job_title, panel),
		"reference_doctype": "Selection Committee",
		"reference_docname": committee.name,
	}
	participants = [
		{"reference_doctype": "Selection Committee", "reference_docname": committee.name, "email": e}
		for e in dict.fromkeys(e for e in emails if e and "@" in e)
	]
	calendar = _meet_calendar()
	ev = frappe.get_doc("Event", event_name) if event_name else frappe.new_doc("Event")
	ev.update(values)
	ev.set("event_participants", participants)
	if calendar:
		frappe.db.savepoint("committee_block")
		try:
			ev.update({"sync_with_google_calendar": 1, "google_calendar": calendar, "google_calendar_id": _google_calendar_id(calendar)})
			ev.save(ignore_permissions=True)
		except Exception:
			# Google refused: keep the block in Pathways and say why in the Error Log.
			frappe.db.rollback(save_point="committee_block")
			frappe.log_error(title=_("Selection Committee calendar block: Google sync failed"), reference_doctype="Selection Committee", reference_name=committee.name)
			ev = frappe.get_doc("Event", event_name) if event_name else frappe.new_doc("Event")
			ev.update(values)
			ev.set("event_participants", participants)
			ev.update({"sync_with_google_calendar": 0})
			ev.save(ignore_permissions=True)
	else:
		ev.save(ignore_permissions=True)
	# Private Events show in a user's Desk calendar when shared with them.
	for user in users:
		if not frappe.db.exists("DocShare", {"share_doctype": "Event", "share_name": ev.name, "user": user}):
			frappe.share.add_docshare("Event", ev.name, user, read=1, notify=0, flags={"ignore_share_permission": True})
	if committee.get("calendar_event") != ev.name:
		committee.db_set("calendar_event", ev.name, update_modified=False)
	return ev.name


# ----------------------------------------------------------- final shortlist (step 14)


def _can_shortlist():
	"""Recruiter / PNCO: whoever may edit the job's Shortlisting Note (Role
	Permissions on Shortlisting Note)."""
	return bool(frappe.has_permission("Shortlisting Note", "write")) and has_full_access("Shortlisting Note")


def _require_shortlist():
	if not _can_shortlist():
		frappe.throw(_("Only the recruitment team can prepare the final shortlist."), frappe.PermissionError)


def _final_shortlist(job_opening):
	"""{application: {remarks, ...}} of the job's final shortlist."""
	note = frappe.db.get_value("Shortlisting Note", {"job_opening": job_opening}, "name")
	if not note:
		return {}
	return {
		r.application: r
		for r in frappe.get_all(
			"Final Shortlist Row", filters={"parenttype": "Shortlisting Note", "parent": note}, fields=["application", "remarks", "hr_outcome"], order_by="idx asc"
		)
	}


def _note_doc(job_opening, create=True):
	name = frappe.db.get_value("Shortlisting Note", {"job_opening": job_opening}, "name")
	if name:
		return frappe.get_doc("Shortlisting Note", name)
	if not create:
		return None
	doc = frappe.new_doc("Shortlisting Note")
	doc.job_opening = job_opening
	doc.prepared_by = frappe.session.user
	return doc


@frappe.whitelist(methods=["POST"])
def set_final_shortlist(job_opening, applications, shortlisted=1, remarks=None):
	"""Job page > Interviews: add candidates to (or take them off) the
	final shortlist after Round 1. The application status is not changed:
	the list lives on the job's Shortlisting Note, so every status filter
	keeps working; Interviews > To schedule offers the final for them."""
	_require_shortlist()
	from pathways.api.panel import hr_outcome_label

	names = frappe.parse_json(applications) if isinstance(applications, str) else applications
	names = list(dict.fromkeys(names or []))
	if not names:
		frappe.throw(_("Choose at least one candidate."))
	doc = _note_doc(job_opening)
	current = {r.application: r for r in doc.final_shortlist}
	changed = []
	for name in names:
		app = frappe.db.get_value("Application", name, ["name", "job_opening", "application_id", "status"], as_dict=True)
		if not app or app.job_opening != job_opening:
			frappe.throw(_("{0} is not an application for this job.").format(name))
		if cint(shortlisted):
			if app.status not in INTERVIEW_POOL:
				frappe.throw(_("{0} is not in the interview stage ({1}).").format(app.application_id, app.status))
			if name in current:
				if remarks is not None:
					current[name].remarks = (remarks or "").strip() or None
				continue
			doc.append(
				"final_shortlist",
				{
					"application": name,
					"hr_outcome": hr_outcome_label(name),
					"remarks": (remarks or "").strip() or None,
					"shortlisted_by": frappe.session.user,
					"shortlisted_on": frappe.utils.now_datetime(),
				},
			)
			changed.append(name)
		elif name in current:
			doc.remove(current[name])
			changed.append(name)
	doc.prepared_by = doc.prepared_by or frappe.session.user
	doc.save(ignore_permissions=True)
	for name in changed:
		frappe.get_doc("Application", name).add_comment(
			"Info",
			(_("Added to the final shortlist by {0}.") if cint(shortlisted) else _("Taken off the final shortlist by {0}.")).format(
				frappe.utils.get_fullname(frappe.session.user)
			),
		)
	return {"changed": len(changed), "shortlisting_note": doc.name, "count": len(doc.final_shortlist)}


@frappe.whitelist()
def get_shortlisting_note(job_opening):
	"""The job's Shortlisting Note for the editor (recruitment team) or to
	read (the job's panel)."""
	if not (_can_shortlist() or _can_manage() or _is_panel_member(job_opening)):
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	doc = _note_doc(job_opening, create=False)
	job = frappe.db.get_value("Job Opening", job_opening, ["name", "job_title", "position"], as_dict=True)
	if not doc:
		return {"name": None, "job": job, "note": "", "final_shortlist": [], "attachments": [], "can_edit": 1 if _can_shortlist() else 0}
	return {
		"name": doc.name,
		"job": job,
		"note": doc.note or "",
		"prepared_by": doc.prepared_by,
		"prepared_by_name": frappe.utils.get_fullname(doc.prepared_by) if doc.prepared_by else "",
		"prepared_on": doc.prepared_on,
		"final_shortlist": [
			{"application": r.application, "application_id": r.application_id, "candidate_name": r.candidate_name, "hr_outcome": r.hr_outcome or "", "remarks": r.remarks or ""}
			for r in doc.final_shortlist
		],
		"attachments": [{"name": r.name, "label": r.label, "attachment": r.attachment} for r in doc.attachments],
		"can_edit": 1 if _can_shortlist() else 0,
	}


@frappe.whitelist(methods=["POST"])
def save_shortlisting_note(job_opening, note=None, attachments=None, remarks=None, prepared_by=None):
	"""Save the note text, its attachments [{label, attachment}] and the
	remarks per shortlisted candidate {application: remarks}."""
	_require_shortlist()
	doc = _note_doc(job_opening)
	if note is not None:
		doc.note = note
	if attachments is not None:
		rows = frappe.parse_json(attachments) if isinstance(attachments, str) else attachments
		doc.set(
			"attachments",
			[{"label": (r.get("label") or "").strip() or r.get("attachment", "").rsplit("/", 1)[-1], "attachment": r.get("attachment")} for r in rows or [] if r.get("attachment")],
		)
	if remarks is not None:
		remarks = frappe.parse_json(remarks) if isinstance(remarks, str) else remarks
		for row in doc.final_shortlist:
			if row.application in remarks:
				row.remarks = (remarks[row.application] or "").strip() or None
	if prepared_by:
		doc.prepared_by = prepared_by
	doc.prepared_by = doc.prepared_by or frappe.session.user
	doc.save(ignore_permissions=True)
	return get_shortlisting_note(job_opening)


def shortlisting_note_pdf(job_opening):
	"""The Shortlisting Note print format as PDF bytes (no permission check)."""
	doc = _note_doc(job_opening, create=False)
	if not doc:
		frappe.throw(_("This job has no Shortlisting Note yet."))
	html = frappe.db.get_value("Print Format", "Shortlisting Note", "html")
	from frappe.utils.pdf import get_pdf

	return get_pdf(frappe.render_template(html, {"doc": doc, "frappe": frappe}), {"page-size": "A4"})


@frappe.whitelist()
def download_shortlisting_note(job_opening):
	if not (_can_shortlist() or _can_manage()):
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	job_title = frappe.db.get_value("Job Opening", job_opening, "job_title")
	frappe.local.response.filename = f"Shortlisting Note - {job_title}.pdf"
	frappe.local.response.filecontent = shortlisting_note_pdf(job_opening)
	frappe.local.response.type = "download"


# ----------------------------------------------------------- HR interaction on the application


@frappe.whitelist()
def get_hr_interaction(application):
	"""Application page: the Round 1 (HR interaction) interviews, their
	assessors and what each recorded."""
	app = frappe.get_doc("Application", application)
	app.check_permission("read")
	from pathways.api.panel import hr_assessments

	interviews = frappe.get_all(
		"Interview",
		filters={"application": application, "round_type": "HR Interaction"},
		fields=["name", "status", "scheduled_datetime", "mode", "meeting_platform", "location"],
		order_by="scheduled_datetime desc",
	)
	assessors = _assessors_by_interview([iv.name for iv in interviews])
	for iv in interviews:
		iv.hr_assessors = assessors.get(iv.name, [])
		iv.assessments = hr_assessments(iv.name)
	note = frappe.db.get_value("Shortlisting Note", {"job_opening": app.job_opening}, "name")
	row = frappe.db.get_value("Final Shortlist Row", {"parenttype": "Shortlisting Note", "parent": note or "", "application": application}, ["remarks"], as_dict=True)
	return {"interviews": interviews, "final_shortlisted": 1 if row else 0, "final_shortlist_remarks": (row or {}).get("remarks") or ""}


# ----------------------------------------------------------- interview schedule (step 16)
# Workflow folder "6. Final Interview / Interview Call Letter": candidates
# join twenty minutes (Round 1: ten) before their slot; the panel gets the
# day's running order.

SCHEDULE_HTML = """
<style>
	body { font-family: Arial, sans-serif; font-size: 11px; color: #111; }
	h1 { font-size: 15px; text-align: center; margin: 0 0 2px; }
	h2 { font-size: 12px; text-align: center; margin: 0 0 10px; letter-spacing: .5px; }
	table { width: 100%; border-collapse: collapse; }
	td, th { border: 1px solid #555; padding: 5px 6px; vertical-align: top; }
	th { background: #f2e6e8; text-align: center; }
	.meta td { border: none; padding: 2px 0; }
	.num { text-align: center; }
	ol { margin: 6px 0 0 16px; padding: 0; }
</style>
{{ letterhead }}
<h2>INTERVIEW SCHEDULE | {{ round_label | upper }}</h2>
<table class="meta" style="margin-bottom:8px">
	<tr><td><b>Position:</b> {{ job_title }}</td><td><b>Date:</b> {{ date_label }}</td></tr>
	<tr><td><b>Mode:</b> {{ mode_label }}</td><td>{% if panel %}<b>Panel:</b> {{ panel }}{% endif %}</td></tr>
</table>
<table>
	<tr><th style="width:4%">Sl. No.</th><th>Candidate Name</th><th>Candidate ID</th><th>Day &amp; Date</th><th>Time (IST)</th><th>Login by</th><th>Meeting link / Venue</th><th>RSVP</th></tr>
	{% for r in rows %}
	<tr>
		<td class="num">{{ loop.index }}</td><td>{{ r.candidate_name }}</td><td>{{ r.application_id }}</td><td>{{ r.day }}, {{ r.date }}</td>
		<td class="num">{{ r.time }}</td><td class="num">{{ r.login_time }}</td><td style="word-break:break-all">{{ r.where }}</td><td class="num">{{ r.rsvp }}</td>
	</tr>
	{% endfor %}
</table>
<p style="margin-top:10px"><b>Please note:</b></p>
<ol>
	<li>Candidates are asked to log in {{ login_minutes }} minutes before their start time; they are admitted once the {{ 'committee' if is_final else 'panel' }} is ready.</li>
	<li>The recruitment team joins 20 minutes before the first interview.</li>
	<li>Please keep this schedule and the candidates' documents confidential.</li>
</ol>
"""


def schedule_data(job_opening, round_type="Final", interview_date=None):
	"""The rows of the interview schedule (no permission check)."""
	if round_type not in ROUNDS:
		frappe.throw(_("Unknown interview round."))
	apps = frappe.get_all("Application", filters={"job_opening": job_opening}, pluck="name")
	interviews = frappe.get_all(
		"Interview",
		filters={"application": ["in", apps or [""]], "round_type": round_type, "status": ["!=", "Cancelled"]},
		fields=["name", "application", "candidate_name", "scheduled_datetime", "mode", "meeting_platform", "meeting_link", "location", "rsvp_status", "application.application_id as application_id"],
		order_by="scheduled_datetime asc",
	)
	if interview_date:
		day = frappe.utils.getdate(interview_date)
		interviews = [iv for iv in interviews if iv.scheduled_datetime and iv.scheduled_datetime.date() == day]
	login_minutes = 20 if round_type == "Final" else 10
	rows = []
	for iv in interviews:
		when = get_datetime(iv.scheduled_datetime)
		where = iv.location if iv.mode == "In-Person" else " ".join(x for x in ((iv.meeting_platform or ""), (iv.meeting_link or "")) if x)
		rows.append(
			{
				"candidate_name": iv.candidate_name, "application_id": iv.application_id, "day": when.strftime("%A"), "date": when.strftime("%d %b %Y"),
				"time": when.strftime("%I:%M %p").lstrip("0"), "login_time": add_to_date(when, minutes=-login_minutes).strftime("%I:%M %p").lstrip("0"),
				"mode": "In person" if iv.mode == "In-Person" else "Online", "where": where or "", "rsvp": iv.rsvp_status or "Pending", "datetime": when,
			}
		)
	job = frappe.db.get_value("Job Opening", job_opening, ["job_title", "track"], as_dict=True)
	committee = frappe.db.get_value("Selection Committee", {"job_opening": job_opening}, "name")
	if round_type == "Final" and committee:
		panel = ", ".join(frappe.utils.get_fullname(m) for m in frappe.get_all("Committee Member Row", filters={"parent": committee, "parenttype": "Selection Committee"}, order_by="idx asc", pluck="member"))
	else:
		people = []
		for r in frappe.get_all("Interview HR Assessor", filters={"parenttype": "Interview", "parent": ["in", [iv.name for iv in interviews] or [""]]}, pluck="assessor"):
			if r not in people:
				people.append(r)
		panel = ", ".join(frappe.utils.get_fullname(u) for u in people)
	days = sorted({r["datetime"].date() for r in rows})
	modes = sorted({r["mode"] for r in rows})
	platforms = sorted({iv.meeting_platform for iv in interviews if iv.meeting_platform and iv.mode != "In-Person"})
	return {
		"job_title": job.job_title,
		"round_label": "Final interview" if round_type == "Final" else "Round 1 (HR interaction)",
		"is_final": round_type == "Final",
		"date_label": ", ".join(frappe.utils.formatdate(d, "dd MMM yyyy") for d in days),
		"mode_label": ", ".join(modes) + (f" ({', '.join(platforms)})" if platforms else ""),
		"panel": panel,
		"rows": rows,
		"login_minutes": login_minutes,
	}


def schedule_pdf(job_opening, round_type="Final", interview_date=None):
	from frappe.utils.pdf import get_pdf

	from pathways.utils.letterhead import letterhead_html

	data = schedule_data(job_opening, round_type, interview_date)
	return get_pdf(frappe.render_template(SCHEDULE_HTML, {**data, "letterhead": letterhead_html()}), {"orientation": "Landscape", "page-size": "A4"})


def schedule_xlsx(job_opening, round_type="Final", interview_date=None):
	from io import BytesIO

	from openpyxl import Workbook
	from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

	data = schedule_data(job_opening, round_type, interview_date)
	wb = Workbook()
	ws = wb.active
	ws.title = "Interview Schedule"
	thin = Side(style="thin", color="999999")
	border = Border(left=thin, right=thin, top=thin, bottom=thin)
	head = ["Sl. No.", "Candidate Name", "Candidate ID", "Day", "Date", "Time (IST)", "Login by", "Mode", "Meeting link / Venue", "RSVP"]
	ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(head))
	ws.cell(1, 1, "National Law School of India University, Bengaluru").font = Font(bold=True, size=14)
	ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(head))
	ws.cell(2, 1, f"Interview Schedule: {data['round_label']} | Position: {data['job_title']}" + (f" | Date: {data['date_label']}" if data["date_label"] else "")).font = Font(bold=True)
	ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=len(head))
	ws.cell(3, 1, f"Panel: {data['panel']}" if data["panel"] else "")
	for c, label in enumerate(head, start=1):
		cell = ws.cell(5, c, label)
		cell.font, cell.border, cell.fill = Font(bold=True), border, PatternFill("solid", fgColor="F2E6E8")
		cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
	for i, r in enumerate(data["rows"], start=1):
		values = [i, r["candidate_name"], r["application_id"], r["day"], r["date"], r["time"], r["login_time"], r["mode"], r["where"], r["rsvp"]]
		for c, value in enumerate(values, start=1):
			cell = ws.cell(5 + i, c, value)
			cell.border = border
			cell.alignment = Alignment(vertical="top", wrap_text=True)
	for col, width in zip("ABCDEFGHIJ", (7, 28, 22, 12, 13, 11, 11, 10, 48, 11)):
		ws.column_dimensions[col].width = width
	buffer = BytesIO()
	wb.save(buffer)
	return buffer.getvalue()


@frappe.whitelist()
def export_interview_schedule(job_opening, round_type="Final", interview_date=None, file_format="xlsx"):
	"""Job page > Interviews > Interview schedule: Excel or PDF, per job and
	(optionally) interview day."""
	if not (_can_manage() or _is_panel_member(job_opening)):
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	job_title = frappe.db.get_value("Job Opening", job_opening, "job_title")
	suffix = f" - {frappe.utils.formatdate(interview_date, 'dd.MM.yyyy')}" if interview_date else ""
	label = "Final" if round_type == "Final" else "Round 1"
	if file_format == "pdf":
		content, ext = schedule_pdf(job_opening, round_type, interview_date), "pdf"
	else:
		content, ext = schedule_xlsx(job_opening, round_type, interview_date), "xlsx"
	frappe.local.response.filename = f"Interview Schedule ({label}) - {job_title}{suffix}.{ext}"
	frappe.local.response.filecontent = content
	frappe.local.response.type = "download"
