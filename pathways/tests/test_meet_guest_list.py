# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Google Meet interviews: the calendar event hides its guest list, so a
candidate never sees who is on the panel (Google Calendar is faked)."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, get_datetime, now_datetime

from pathways.api import interviews

GC = "frappe.integrations.doctype.google_calendar.google_calendar.get_google_calendar_object"


class FakeEvents:
	"""Records what Pathways sends to the Google Calendar events API."""

	def __init__(self):
		self.calls = []

	def _call(self, kind, **kwargs):
		self.calls.append((kind, kwargs))
		result = {"id": "g-event-1", "hangoutLink": "https://meet.google.com/abc-defg-hij"}
		return type("Req", (), {"execute": lambda _self: result})()

	def insert(self, **kwargs):
		return self._call("insert", **kwargs)

	def patch(self, **kwargs):
		return self._call("patch", **kwargs)

	def get(self, **kwargs):
		self.calls.append(("get", kwargs))
		event = {"id": "g-event-1", "guestsCanSeeOtherGuests": False, "attendees": [], "hangoutLink": "https://meet.google.com/abc-defg-hij"}
		return type("Req", (), {"execute": lambda _self: dict(event)})()

	def update(self, **kwargs):
		return self._call("update", **kwargs)


class FakeService:
	def __init__(self):
		self.ev = FakeEvents()

	def events(self):
		return self.ev


class TestMeetGuestList(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.calendar = "Pathways Test Calendar"
		if not frappe.db.exists("Google Calendar", self.calendar):
			cal = frappe.get_doc({"doctype": "Google Calendar", "calendar_name": self.calendar, "user": "Administrator", "enable": 1, "push_to_google_calendar": 1})
			cal.flags.ignore_mandatory = True
			cal.flags.ignore_links = True
			cal.flags.ignore_validate = True
			cal.insert(ignore_permissions=True)
		track = "Admin" if frappe.db.exists("Recruitment Track", "Admin") else frappe.db.get_value("Recruitment Track", {}, "name")
		job = frappe.get_doc(
			{
				"doctype": "Job Opening", "job_title": "Test Meet Post", "track": track,
				"department": frappe.db.get_value("Pathways Department", {}, "name"), "employment_type": "Permanent", "vacancies": 1,
			}
		)
		job.flags.ignore_mandatory = True
		job.insert(ignore_permissions=True)
		candidate = frappe.get_doc(
			{
				"doctype": "Candidate", "full_name": "Meet Candidate", "email": f"meet-{frappe.generate_hash(length=6)}@example.com",
				"mobile_number": "95" + frappe.generate_hash(length=8).translate(str.maketrans("abcdef", "123456"))[:8],
			}
		)
		candidate.flags.ignore_validate = True
		candidate.insert(ignore_permissions=True)
		app = frappe.get_doc({"doctype": "Application", "candidate": candidate.name, "job_opening": job.name, "resume_attachment": "/private/files/meet-cv.pdf"})
		app.flags.ignore_validate = True
		app.flags.ignore_mandatory = True
		app.insert(ignore_permissions=True)
		frappe.db.set_value("Application", app.name, "status", "Shortlisted")
		self.app, self.job, self.candidate_email = app.name, job.name, candidate.email
		self.start = get_datetime(add_days(now_datetime(), 3)).replace(hour=10, minute=0, second=0, microsecond=0)

	def _patches(self, service):
		return (
			patch(GC, return_value=(service, frappe._dict(push_to_google_calendar=1))),
			patch.object(interviews, "_meet_calendar", return_value=self.calendar),
			patch.object(interviews, "_google_calendar_id", return_value="cal-1@group.calendar.google.com"),
			patch("pathways.utils.communication.send_event"),
		)

	def test_new_meet_event_hides_the_guest_list(self):
		service = FakeService()
		p1, p2, p3, p4 = self._patches(service)
		with p1, p2, p3, p4:
			iv = interviews.schedule_interviews(self.job, [self.app], "HR Interaction", str(self.start), create_meet=1, send_invite=0)["interviews"][0]
		inserts = [kw for kind, kw in service.ev.calls if kind == "insert"]
		self.assertEqual(len(inserts), 1)
		body = inserts[0]["body"]
		self.assertIs(body["guestsCanSeeOtherGuests"], False)
		self.assertIn({"email": self.candidate_email}, body["attendees"])
		self.assertEqual(inserts[0]["sendUpdates"], "all")
		event = frappe.db.get_value("Interview", iv, "calendar_event")
		ev = frappe.db.get_value("Event", event, ["sync_with_google_calendar", "google_calendar_event_id", "google_meet_link"], as_dict=True)
		self.assertEqual((ev.sync_with_google_calendar, ev.google_calendar_event_id), (1, "g-event-1"))
		self.assertEqual(frappe.db.get_value("Interview", iv, "meeting_link"), "https://meet.google.com/abc-defg-hij")

	def test_reschedule_keeps_the_guest_list_hidden(self):
		service = FakeService()
		p1, p2, p3, p4 = self._patches(service)
		with p1, p2, p3, p4:
			iv = interviews.schedule_interviews(self.job, [self.app], "HR Interaction", str(self.start), create_meet=1, send_invite=0)["interviews"][0]
			service.ev.calls.clear()
			interviews.update_interview(iv, start=str(add_days(self.start, 1)), send_invite=0)
		kinds = [kind for kind, _kw in service.ev.calls]
		# Hidden first, quietly; then Frappe's own update keeps what Google returned.
		self.assertEqual(kinds[0], "patch")
		patch_call = service.ev.calls[0][1]
		self.assertEqual((patch_call["body"], patch_call["sendUpdates"]), ({"guestsCanSeeOtherGuests": False}, "none"))
		updates = [kw for kind, kw in service.ev.calls if kind == "update"]
		self.assertTrue(updates)
		self.assertIs(updates[-1]["body"]["guestsCanSeeOtherGuests"], False)
