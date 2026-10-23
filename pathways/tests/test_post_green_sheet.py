# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Post-Interview (selection) Green Sheet, workflow steps 20, 24 and 25:
chain seeding, drafting from the committee's outcomes, the full approval
walk (with the approval email), return / revise, the signed copy and the
helper Offers rely on."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from pathways.api import post_green_sheet as pgs
from pathways.api.approval import record_approval_action
from pathways.patches.v1_0.post_interview_green_sheet_setup import DEFAULT_STEPS, seed_post_interview_chains

DOCTYPE = "Post-Interview Green Sheet"


def _user(role):
	email = f"pigs-{frappe.scrub(role)}-{frappe.generate_hash(length=6)}@example.com"
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": role.replace("Pathways ", ""),
			"send_welcome_email": 0,
			"user_type": "System User",
			"roles": [{"role": role}],
		}
	).insert(ignore_permissions=True)
	return user.name


class TestPostGreenSheet(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.track = f"PIGS Track {frappe.generate_hash(length=5)}"
		frappe.get_doc({"doctype": "Recruitment Track", "track_name": cls.track, "is_active": 1}).insert(ignore_permissions=True)
		cls.created_chains = seed_post_interview_chains()
		department = frappe.db.get_value("Pathways Department", {}, "name")
		if not department:
			department = frappe.get_doc({"doctype": "Pathways Department", "department_name": "PIGS Test Dept"}).insert(ignore_permissions=True).name
		cls.department = department
		cls.approvers = {role: _user(role) for role, _label in DEFAULT_STEPS}

	def setUp(self):
		frappe.set_user("Administrator")
		self.job = frappe.get_doc(
			{
				"doctype": "Job Opening",
				"job_title": "Graphic Designer",
				"track": self.track,
				"department": self.department,
				"employment_type": "Consultant",
				"vacancies": 1,
				"status": "Draft",
				"tenure_description": "One year, extendable",
			}
		).insert(ignore_permissions=True)
		self.selected = self._application("Rajalekshmi L S", "Selected", years=7)
		self.waitlisted = self._application("Riya Dipak", "Waitlisted")
		self.rejected = self._application("Someone Else", "Not Selected")

	def tearDown(self):
		frappe.set_user("Administrator")

	def _application(self, name, outcome, years=0):
		candidate = frappe.get_doc(
			{"doctype": "Candidate", "full_name": name, "email": f"pigs-{frappe.generate_hash(length=8)}@example.com", "mobile_number": "9876543210"}
		).insert(ignore_permissions=True)
		app = frappe.get_doc(
			{
				"doctype": "Application",
				"candidate": candidate.name,
				"job_opening": self.job.name,
				"overall_experience_years": years,
				"qualifications": [{"degree_level": "Postgraduate", "degree_name": "MA"}],
			}
		).insert(ignore_permissions=True)
		app.db_set({"selection_outcome": outcome, "status": "Interview Completed" if outcome == "Waitlisted" else outcome})
		return app.name

	def _raise(self):
		name = pgs.create_from_outcomes(self.job.name)
		return frappe.get_doc(DOCTYPE, name)

	def _walk(self, sheet_name, roles):
		for role in roles:
			frappe.set_user(self.approvers[role])
			record_approval_action(DOCTYPE, sheet_name, "Approved", "ok")
		frappe.set_user("Administrator")

	# ------------------------------------------------------------- seeding

	def test_chain_seeded_once_per_track(self):
		"""Setup: the default Recruiter > PNCO > CFO > Registrar > VC chain is seeded once per track
		and seeding again adds nothing.
		"""
		template = frappe.get_all(
			"Approval Chain Template",
			filters={"track": self.track, "applies_to": DOCTYPE},
			fields=["name", "employment_type"],
		)
		self.assertEqual(len(template), 1)
		self.assertFalse(template[0].employment_type)
		steps = frappe.get_doc("Approval Chain Template", template[0].name).steps
		self.assertEqual([s.approver_role for s in sorted(steps, key=lambda s: s.sequence)], [r for r, _l in DEFAULT_STEPS])
		# Idempotent: nothing new for tracks that already have one.
		self.assertNotIn(template[0].name, seed_post_interview_chains())
		self.assertEqual(frappe.db.count("Approval Chain Template", {"track": self.track, "applies_to": DOCTYPE}), 1)

	# ---------------------------------------------------------- drafting

	def test_draft_prefilled_from_outcomes(self):
		"""Step 24: raising the sheet pre-fills the selected and waitlisted candidates, subject,
		selection note and a fee row from the panel outcomes; raising again returns the same draft.
		"""
		sheet = self._raise()
		self.assertEqual(sheet.docstatus, 0)
		self.assertEqual(sheet.recommended_application, self.selected)
		self.assertEqual(sheet.waitlist_application, self.waitlisted)
		self.assertEqual(sheet.recommended_candidate_name, "Rajalekshmi L S")
		self.assertEqual(sheet.employment_type, "Consultant")
		self.assertTrue(sheet.approval_chain_template)
		self.assertIn("Graphic Designer", sheet.subject)
		self.assertIn("Rajalekshmi L S", sheet.selection_note)
		self.assertIn("Riya Dipak", sheet.selection_note)
		self.assertEqual(len(sheet.compensation_table), 1)
		row = sheet.compensation_table[0]
		self.assertEqual(row.application, self.selected)
		self.assertEqual(row.years_experience, "7 years")
		self.assertEqual(row.highest_qualification, "MA")
		self.assertTrue(row.medical_insurance)
		# Raising again returns the open draft instead of a second sheet.
		self.assertEqual(pgs.create_from_outcomes(self.job.name), sheet.name)

	def test_cannot_raise_without_selected_candidate(self):
		"""Step 24: the sheet cannot be raised until the panel has selected someone."""
		frappe.db.set_value("Application", self.selected, "selection_outcome", "Not Selected")
		self.assertRaises(frappe.ValidationError, pgs.create_from_outcomes, self.job.name)

	# ------------------------------------------------------ approval walk

	def test_full_approval_walk(self):
		"""Step 25: submitting freezes the chain and emails the first approver with a link to the
		sheet; a later approver cannot act out of turn. After every step approves, the sheet is
		Approved, unlocks offers for the selected and waitlisted candidates, and both print
		formats render.
		"""
		sheet = self._raise()
		pgs.save_sheet(sheet.name, {"date_of_appointment": "Tentatively in May", "compensation_table": [
			{"application": self.selected, "candidate_name": "Rajalekshmi L S", "recommended_salary": 60000, "position_offered": "Graphic Designer", "medical_insurance": 1, "leave_applicable": 1}
		]})
		self.assertIsNone(pgs.get_approved_sheet_for_application(self.selected))

		with patch("pathways.utils.communication.send_event") as send:
			pgs.submit_sheet(sheet.name)
		sheet.reload()
		self.assertEqual(sheet.status, "Under Approval")
		self.assertEqual(len(sheet.approval_steps), len(DEFAULT_STEPS))
		event, doctype, docname, context = send.call_args.args[:4]
		self.assertEqual((event, doctype, docname), ("green_sheet_approval", DOCTYPE, sheet.name))
		self.assertIn(f"/pathways/selection-green-sheets/{sheet.name}", context["link"])
		# Other test users on the site may hold the role too.
		self.assertIn(self.approvers["Pathways Recruiter"], send.call_args.kwargs["approvers"])
		self.assertNotIn(self.approvers["Pathways CFO"], send.call_args.kwargs["approvers"])

		# A later approver cannot jump the queue.
		frappe.set_user(self.approvers["Pathways CFO"])
		self.assertRaises(frappe.PermissionError, record_approval_action, DOCTYPE, sheet.name, "Approved")
		frappe.set_user("Administrator")

		with patch("pathways.utils.communication.send_event") as send:
			self._walk(sheet.name, [role for role, _l in DEFAULT_STEPS])
		# Every step after the first notified its approvers.
		self.assertEqual(send.call_count, len(DEFAULT_STEPS) - 1)
		sheet.reload()
		self.assertEqual(sheet.status, "Approved")
		self.assertEqual(len(sheet.approval_log), len(DEFAULT_STEPS))

		self.assertEqual(pgs.get_approved_sheet_for_application(self.selected), sheet.name)
		self.assertEqual(pgs.get_approved_sheet_for_application(self.waitlisted), sheet.name)
		self.assertIsNone(pgs.get_approved_sheet_for_application(self.rejected))

		# Both print formats render.
		for fmt in ("Post-Interview Green Sheet", "Panel Recommendation"):
			html = frappe.get_print(DOCTYPE, sheet.name, print_format=fmt)
			self.assertIn("Rajalekshmi L S", html)

	# ----------------------------------------------------- return / revise

	def test_return_and_revise(self):
		"""Step 25: returning needs a reason and blocks offers. Revising cancels the sheet and opens
		an amended draft with the same content; it can be resubmitted and withdrawn.
		"""
		sheet = self._raise()
		with patch("pathways.utils.communication.send_event"):
			pgs.submit_sheet(sheet.name)
			frappe.set_user(self.approvers["Pathways Recruiter"])
			record_approval_action(DOCTYPE, sheet.name, "Approved")
			frappe.set_user(self.approvers["Pathways PNCO"])
			self.assertRaises(frappe.ValidationError, record_approval_action, DOCTYPE, sheet.name, "Returned for Revision", "")
			record_approval_action(DOCTYPE, sheet.name, "Returned for Revision", "Fix the fee")
			frappe.set_user("Administrator")
		sheet.reload()
		self.assertEqual(sheet.status, "Returned for Revision")
		self.assertIsNone(pgs.get_approved_sheet_for_application(self.selected))

		new_name = pgs.revise_sheet(sheet.name)
		sheet.reload()
		self.assertEqual(sheet.docstatus, 2)
		revised = frappe.get_doc(DOCTYPE, new_name)
		self.assertEqual(revised.docstatus, 0)
		self.assertEqual(revised.amended_from, sheet.name)
		self.assertEqual(revised.status, "Draft")
		self.assertFalse(revised.approval_log)
		self.assertEqual(revised.recommended_application, self.selected)

		with patch("pathways.utils.communication.send_event"):
			pgs.save_sheet(new_name, {"deliverables": "Design collateral"}, submit=1)
			revised.reload()
			self.assertEqual(revised.status, "Under Approval")
			self.assertEqual(revised.deliverables, "Design collateral")
			# Withdraw cancels it.
			pgs.withdraw_sheet(new_name)
		revised.reload()
		self.assertEqual(revised.docstatus, 2)

	def test_delete_draft(self):
		"""An unsubmitted draft can be deleted."""
		sheet = self._raise()
		pgs.delete_draft(sheet.name)
		self.assertFalse(frappe.db.exists(DOCTYPE, sheet.name))

	# ----------------------------------------------------------- signed copy

	def test_signed_copy(self):
		"""Step 25: the signed copy can be uploaded only after submission and only by someone who can
		raise sheets; approvers cannot. It can also be removed.
		"""
		sheet = self._raise()
		self.assertRaises(frappe.ValidationError, pgs.attach_signed_copy, sheet.name, "/private/files/signed.pdf")
		with patch("pathways.utils.communication.send_event"):
			pgs.submit_sheet(sheet.name)
		self.assertEqual(pgs.attach_signed_copy(sheet.name, "/private/files/signed.pdf"), "/private/files/signed.pdf")
		self.assertEqual(frappe.db.get_value(DOCTYPE, sheet.name, "signed_copy_attachment"), "/private/files/signed.pdf")
		# Someone without create rights (an approver) cannot.
		frappe.set_user(self.approvers["Pathways CFO"])
		self.assertRaises(frappe.PermissionError, pgs.attach_signed_copy, sheet.name, None)
		frappe.set_user("Administrator")
		self.assertIsNone(pgs.attach_signed_copy(sheet.name, None))

	def test_permanent_sheet_prints_pay_fixation(self):
		"""Permanent posts show and print the pay fixation and probation details."""
		self.job.db_set("employment_type", "Permanent")
		sheet = self._raise()
		self.assertEqual(sheet.employment_type, "Permanent")
		self.assertFalse(sheet.compensation_table[0].medical_insurance)
		pgs.save_sheet(sheet.name, {"advertised_pay_level": "5/6/7/8", "fixed_pay_level": "Entry level 7", "ctc": 90000, "gross_salary": 80000, "probation_period": "One year"})
		html = frappe.get_print(DOCTYPE, sheet.name, print_format="Post-Interview Green Sheet")
		self.assertIn("5/6/7/8", html)
		self.assertIn("Entry level 7", html)
		self.assertIn("Probation", html)
		self.assertTrue(pgs.get_sheet(sheet.name)["is_permanent"])

	def test_job_selection_card(self):
		"""The job page's Selection card shows the selected candidates, the current sheet and whether
		an approval chain exists.
		"""
		sheet = self._raise()
		data = pgs.get_job_selection(self.job.name)
		self.assertEqual([s["application"] for s in data["outcomes"]["selected"]], [self.selected])
		self.assertEqual(data["current"]["name"], sheet.name)
		self.assertTrue(data["has_chain_template"])
		detail = pgs.get_sheet(sheet.name)
		self.assertFalse(detail["is_permanent"])
		self.assertTrue(any(c["value"] == self.selected for c in detail["candidates"]))
