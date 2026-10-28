# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Candidate portal logins (pathways.utils.candidate_account)."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from pathways.permissions import CANDIDATE_ROLE
from pathways.utils.candidate_account import link_existing_account


def _user(email, user_type="Website User", roles=()):
	frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": "Existing",
			"user_type": user_type,
			"send_welcome_email": 0,
			"roles": [{"role": r} for r in roles],
		}
	).insert(ignore_permissions=True)
	return email


def _candidate(email):
	return (
		frappe.get_doc({"doctype": "Candidate", "full_name": "Existing Login", "email": email, "mobile_number": "9876501234"})
		.insert(ignore_permissions=True)
		.name
	)


class TestCandidateAccount(IntegrationTestCase):
	def test_guest_application_with_existing_login(self):
		"""Someone applies as a guest with an email that already has a login on the site
		(e.g. an SLCM account): that login gets the Candidate role and owns the record, and
		is told once to sign in with the existing password. The password is never sent."""
		email = _user(f"existing-{frappe.generate_hash(length=6)}@example.com")
		candidate = _candidate(email)
		with patch("pathways.utils.communication._send_event") as send:
			self.assertTrue(link_existing_account(candidate))
			self.assertIn(CANDIDATE_ROLE, frappe.get_roles(email))
			self.assertEqual(frappe.db.get_value("Candidate", candidate, "owner"), email)
			kwargs = send.call_args.kwargs
			self.assertEqual(kwargs["rule_event"], "candidate_portal_existing_account")
			self.assertEqual(kwargs["candidate"]["email"], email)
			self.assertNotIn("temporary_password", kwargs["context"])
			# A second application: already a candidate, no second email.
			self.assertFalse(link_existing_account(candidate))
			self.assertEqual(send.call_count, 1)

	def test_staff_login_is_left_alone(self):
		"""A staff (System User) login never becomes a candidate login this way."""
		email = _user(f"staff-{frappe.generate_hash(length=6)}@example.com", "System User", roles=("Pathways Recruiter",))
		candidate = _candidate(email)
		with patch("pathways.utils.communication._send_event") as send:
			self.assertFalse(link_existing_account(candidate))
		send.assert_not_called()
		self.assertNotIn(CANDIDATE_ROLE, frappe.get_roles(email))

	def test_existing_rule_and_template(self):
		"""The email is set up in Email Setup like every other recruitment email."""
		template = frappe.db.get_value("Recruitment Email Rule", "candidate_portal_existing_account", "email_template")
		self.assertEqual(template, "Candidate Portal Login (Existing Account)")
		self.assertNotIn("temporary_password", frappe.db.get_value("Email Template", template, "response"))
