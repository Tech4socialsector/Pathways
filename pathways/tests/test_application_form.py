# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Server-side validation of the apply form (workflow step 2)."""

import frappe
from frappe.tests import IntegrationTestCase

from pathways.utils.application_form import validate_submission


class TestApplicationForm(IntegrationTestCase):
	def test_single_choice_question_with_referees(self):
		"""A job with a Single Choice screening question (e.g. the CFO's professional
		qualification) still validates the referees' relationships: the choices of the
		question must not replace the form's dropdown lists. An incomplete form gets the
		usual list of corrections, never a server error."""
		job = frappe.get_doc(
			{
				"doctype": "Job Opening",
				"job_title": "Form Test Post",
				"track": "Admin",
				"screening_questions": [
					{"question": "Your professional qualification?", "answer_type": "Single Choice", "options": "CA\nCMA", "is_mandatory": 1, "idx": 1},
				],
			}
		)
		data = {
			"candidate": {"full_name": "Form Tester"},
			"application": {
				"screening_answers": [{"idx": 1, "answer": "CA"}],
				"references": [
					{"referee_name": "A", "current_designation_org": "X", "relationship": "Current Supervisor", "email": "a@example.com", "mobile": "9876543210"},
					{"referee_name": "B", "current_designation_org": "Y", "relationship": "Not a listed relationship", "email": "b@example.com", "mobile": "9876543211"},
				],
			},
		}
		with self.assertRaises(frappe.ValidationError):
			validate_submission(job, data, "Guest", email="tester@example.com")
		errors = frappe.local.response.get("field_errors") or {}
		self.assertIn("candidate.mobile_number", errors)
		self.assertNotIn("screening.1", errors)  # "CA" is one of the choices
		self.assertNotIn("ref.0.relationship", errors)
		self.assertIn("ref.1.relationship", errors)
