# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Event emails (pathways.utils.communication)."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from pathways.utils.communication import _send_event


class TestCommunication(IntegrationTestCase):
	def test_cc_and_bcc_reach_sendmail(self):
		"""Extra CC and BCC of a send are passed to sendmail with the rule's own CC; an
		address already in CC is not blind-copied as well."""
		rule = frappe.get_doc("Recruitment Email Rule", "appointment_order")
		with patch("frappe.sendmail") as sendmail:
			_send_event(
				rule_event=rule.name,
				context={"candidate_name": "Test"},
				candidate={"email": "candidate@example.com", "name": "Test"},
				extra_cc=["copy@example.com"],
				extra_bcc=["hidden@example.com", "copy@example.com"],
			)
		kwargs = sendmail.call_args.kwargs
		self.assertEqual(kwargs["recipients"], ["candidate@example.com"])
		self.assertIn("copy@example.com", kwargs["cc"])
		self.assertEqual(kwargs["bcc"], ["hidden@example.com"])
