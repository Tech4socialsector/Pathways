# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Candidate portal notification bell: every candidate email leaves a
portal notification (no second email); candidates see and mark only their
own."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from pathways.permissions import CANDIDATE_ROLE
from pathways.utils import candidate_notifications as cn


def _candidate_user(label):
	email = f"notif-{label}-{frappe.generate_hash(length=6)}@example.com"
	user = frappe.get_doc({"doctype": "User", "email": email, "first_name": label, "user_type": "Website User", "send_welcome_email": 0})
	user.insert(ignore_permissions=True)
	user.add_roles(CANDIDATE_ROLE)
	return email


class TestCandidateNotifications(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.me = _candidate_user("me")
		self.other = _candidate_user("other")
		track = "Admin" if frappe.db.exists("Recruitment Track", "Admin") else frappe.db.get_value("Recruitment Track", {}, "name")
		job = frappe.get_doc(
			{
				"doctype": "Job Opening", "job_title": "Test Notification Post", "track": track,
				"department": frappe.db.get_value("Pathways Department", {}, "name"), "employment_type": "Permanent", "vacancies": 1,
			}
		)
		job.flags.ignore_mandatory = True
		job.insert(ignore_permissions=True)
		candidate = frappe.get_doc(
			{
				"doctype": "Candidate", "full_name": "Notif Candidate", "email": self.me,
				"mobile_number": "94" + frappe.generate_hash(length=8).translate(str.maketrans("abcdef", "123456"))[:8],
			}
		)
		candidate.flags.ignore_validate = True
		candidate.insert(ignore_permissions=True)
		app = frappe.get_doc({"doctype": "Application", "candidate": candidate.name, "job_opening": job.name, "resume_attachment": "/private/files/notif-cv.pdf"})
		app.flags.ignore_validate = True
		app.flags.ignore_mandatory = True
		app.insert(ignore_permissions=True)
		self.app = app.name

	def tearDown(self):
		frappe.set_user("Administrator")

	def _as(self, user, fn, *args, **kwargs):
		frappe.set_user(user)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_notification_is_recorded_without_a_second_email(self):
		queued = frappe.db.count("Email Queue")
		cn.notify_candidate("application_received", self.me, "<b>Application Received</b>: Test", "Application", self.app)
		self.assertEqual(frappe.db.count("Email Queue"), queued)
		log = frappe.get_last_doc("Notification Log", filters={"for_user": self.me})
		self.assertEqual((log.type, log.subject, log.read), ("Alert", "Application Received: Test", 0))
		self.assertEqual(log.link, f"/pathways/portal/applications/{self.app}")

	def test_login_emails_staff_and_unknown_addresses_are_skipped(self):
		cn.notify_candidate("candidate_portal_access", self.me, "Your login", "Candidate", None)
		cn.notify_candidate("application_received", "Administrator", "x", "Application", self.app)
		cn.notify_candidate("application_received", "nobody@example.com", "x", "Application", self.app)
		self.assertFalse(frappe.db.exists("Notification Log", {"for_user": self.me}))
		self.assertFalse(frappe.db.exists("Notification Log", {"for_user": "Administrator", "subject": "x", "type": "Alert"}))

	def test_each_candidate_sees_and_marks_only_their_own(self):
		cn.notify_candidate("application_received", self.me, "Mine one", "Application", self.app)
		cn.notify_candidate("application_received", self.me, "Mine two", "Application", self.app)
		cn.notify_candidate("application_received", self.other, "Theirs", "Application", self.app)
		mine = self._as(self.me, cn.get_my_notifications)
		self.assertEqual(mine["unread"], 2)
		self.assertEqual({n.subject for n in mine["notifications"]}, {"Mine one", "Mine two"})
		theirs = frappe.db.get_value("Notification Log", {"for_user": self.other}, "name")
		# Someone else's notification is ignored, not marked.
		self._as(self.me, cn.mark_my_notifications_read, frappe.as_json([theirs, mine["notifications"][0].name]))
		self.assertEqual(frappe.db.get_value("Notification Log", theirs, "read"), 0)
		self.assertEqual(self._as(self.me, cn.get_my_notifications)["unread"], 1)
		self.assertEqual(self._as(self.me, cn.mark_my_notifications_read)["unread"], 0)
		self.assertEqual(self._as(self.other, cn.get_my_notifications)["unread"], 1)

	def test_staff_and_guests_cannot_use_the_bell(self):
		self.assertRaises(frappe.PermissionError, cn.get_my_notifications)  # Administrator
		self.assertRaises(frappe.PermissionError, self._as, "Guest", cn.get_my_notifications)

	def test_candidate_email_send_creates_the_notification(self):
		from pathways.utils.communication import _send_event

		if not frappe.db.exists("Recruitment Email Rule", "application_received"):
			self.skipTest("application_received email rule not set up")
		with patch("frappe.sendmail"):
			_send_event(
				rule_event="application_received", reference_doctype="Application", reference_name=self.app,
				context={"job_title": "Test Notification Post", "candidate_name": "Notif Candidate", "application_id": self.app},
				candidate={"email": self.me, "name": "Notif Candidate"},
			)
		log = frappe.get_last_doc("Notification Log", filters={"for_user": self.me})
		self.assertIn("Test Notification Post", log.subject)
