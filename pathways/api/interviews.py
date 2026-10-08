# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Interview stage (workflow steps 13-16): the job's Selection Committee,
scheduling Round 1 (HR interaction) and Final interviews with the invite
emails, and the candidate's RSVP."""

import frappe
from frappe import _
from frappe.utils import add_to_date, cint, get_datetime, get_url

from pathways.permissions import CANDIDATE_ROLE, has_full_access

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
		fields=["name", "application", "round_type", "status", "scheduled_datetime", "mode", "meeting_platform", "meeting_link", "location", "rsvp_status"],
		order_by="scheduled_datetime asc",
	)
	by_app = {}
	for iv in interviews:
		by_app.setdefault(iv.application, {})[iv.round_type] = iv
	rows = []
	for a in apps:
		rounds = by_app.get(a.name, {})
		if a.status == "Not Selected" and not rounds:
			continue
		rows.append({**a, "rounds": {r: rounds.get(r) for r in ROUNDS}})

	settings = frappe.get_cached_doc("Pathways Settings")
	return {
		"candidates": rows,
		"committee": _committee(job_opening),
		"committee_size": {
			"min": cint(settings.get("min_selection_committee_size")) or 3,
			"max": cint(settings.get("max_selection_committee_size")) or 5,
		},
		"can_manage": manage,
	}


# ----------------------------------------------------------- committee


@frappe.whitelist()
def get_panel_options():
	_require_manage()
	return frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Guest", "Administrator"]]},
		fields=["name", "full_name"],
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
	return _committee(job_opening)


def _time_label(value):
	if not value:
		return ""
	return frappe.utils.format_time(value, "h:mm a")


# ----------------------------------------------------------- scheduling


@frappe.whitelist(methods=["POST"])
def schedule_interviews(
	job_opening, applications, round_type, start, slot_minutes=0, mode="Video Conference", meeting_link=None,
	meeting_platform=None, rsvp_deadline=None, send_invite=1, location=None, create_meet=0,
):
	"""Schedule (or reschedule) one round for several candidates. Each
	candidate gets the next slot: start, start + slot, ... The invite (Round
	1) or call letter (Final) goes to each candidate."""
	_require_manage()
	if round_type not in ROUNDS:
		frappe.throw(_("Unknown interview round."))
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
		iv.save(ignore_permissions=True)
		# A new Meet link, or move the event a Meet link was made with before.
		if create_meet or (iv.get("calendar_event") and not in_person and _meet_calendar()):
			_sync_meet_event(iv, app, slot_minutes or 30, committee)
		elif in_person:
			_cancel_meet_event(iv)

		if app.status == "Shortlisted":
			app.status = "Interview Scheduled"
			app.save(ignore_permissions=True)
		app.add_comment(
			"Info",
			_("{0} interview {1} for {2} by {3}.").format(
				_(round_type), _("rescheduled") if existing else _("scheduled"),
				frappe.utils.format_datetime(when, "dd MMM yyyy, h:mm a"), frappe.utils.get_fullname(frappe.session.user),
			),
		)
		if cint(send_invite):
			_send_invite(iv, app, meeting_platform, rsvp_deadline)
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
	candidate = frappe.db.get_value("Candidate", app.candidate, ["full_name", "email"], as_dict=True) or {}
	job_title = frappe.db.get_value("Job Opening", app.job_opening, "job_title")
	start = get_datetime(iv.scheduled_datetime)
	end = add_to_date(start, minutes=max(cint(minutes), 15))
	emails = [candidate.get("email")]
	if iv.round_type == "Final" and committee:
		emails += frappe.get_all("Committee Member Row", filters={"parent": committee, "parenttype": "Selection Committee"}, pluck="member")
	participants = [
		{"reference_doctype": "Interview", "reference_docname": iv.name, "email": e}
		for e in dict.fromkeys(e for e in emails if e and e != "Administrator" and "@" in e)
	]
	subject = _("{0} interview: {1}, {2}").format(
		_("Round 1 (HR)") if iv.round_type == "HR Interaction" else _("Final"), candidate.get("full_name") or app.application_id, job_title
	)
	if iv.get("calendar_event") and frappe.db.exists("Event", iv.calendar_event):
		ev = frappe.get_doc("Event", iv.calendar_event)
		ev.update({"subject": subject, "starts_on": start, "ends_on": end, "status": "Open"})
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


