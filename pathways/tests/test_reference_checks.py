# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Reference checks (workflow step 21): prefill from the application's
referees, the referee link (issue, validate, expiry, one submission),
recording by the recruiter, and that candidates can never read responses."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from pathways.api import reference_checks as rc
from pathways.patches.v1_0.seed_reference_check_templates import seed_reference_check_templates

TRACK = "Admin"


class TestReferenceChecks(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("Recruitment Track", TRACK):
			frappe.get_doc({"doctype": "Recruitment Track", "track_name": TRACK, "is_active": 1}).insert(ignore_permissions=True)
		seed_reference_check_templates()
		department = frappe.db.get_value("Pathways Department", {}, "name")
		if not department:
			department = frappe.get_doc({"doctype": "Pathways Department", "department_name": "RC Test Dept"}).insert(ignore_permissions=True).name
		cls.job = frappe.get_doc(
			{
				"doctype": "Job Opening",
				"job_title": "RC Test Officer",
				"track": TRACK,
				"department": department,
				"employment_type": "Permanent",
				"vacancies": 1,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

	def setUp(self):
		frappe.set_user("Administrator")
		email = f"rc-cand-{frappe.generate_hash(length=8)}@example.com"
		self.candidate = frappe.get_doc(
			{"doctype": "Candidate", "full_name": "Asha Rao", "email": email, "mobile_number": "9876543210"}
		).insert(ignore_permissions=True)
		self.app = frappe.get_doc(
			{
				"doctype": "Application",
				"candidate": self.candidate.name,
				"job_opening": self.job.name,
				"references": [
					{
						"referee_name": "Dr. Meera Iyer",
						"current_designation_org": "Professor, XYZ University",
						"relationship": "Former supervisor",
						"email": "meera@example.com",
						"mobile": "9000000001",
					},
					{
						"referee_name": "Ravi Kumar",
						"current_designation_org": "Manager, ABC Ltd",
						"relationship": "Colleague",
						"email": "ravi@example.com",
						"mobile": "9000000002",
					},
				],
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def _create(self):
		rc.create_checks(self.app.name)
		return frappe.get_all("Reference Check", filters={"application": self.app.name}, pluck="name", order_by="creation asc")

	def _send(self, check):
		with patch("pathways.utils.communication.send_event") as send:
			out = rc.send_request(check)
		return out["form_link"].rsplit("/", 1)[1], send

	def _answers(self, form, text="Good"):
		answers = {}
		for q in form["questions"]:
			if q["answer_type"] == "Rating 1-5":
				answers[q["name"]] = {"rating_value": 4}
			elif q["answer_type"] == "Yes-No":
				answers[q["name"]] = {"answer_text": "Yes"}
			else:
				answers[q["name"]] = {"answer_text": text}
		return answers

	# ------------------------------------------------------------ prefill

	def test_prefill_from_application_referees(self):
		"""Step 21: starting checks creates one per referee the candidate gave, using the track's
		template with {position} filled in. Starting again is refused; an extra referee can be added.
		"""
		names = self._create()
		self.assertEqual(len(names), 2)
		check = frappe.get_doc("Reference Check", names[0])
		self.assertEqual(check.referee_name, "Dr. Meera Iyer")
		self.assertEqual(check.referee_email, "meera@example.com")
		self.assertEqual(check.relationship_to_candidate, "Former supervisor")
		self.assertEqual(check.candidate_name, "Asha Rao")
		self.assertEqual(check.template, "Admin Reference Check")
		self.assertEqual(check.status, "Pending")
		# The template's questions are copied in, with {position} filled.
		self.assertGreater(len(check.responses), 5)
		self.assertTrue(any("RC Test Officer" in r.question_text for r in check.responses))

		# Running again creates nothing new; an extra referee can be added.
		self.assertRaises(frappe.ValidationError, rc.create_checks, self.app.name)
		rc.create_checks(self.app.name, referees=[{"referee_name": "Extra Person", "referee_email": "extra@example.com"}])
		data = rc.get_application_checks(self.app.name)
		self.assertEqual(len(data["checks"]), 3)
		self.assertTrue(all(r["added"] for r in data["referees"]))

	# ------------------------------------------------------------ token

	def test_token_issue_validate_and_one_time_submit(self):
		"""Step 21 (referee form): sending emails the referee a link whose token is stored only as a
		hash. A guest can open it, required answers are enforced, submitting emails the recruiter,
		and the link works only once. Staff cannot overwrite the referee's answers.
		"""
		name = self._create()[0]
		token, send = self._send(name)
		send.assert_called_once()
		self.assertEqual(send.call_args.args[0], "reference_request")
		self.assertEqual(send.call_args.kwargs["recipients"][0]["email"], "meera@example.com")

		check = frappe.get_doc("Reference Check", name)
		self.assertEqual(check.status, "In Progress")
		self.assertEqual(check.mode, "Referee form")
		# Only the hash is stored.
		self.assertNotEqual(check.access_token_hash, token)
		self.assertNotIn(token, frappe.as_json(check.as_dict()))

		frappe.set_user("Guest")
		self.assertEqual(rc.get_referee_form("not-a-real-token")["state"], "invalid")
		form = rc.get_referee_form(token)
		self.assertEqual(form["state"], "open")
		self.assertEqual(form["candidate_name"], "Asha Rao")
		self.assertEqual(form["position"], "RC Test Officer")
		self.assertIn("Asha Rao", form["intro"])

		# Required answers are enforced.
		self.assertRaises(frappe.ValidationError, rc.submit_referee_form, token, {})
		with patch("pathways.utils.communication.send_event") as received:
			rc.submit_referee_form(token, self._answers(form, "Excellent colleague"))
		self.assertEqual(received.call_args.args[0], "reference_received")
		self.assertEqual(received.call_args.kwargs["approvers"], ["Administrator"])

		# One submission only.
		self.assertEqual(rc.get_referee_form(token)["state"], "submitted")
		self.assertRaises(frappe.ValidationError, rc.submit_referee_form, token, self._answers(form))

		frappe.set_user("Administrator")
		check.reload()
		self.assertEqual(check.status, "Completed")
		self.assertTrue(check.completed_on)
		self.assertIn("Excellent colleague", [r.answer_text for r in check.responses])
		# The referee's own answers cannot be overwritten by staff.
		self.assertRaises(frappe.ValidationError, rc.record_responses, name, {}, None, 1)

	def test_token_expiry_and_resend(self):
		"""An expired link cannot be opened or submitted. Resending issues a new link and the old one
		stops working.
		"""
		name = self._create()[0]
		token, _send = self._send(name)
		frappe.db.set_value("Reference Check", name, "token_expires_on", add_days(now_datetime(), -1))
		frappe.set_user("Guest")
		self.assertEqual(rc.get_referee_form(token)["state"], "expired")
		self.assertRaises(frappe.ValidationError, rc.submit_referee_form, token, {})

		# Resending issues a new link and the old one stops working.
		frappe.set_user("Administrator")
		new_token, _send = self._send(name)
		self.assertNotEqual(new_token, token)
		frappe.set_user("Guest")
		self.assertEqual(rc.get_referee_form(token)["state"], "invalid")
		self.assertEqual(rc.get_referee_form(new_token)["state"], "open")

	def test_reminder_keeps_previous_link_working(self):
		"""The daily reminder is sent once after the configured days, and both the original and the
		reminder links stay valid.
		"""
		frappe.db.set_single_value("Pathways Settings", "reference_reminder_after_days", 3)
		name = self._create()[0]
		token, _send = self._send(name)
		frappe.db.set_value("Reference Check", name, "requested_on", add_days(now_datetime(), -4))
		with patch("pathways.utils.communication.send_event") as send:
			rc.send_reminders()
			rc.send_reminders()  # only one reminder
		events = [c.args[0] for c in send.call_args_list if c.args[2] == name]
		self.assertEqual(events, ["reference_reminder"])
		reminder_token = send.call_args.args[3]["form_link"].rsplit("/", 1)[1]
		frappe.set_user("Guest")
		self.assertEqual(rc.get_referee_form(token)["state"], "open")
		self.assertEqual(rc.get_referee_form(reminder_token)["state"], "open")

	# ------------------------------------------------------------ recruiter

	def test_recruiter_records_answers(self):
		"""Step 21 (by phone): the recruiter can save partial answers as a draft, then complete with a
		summary. The per-application summary counts completed and pending checks.
		"""
		name = self._create()[1]
		check = frappe.get_doc("Reference Check", name)
		answers = {r.name: {"answer_text": "Said on the phone"} for r in check.responses}
		# Saving a draft does not need every answer.
		rc.record_responses(name, {check.responses[0].name: {"answer_text": "Partial"}}, None, 0)
		self.assertEqual(frappe.db.get_value("Reference Check", name, "status"), "In Progress")
		out = rc.record_responses(name, answers, "Strong reference overall.", 1)
		self.assertEqual(out["status"], "Completed")
		self.assertEqual(out["mode"], "Recorded by recruiter")
		self.assertEqual(out["recorded_by"], "Administrator")
		self.assertEqual(out["overall_assessment_summary"], "Strong reference overall.")
		self.assertTrue(all(r["answer_text"] == "Said on the phone" for r in out["responses"]))

		summary = rc.summary_for_applications([self.app.name])
		self.assertEqual(summary[self.app.name], {"total": 2, "completed": 1, "in_progress": 0, "pending": 1})

	def test_rating_validated(self):
		"""Rating answers must be within 1-5."""
		tpl = frappe.get_doc("Reference Check Template", "Research Reference Check")
		self.assertTrue(any(q.answer_type == "Rating 1-5" for q in tpl.questions))
		name = self._create()[0]
		check = frappe.get_doc("Reference Check", name)
		check.responses[0].answer_type = "Rating 1-5"
		check.save()
		self.assertRaises(frappe.ValidationError, rc.record_responses, name, {check.responses[0].name: {"rating_value": 9}}, None, 0)

	# ------------------------------------------------------------ candidate

	def test_candidate_cannot_read_reference_checks(self):
		"""A candidate can never see, list, send or record their reference checks."""
		name = self._create()[0]
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": self.candidate.email,
				"first_name": "Asha",
				"send_welcome_email": 0,
				"user_type": "Website User",
				"roles": [{"role": "Pathways Candidate"}],
			}
		).insert(ignore_permissions=True)
		frappe.set_user(user.name)
		self.assertFalse(frappe.has_permission("Reference Check", "read"))
		self.assertFalse(frappe.has_permission("Reference Check", "read", doc=name))
		self.assertEqual(rc.get_application_checks(self.app.name), {"can_view": False})
		self.assertEqual(rc.summary_for_applications([self.app.name]), {})
		self.assertRaises(frappe.PermissionError, rc.send_request, name)
		self.assertRaises(frappe.PermissionError, rc.record_responses, name, {}, None, 0)
		self.assertRaises(frappe.PermissionError, frappe.get_list, "Reference Check")

	# ------------------------------------------------------------ email + print

	def test_request_email_goes_to_referee_and_prints(self):
		"""The request email is actually delivered to the referee's address (logged), and the
		Reference Check print format renders.
		"""
		from pathways.utils.communication import _send_event

		name = self._create()[0]
		_send_event(
			rule_event="reference_request",
			reference_doctype="Reference Check",
			reference_name=name,
			context={"candidate_name": "Asha Rao", "job_title": "RC Test Officer", "referee_name": "Dr. Meera Iyer", "form_link": "https://x/y", "expires_on": "1 Jan 2027"},
			extra_recipients=[("meera@example.com", "Dr. Meera Iyer")],
		)
		self.assertTrue(
			frappe.db.exists("Communication Log", {"reference_doctype": "Reference Check", "reference_name": name, "recipient": "meera@example.com"})
		)
		html = frappe.get_print("Reference Check", name, print_format="Reference Check")
		self.assertIn("Dr. Meera Iyer", html)
		self.assertIn("Asha Rao", html)


class TestRefereeEndpointsOverHTTP(IntegrationTestCase):
	"""The referee endpoints are reachable as Guest and rate-limited."""

	def test_guest_access_and_rate_limit(self):
		"""Over HTTP, guests can call the referee endpoints without logging in; a bad token is refused,
		and repeated submissions are rate-limited (HTTP 429).
		"""
		from frappe.tests.test_api import FrappeAPITestCase

		client = FrappeAPITestCase()
		frappe.cache.delete_keys("rl:pathways.api.reference_checks")
		url = client.method("pathways.api.reference_checks.get_referee_form")
		response = client.get(url, {"token": "no-such-token"})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json["message"]["state"], "invalid")

		submit = client.method("pathways.api.reference_checks.submit_referee_form")
		codes = [client.post(submit, {"token": "no-such-token", "answers": "{}"}).status_code for _ in range(11)]
		self.assertEqual(codes[0], 403)
		self.assertEqual(codes[-1], 429)
		frappe.cache.delete_keys("rl:pathways.api.reference_checks")
