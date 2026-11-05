# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""The candidate's reply to an interview on the portal: Confirm, Request
reschedule (reason + 1-3 preferred times) or Withdraw, and a new time from
the recruitment team resetting the reply."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, add_to_date, get_datetime, now_datetime

from pathways.api import interviews
from pathways.permissions import CANDIDATE_ROLE


class TestInterviewRSVP(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		track = "Admin" if frappe.db.exists("Recruitment Track", "Admin") else frappe.db.get_value("Recruitment Track", {}, "name")
		job = frappe.get_doc(
			{
				"doctype": "Job Opening", "job_title": "Test RSVP Post", "track": track,
				"department": frappe.db.get_value("Pathways Department", {}, "name"), "employment_type": "Permanent", "vacancies": 1,
			}
		)
		job.flags.ignore_mandatory = True
		job.insert(ignore_permissions=True)
		self.email = f"rsvp-{frappe.generate_hash(length=6)}@example.com"
		user = frappe.get_doc({"doctype": "User", "email": self.email, "first_name": "RSVP", "user_type": "Website User", "send_welcome_email": 0})
		user.insert(ignore_permissions=True)
		user.add_roles(CANDIDATE_ROLE)
		candidate = frappe.get_doc(
			{
				"doctype": "Candidate", "full_name": "RSVP Candidate", "email": self.email,
				"mobile_number": "96" + frappe.generate_hash(length=8).translate(str.maketrans("abcdef", "123456"))[:8],
			}
		)
		candidate.flags.ignore_validate = True
		candidate.insert(ignore_permissions=True)
		app = frappe.get_doc({"doctype": "Application", "candidate": candidate.name, "job_opening": job.name, "resume_attachment": "/private/files/rsvp-cv.pdf"})
		app.flags.ignore_validate = True
		app.flags.ignore_mandatory = True
		app.insert(ignore_permissions=True)
		frappe.db.set_value("Application", app.name, "status", "Shortlisted")
		self.app, self.job = app.name, job.name
		self.start = get_datetime(add_days(now_datetime(), 3)).replace(hour=10, minute=0, second=0, microsecond=0)
		self.iv = interviews.schedule_interviews(job.name, [app.name], "HR Interaction", str(self.start), meeting_link="https://zoom.us/j/9", send_invite=0)["interviews"][0]

	def tearDown(self):
		frappe.set_user("Administrator")

	def _reply(self, response, **kwargs):
		frappe.set_user(self.email)
		try:
			with patch("pathways.utils.communication.send_event") as send:
				result = interviews.respond_rsvp(self.iv, response, **kwargs)
			return result, send
		finally:
			frappe.set_user("Administrator")

	def _slot(self, days, hour=11):
		return get_datetime(add_days(now_datetime(), days)).replace(hour=hour, minute=30, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")

	def test_confirm_records_and_notifies(self):
		result, send = self._reply("Confirmed")
		self.assertEqual(result["rsvp_status"], "Confirmed")
		iv = frappe.get_doc("Interview", self.iv)
		self.assertEqual(iv.rsvp_status, "Confirmed")
		self.assertTrue(iv.rsvp_responded_on)
		self.assertEqual(send.call_args.args[0], "interview_rsvp_update")
		self.assertRaises(frappe.ValidationError, self._reply, "Confirmed")  # same reply twice

	def test_reschedule_needs_reason_and_valid_times(self):
		self.assertRaises(frappe.ValidationError, self._reply, "Reschedule Requested", reason="short", preferred_slots=[self._slot(5)])
		reason = "I have a university examination that day."
		self.assertRaises(frappe.ValidationError, self._reply, "Reschedule Requested", reason=reason, preferred_slots=[])
		past = add_to_date(now_datetime(), hours=-2).strftime("%Y-%m-%d %H:%M:%S")
		self.assertRaises(frappe.ValidationError, self._reply, "Reschedule Requested", reason=reason, preferred_slots=[past])
		self.assertRaises(frappe.ValidationError, self._reply, "Reschedule Requested", reason=reason, preferred_slots=[self._slot(90)])
		self.assertRaises(frappe.ValidationError, self._reply, "Reschedule Requested", reason=reason, preferred_slots=[self._slot(5), self._slot(5)])
		self.assertRaises(
			frappe.ValidationError, self._reply, "Reschedule Requested", reason=reason, preferred_slots=[self._slot(d) for d in (4, 5, 6, 7)]
		)
		current = self.start.strftime("%Y-%m-%d %H:%M:%S")
		self.assertRaises(frappe.ValidationError, self._reply, "Reschedule Requested", reason=reason, preferred_slots=[current])

		result, send = self._reply("Reschedule Requested", reason=reason, preferred_slots=frappe.as_json([self._slot(6), self._slot(5)]))
		self.assertEqual(result["rsvp_status"], "Reschedule Requested")
		iv = frappe.get_doc("Interview", self.iv)
		self.assertEqual(iv.rsvp_reason, reason)
		self.assertEqual(len(iv.reschedule_preferences.splitlines()), 2)
		self.assertLess(iv.reschedule_preferences.splitlines()[0], iv.reschedule_preferences.splitlines()[1])  # sorted
		self.assertEqual(len(send.call_args.args[3]["preferred_times"]), 2)
		# Only one open request at a time.
		self.assertRaises(frappe.ValidationError, self._reply, "Reschedule Requested", reason=reason, preferred_slots=[self._slot(8)])

	def test_new_time_from_team_resets_the_request(self):
		self._reply("Reschedule Requested", reason="I am travelling on that date.", preferred_slots=[self._slot(5)])
		with patch("pathways.utils.communication.send_event"):
			interviews.update_interview(self.iv, start=self._slot(5), send_invite=0)
		iv = frappe.get_doc("Interview", self.iv)
		self.assertEqual(iv.rsvp_status, "Pending")
		self.assertFalse(iv.rsvp_reason or iv.reschedule_preferences or iv.rsvp_responded_on)
		self.assertEqual(self._reply("Confirmed")[0]["rsvp_status"], "Confirmed")

	def test_withdraw_is_final(self):
		result, _send = self._reply("Withdrawn", reason="I have accepted another offer.")
		self.assertEqual(result["rsvp_status"], "Withdrawn")
		self.assertRaises(frappe.ValidationError, self._reply, "Confirmed")
		# The old Declined reply is read as Withdrawn.
		frappe.db.set_value("Interview", self.iv, "rsvp_status", "Declined")
		self.assertRaises(frappe.ValidationError, self._reply, "Confirmed")

	def test_only_the_candidate_and_only_open_interviews(self):
		other = f"rsvp-other-{frappe.generate_hash(length=6)}@example.com"
		frappe.get_doc({"doctype": "User", "email": other, "first_name": "Other", "user_type": "Website User", "send_welcome_email": 0}).insert(ignore_permissions=True)
		frappe.get_doc("User", other).add_roles(CANDIDATE_ROLE)
		frappe.set_user(other)
		try:
			self.assertRaises(frappe.PermissionError, interviews.respond_rsvp, self.iv, "Confirmed")
		finally:
			frappe.set_user("Administrator")
		self.assertRaises(frappe.ValidationError, self._reply, "Maybe")
		frappe.db.set_value("Interview", self.iv, "status", "Cancelled")
		self.assertRaises(frappe.ValidationError, self._reply, "Confirmed")

	# ----- the recruitment team's answer (Interviews > Reschedule requests)

	def _request(self, *days):
		slots = [self._slot(d) for d in days]
		self._reply("Reschedule Requested", reason="I am travelling on that date.", preferred_slots=slots)
		return slots

	def _decide(self, decision, **kwargs):
		with patch("pathways.utils.communication.send_event") as send:
			return interviews.decide_reschedule_request(self.iv, decision, **kwargs), send

	def test_accept_moves_to_a_suggested_time_and_keeps_the_venue(self):
		frappe.db.set_value("Interview", self.iv, {"mode": "In-Person", "location": "Room 004", "meeting_link": None})
		slots = self._request(5, 6)
		self.assertRaises(frappe.ValidationError, self._decide, "Accept", preferred_time=self._slot(9))  # not suggested
		result, _send = self._decide("Accept", preferred_time=slots[1])
		self.assertEqual(result["outcome"], "Accepted")
		iv = frappe.get_doc("Interview", self.iv)
		self.assertEqual(get_datetime(iv.scheduled_datetime), get_datetime(slots[1]))
		self.assertEqual((iv.status, iv.rsvp_status, iv.reschedule_outcome), ("Rescheduled", "Pending", "Accepted"))
		self.assertEqual(iv.location, "Room 004")
		self.assertFalse(iv.reschedule_preferences)
		# Answered: nothing left to decide.
		self.assertRaises(frappe.ValidationError, self._decide, "Decline", note="Not possible on that day.")

	def test_decline_keeps_the_time_and_blocks_a_second_request(self):
		self._request(5)
		self.assertRaises(frappe.ValidationError, self._decide, "Decline", note="No.")  # reason too short
		result, send = self._decide("Decline", note="The panel is available only on this date.")
		self.assertEqual(result["outcome"], "Declined")
		self.assertEqual(send.call_args.args[0], "reschedule_request_declined")
		iv = frappe.get_doc("Interview", self.iv)
		self.assertEqual(get_datetime(iv.scheduled_datetime), self.start)
		self.assertEqual((iv.rsvp_status, iv.reschedule_outcome), ("Pending", "Declined"))
		self.assertEqual(iv.reschedule_outcome_note, "The panel is available only on this date.")
		self.assertRaises(frappe.ValidationError, self._reply, "Reschedule Requested", reason="I really cannot make it.", preferred_slots=[self._slot(7)])
		self.assertEqual(self._reply("Confirmed")[0]["rsvp_status"], "Confirmed")
		# A new time from the team clears the decision.
		with patch("pathways.utils.communication.send_event"):
			interviews.update_interview(self.iv, start=self._slot(8), send_invite=0)
		self.assertFalse(frappe.db.get_value("Interview", self.iv, "reschedule_outcome"))

	def test_no_decision_without_an_open_request(self):
		self.assertRaises(frappe.ValidationError, self._decide, "Decline", note="Not possible on that day.")
		self._request(5)
		self.assertRaises(frappe.ValidationError, self._decide, "Maybe")

	def test_interview_stage_for_the_applications_filter(self):
		iv = lambda round_type, status, rsvp="Pending", when="2026-12-01 10:00": frappe._dict(
			round_type=round_type, status=status, rsvp_status=rsvp, scheduled_datetime=get_datetime(when)
		)
		stage = interviews._interview_stage
		self.assertEqual(stage([]), "No interview")
		self.assertEqual(stage([iv("HR Interaction", "Scheduled")]), "Round 1 scheduled")
		self.assertEqual(stage([iv("HR Interaction", "Rescheduled", "Reschedule Requested")]), "Reschedule requested")
		self.assertEqual(stage([iv("HR Interaction", "Scheduled", "Declined")]), "Withdrawn from interview")
		self.assertEqual(stage([iv("HR Interaction", "Completed")]), "Round 1 completed")
		# An open final interview wins over the completed Round 1.
		self.assertEqual(stage([iv("HR Interaction", "Completed"), iv("Final", "Scheduled")]), "Final scheduled")
		self.assertEqual(stage([iv("HR Interaction", "Completed"), iv("Final", "Completed")]), "Final completed")
		self.assertEqual(stage([iv("HR Interaction", "Cancelled")]), "Interview cancelled")
		self.assertEqual(set(interviews.INTERVIEW_STAGES), {
			"No interview", "Round 1 scheduled", "Reschedule requested", "Withdrawn from interview",
			"Round 1 completed", "Final scheduled", "Final completed", "Interview cancelled",
		})