def _cancel_meet_event(iv):
	if iv.get("calendar_event") and frappe.db.exists("Event", iv.calendar_event):
		ev = frappe.get_doc("Event", iv.calendar_event)
		ev.status = "Cancelled"
		ev.save(ignore_permissions=True)


def _send_invite(iv, app, meeting_platform=None, rsvp_deadline=None):
	from pathways.utils.communication import candidate_email_context, send_event

	when = get_datetime(iv.scheduled_datetime)
	context, candidate = candidate_email_context(app)
	context.update(
		{
			"interview_date_time": frappe.utils.format_datetime(when, "EEEE, dd MMM yyyy 'at' h:mm a"),
			"interview_date": when.strftime("%d %b %Y"),
			"interview_day": when.strftime("%A"),
			"interview_time": when.strftime("%I:%M %p").lstrip("0") + " (IST)",
			"login_time": add_to_date(when, minutes=-20).strftime("%I:%M %p").lstrip("0"),
			"interview_mode": "Online" if iv.mode == "Video Conference" else "In person",
			"meeting_platform": meeting_platform or iv.get("meeting_platform") or "Microsoft Teams",
			"meeting_link": iv.meeting_link or "",
			"interview_location": iv.get("location") or "",
			"rsvp_deadline": frappe.utils.format_datetime(rsvp_deadline, "dd MMM yyyy, h:mm a") if rsvp_deadline else "",
			"rsvp_link": get_url(f"/pathways/portal/applications/{app.name}"),
		}
	)
	send_event(INVITE_EVENT[iv.round_type], "Interview", iv.name, context, candidate=candidate)


@frappe.whitelist(methods=["POST"])
def resend_invite(interview, meeting_platform=None, rsvp_deadline=None):
	_require_manage()
	iv = frappe.get_doc("Interview", interview)
	_send_invite(iv, frappe.get_doc("Application", iv.application), meeting_platform, rsvp_deadline)
	return True


@frappe.whitelist(methods=["POST"])
def set_interview_status(interview, status):
	"""Mark an interview Completed or Cancelled. A completed Final moves the
	application to Interview Completed."""
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
	app.add_comment("Info", _("{0} interview marked {1} by {2}.").format(_(iv.round_type), _(status).lower(), frappe.utils.get_fullname(frappe.session.user)))
	return {"status": iv.status, "application_status": app.status}


# ----------------------------------------------------------- RSVP


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
	iv.db_set("rsvp_status", response)
	frappe.get_doc("Application", iv.application).add_comment(
		"Info", _("Candidate {0} the {1} interview on {2}.").format(
			_("confirmed") if response == "Confirmed" else _("declined"), _(iv.round_type),
			frappe.utils.format_datetime(iv.scheduled_datetime, "dd MMM yyyy, h:mm a"),
		),
	)
	return response


# ----------------------------------------------------------- all interviews


@frappe.whitelist()
def list_interviews():
	"""Interviews page: every interview the user may see, with names."""
	rows = frappe.get_list(
		"Interview",
		fields=[
			"name", "application", "round_type", "status", "scheduled_datetime", "mode", "meeting_platform", "meeting_link", "location", "rsvp_status",
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
	for r in rows:
		a = apps.get(r.application) or {}
		r.candidate_name = a.get("candidate_name")
		r.job_title = a.get("job_title")
	return rows


@frappe.whitelist()
def list_to_schedule():
	"""Interviews page > To schedule: shortlisted candidates with no open
	interview yet, grouped by job, for the recruitment team."""
	if not _can_manage():
		return []
	apps = frappe.get_all(
		"Application",
		filters={"status": "Shortlisted"},
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
	for iv in frappe.get_all(
		"Interview",
		filters={"application": ["in", [a.name for a in apps]], "status": ["in", ["Cancelled", "Completed"]]},
		fields=["application", "round_type", "status"],
		order_by="scheduled_datetime asc",
	):
		label = _("Round 1") if iv.round_type == "HR Interaction" else _("Final")
		history.setdefault(iv.application, []).append(f"{label} {_(iv.status).lower()}")
	committees = {
		c.job_opening: c
		for c in frappe.get_all(
			"Selection Committee",
			filters={"job_opening": ["in", list({a.job_opening for a in apps})]},
			fields=["job_opening", "scheduled_date", "scheduled_time"],
		)
	}
	jobs = {}
	for a in apps:
		if a.name in booked:
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
			}
		)
	return sorted(jobs.values(), key=lambda j: (-len(j["candidates"]), j["job_title"] or ""))
