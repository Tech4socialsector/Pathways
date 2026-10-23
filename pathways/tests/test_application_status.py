# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Manual status changes (Change Status dialog and bulk change). Offer,
document and joining statuses must match their own records, so an
application can never be labelled "Offer Accepted" with no offer behind it
(which would leave onboarding never started)."""

import random

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from pathways.api import application as api


def _user(email, roles):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"user_type": "System User",
				"send_welcome_email": 0,
				"roles": [{"role": r} for r in roles],
			}
		).insert(ignore_permissions=True)
	return email


class TestApplicationStatus(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		job = frappe.get_doc(
			{
				"doctype": "Job Opening",
				"job_title": f"Status Test Post {frappe.generate_hash(length=5)}",
				"track": frappe.db.get_value("Recruitment Track", {}, "name"),
				"department": frappe.db.get_value("Pathways Department", {}, "name"),
				"employment_type": "Permanent",
				"vacancies": 1,
			}
		)
		job.flags.ignore_mandatory = True
		job.insert(ignore_permissions=True)
		candidate = frappe.get_doc(
			{
				"doctype": "Candidate",
				"full_name": "Status Candidate",
				"email": f"status-{frappe.generate_hash(length=8)}@example.com",
				"mobile_number": "9" + "".join(random.choice("0123456789") for _ in range(9)),
			}
		)
		candidate.flags.ignore_validate = True
		candidate.insert(ignore_permissions=True)
		app = frappe.get_doc({"doctype": "Application", "candidate": candidate.name, "job_opening": job.name})
		app.flags.ignore_validate = True
		app.flags.ignore_mandatory = True
		app.insert(ignore_permissions=True)
		frappe.db.set_value("Application", app.name, "status", "Selected")
		self.app = app.name
		self.job = job.name

	def tearDown(self):
		frappe.set_user("Administrator")

	def _offer(self, status):
		offer = frappe.get_doc({"doctype": "Offer Appointment Order", "application": self.app, "status": "Draft"})
		offer.flags.ignore_validate = True
		offer.flags.ignore_mandatory = True
		offer.insert(ignore_permissions=True)
		# Set directly: this test is about the dialog, not the offer's own hooks.
		frappe.db.set_value("Offer Appointment Order", offer.name, "status", status)
		return offer.name

	def _status(self):
		return frappe.db.get_value("Application", self.app, "status")

	def test_offer_statuses_need_a_matching_offer(self):
		"""Even with the override role, Offer Accepted / Joined / Documents Verified cannot be
		set while no offer, joining or checklist backs them; the dialog says how to get there."""
		options = api.get_application_status_options(self.app)
		for status in ("Offer Extended", "Offer Accepted", "Documents Verified", "Joined"):
			self.assertNotIn(status, options["options"])
			self.assertRaises(frappe.ValidationError, api.set_application_status, self.app, status)
		reasons = {r["status"]: r["reason"] for r in options["unavailable"]}
		self.assertIn("portal", reasons["Offer Accepted"])
		self.assertEqual(self._status(), "Selected")

	def test_status_can_be_repaired_to_match_the_offer(self):
		"""When the label has drifted from an accepted offer, the override role can set it back
		to Offer Accepted, but not to Offer Declined, which the offer does not support."""
		self._offer("Accepted")
		self.assertEqual(api.set_application_status(self.app, "Offer Accepted"), "Offer Accepted")
		self.assertRaises(frappe.ValidationError, api.set_application_status, self.app, "Offer Declined")

	def test_live_offer_blocks_moving_back(self):
		"""While an offer is in progress the application cannot be moved back by hand (that would
		hide a live offer); once the offer is declined, Not Selected is allowed again."""
		offer = self._offer("Sent")
		for status in ("Under Review", "Shortlisted", "Not Selected"):
			self.assertRaises(frappe.ValidationError, api.set_application_status, self.app, status)
		reasons = {r["status"]: r["reason"] for r in api.get_application_status_options(self.app)["unavailable"]}
		self.assertIn(offer, reasons["Under Review"])

		frappe.db.set_value("Offer Appointment Order", offer, "status", "Declined")
		self.assertEqual(api.set_application_status(self.app, "Not Selected"), "Not Selected")

	def test_screening_statuses_stay_free_without_records(self):
		"""With no offer or joining, staff move an application through screening and selection
		freely; a recruiter without the override role cannot withdraw it."""
		recruiter = _user("status-recruiter@example.com", ["Pathways Recruiter"])
		frappe.set_user(recruiter)
		options = api.get_application_status_options(self.app)["options"]
		for status in ("Under Review", "Shortlisted", "Interview Completed", "Not Selected"):
			self.assertIn(status, options)
		self.assertNotIn("Withdrawn", options)
		self.assertEqual(api.set_application_status(self.app, "Interview Completed"), "Interview Completed")

	def test_joining_record_decides_joined(self):
		"""Joined can be set by hand only when the joining record says Joined."""
		self._offer("Accepted")
		joining = frappe.get_doc(
			{"doctype": "Joining", "application": self.app, "confirmed_doj": add_days(today(), -1), "status": "Confirmed"}
		)
		joining.flags.ignore_validate = True
		joining.flags.ignore_mandatory = True
		joining.flags.ignore_links = True
		joining.insert(ignore_permissions=True)
		self.assertRaises(frappe.ValidationError, api.set_application_status, self.app, "Joined")
		frappe.db.set_value("Joining", joining.name, "status", "Joined")
		self.assertEqual(api.set_application_status(self.app, "Joined"), "Joined")
