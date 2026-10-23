# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Post-interview regrets (step 32), panel thanks and honorarium (step 33),
the Interview Assessment print format, and the removal of the legacy
scoring endpoints."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from pathways.api import honorarium, selection


def _user(email, first_name):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": first_name, "user_type": "System User", "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	return email


class TestSelectionComms(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		track = frappe.db.get_value("Recruitment Track", {}, "name")
		department = frappe.db.get_value("Pathways Department", {}, "name")
		self.job = frappe.get_doc(
			{
				"doctype": "Job Opening",
				"job_title": "Test Selection Comms Post",
				"track": track,
				"department": department,
				"employment_type": "Permanent",
				"vacancies": 1,
			}
		)
		self.job.flags.ignore_mandatory = True
		self.job.insert(ignore_permissions=True)
		self.panel = [
			_user("sc-panel-int@example.com", "Internal Panellist"),
			_user("sc-panel-ext@example.com", "External Expert"),
			_user("sc-panel-ext2@example.com", "Second Expert"),
		]
		committee = frappe.get_doc(
			{
				"doctype": "Selection Committee",
				"job_opening": self.job.name,
				"members": [
					{"member": self.panel[0], "is_external_expert": 0},
					{"member": self.panel[1], "is_external_expert": 1},
					{"member": self.panel[2], "is_external_expert": 1},
				],
			}
		)
		committee.flags.ignore_validate = True
		committee.insert(ignore_permissions=True)
		self.committee = committee.name

	def _application(self, label, outcome, interview_status="Completed"):
		candidate = frappe.get_doc(
			{
				"doctype": "Candidate",
				"full_name": f"SC {label}",
				"email": f"sc-{label}-{frappe.generate_hash(length=6)}@example.com",
				"mobile_number": "98" + frappe.generate_hash(length=8).translate(str.maketrans("abcdef", "123456"))[:8],
			}
		)
		candidate.flags.ignore_validate = True
		candidate.insert(ignore_permissions=True)
		app = frappe.get_doc({"doctype": "Application", "candidate": candidate.name, "job_opening": self.job.name})
		app.flags.ignore_validate = True
		app.flags.ignore_mandatory = True
		app.insert(ignore_permissions=True)
		interview = frappe.get_doc(
			{
				"doctype": "Interview",
				"application": app.name,
				"round_type": "Final",
				"selection_committee": self.committee,
				"scheduled_datetime": now_datetime(),
			}
		)
		interview.flags.ignore_validate = True
		interview.insert(ignore_permissions=True)
		frappe.db.set_value("Interview", interview.name, "status", interview_status)
		status = {"Selected": "Selected", "Not Selected": "Not Selected"}.get(outcome, "Interview Completed")
		frappe.db.set_value("Application", app.name, {"selection_outcome": outcome, "status": status})
		return app.name

	# ------------------------------------------------------------ regrets

	def test_regret_pending_and_sent_once(self):
		"""Step 32: regrets go only to interviewed, not-selected candidates; waitlisted candidates are
		held back and selected or not-yet-interviewed ones are skipped. The screening regret field
		is untouched, and a second run sends nothing.
		"""
		rejected = self._application("rejected", "Not Selected")
		waitlisted = self._application("waitlisted", "Waitlisted")
		selected = self._application("selected", "Selected")
		not_interviewed = self._application("noshow", "Not Selected", interview_status="Scheduled")

		pending = selection.post_interview_regret_pending(self.job.name)
		self.assertEqual(pending["not_selected"], 1)
		self.assertEqual(pending["waitlisted"], 1)
		self.assertFalse(pending["waitlist_released"])

		with patch("pathways.utils.communication.send_event") as send:
			result = selection.send_post_interview_regrets(self.job.name)
		self.assertEqual(result["applications"], [rejected])
		self.assertEqual(result["waitlisted_held"], 1)
		self.assertEqual(send.call_count, 1)
		self.assertEqual(send.call_args.args[0], "regret_after_interview")
		self.assertTrue(frappe.db.get_value("Application", rejected, "interview_regret_sent_on"))
		# The screening regret field is untouched.
		self.assertFalse(frappe.db.get_value("Application", rejected, "regret_sent_on"))
		for name in (waitlisted, selected, not_interviewed):
			self.assertFalse(frappe.db.get_value("Application", name, "interview_regret_sent_on"))

		# Second run: nobody new.
		with patch("pathways.utils.communication.send_event") as send:
			again = selection.send_post_interview_regrets(self.job.name)
		self.assertEqual(again["sent"], 0)
		send.assert_not_called()

	def test_waitlisted_included_on_request(self):
		"""Step 32: ticking 'include waitlisted' sends them a regret and marks them Not Selected."""
		waitlisted = self._application("wl", "Waitlisted")
		with patch("pathways.utils.communication.send_event") as send:
			result = selection.send_post_interview_regrets(self.job.name, include_waitlisted=1)
		self.assertEqual(result["applications"], [waitlisted])
		self.assertEqual(send.call_count, 1)
		app = frappe.db.get_value("Application", waitlisted, ["selection_outcome", "status", "interview_regret_sent_on"], as_dict=True)
		self.assertEqual(app.selection_outcome, "Not Selected")
		self.assertEqual(app.status, "Not Selected")
		self.assertTrue(app.interview_regret_sent_on)

	def test_waitlist_released_when_job_filled(self):
		"""Step 32: once the job is Filled, the waitlist is released and included automatically."""
		waitlisted = self._application("wl2", "Waitlisted")
		frappe.db.set_value("Job Opening", self.job.name, "status", "Filled")
		self.assertTrue(selection.post_interview_regret_pending(self.job.name)["waitlist_released"])
		with patch("pathways.utils.communication.send_event"):
			result = selection.send_post_interview_regrets(self.job.name)
		self.assertEqual(result["applications"], [waitlisted])

	def test_regret_rule_is_automatic_with_own_template(self):
		"""The post-interview regret email rule is automatic and uses its own template."""
		rule = frappe.db.get_value("Recruitment Email Rule", "regret_after_interview", ["is_automatic", "email_template"], as_dict=True)
		self.assertEqual(rule.is_automatic, 1)
		self.assertEqual(rule.email_template, "Regret After Interview")

	# ------------------------------------------------------------ thanks + honorarium

	def test_thanks_sent_once_and_honorarium_rows(self):
		"""Step 33: the thank-you goes to each panellist once and creates one honorarium row each.
		With 'external experts only', internal panellists are Not applicable and external ones get
		the default amount. A second run sends and creates nothing.
		"""
		settings = frappe.get_single("Pathways Settings")
		settings.honorarium_internal_amount = 1000
		settings.honorarium_external_amount = 5000
		settings.honorarium_external_only = 1
		settings.flags.ignore_mandatory = True
		settings.save(ignore_permissions=True)

		with patch("pathways.utils.communication.send_event") as send:
			result = honorarium.send_panel_thanks(self.job.name)
		self.assertEqual(result["sent"], 3)
		self.assertEqual(result["created"], 3)
		self.assertEqual(send.call_count, 3)
		self.assertEqual({c.kwargs["approvers"][0] for c in send.call_args_list}, set(self.panel))
		self.assertTrue(all(c.args[0] == "panel_thanks" for c in send.call_args_list))

		rows = {
			r.panellist: r
			for r in frappe.get_all(
				"Panel Honorarium", filters={"job_opening": self.job.name}, fields=["panellist", "status", "amount", "is_external", "thanks_sent_on"]
			)
		}
		self.assertEqual(len(rows), 3)
		self.assertEqual(rows[self.panel[0]].status, "Not applicable")
		self.assertEqual(rows[self.panel[0]].amount, 0)
		self.assertEqual(rows[self.panel[1]].status, "Pending")
		self.assertEqual(rows[self.panel[1]].amount, 5000)
		self.assertTrue(all(r.thanks_sent_on for r in rows.values()))
		self.assertEqual(honorarium.panel_thanks_pending(self.job.name)["pending"], 0)

		with patch("pathways.utils.communication.send_event") as send:
			again = honorarium.send_panel_thanks(self.job.name)
		self.assertEqual(again["sent"], 0)
		self.assertEqual(again["created"], 0)
		send.assert_not_called()
		self.assertEqual(frappe.db.count("Panel Honorarium", {"job_opening": self.job.name}), 3)

	def test_honorarium_approve_then_paid(self):
		"""Step 33: an honorarium cannot be marked paid before approval. Approval records the approver
		and normalises the PAN; once Paid it records the reference and can no longer be edited.
		"""
		with patch("pathways.utils.communication.send_event"):
			honorarium.send_panel_thanks(self.job.name)
		name = frappe.db.get_value("Panel Honorarium", {"job_opening": self.job.name, "panellist": self.panel[1]}, "name")
		honorarium.update_honorarium(name, amount=2500, pan_number="abcde1234f")
		# Paid before approval is refused.
		self.assertEqual(honorarium.mark_paid([name])["updated"], 0)
		self.assertEqual(honorarium.approve([name])["updated"], 1)
		doc = frappe.get_doc("Panel Honorarium", name)
		self.assertEqual(doc.status, "Approved")
		self.assertEqual(doc.approved_by, "Administrator")
		self.assertEqual(doc.pan_number, "ABCDE1234F")
		self.assertEqual(honorarium.mark_paid([name], payment_reference="UTR123")["updated"], 1)
		doc.reload()
		self.assertEqual(doc.status, "Paid")
		self.assertEqual(doc.payment_reference, "UTR123")
		self.assertTrue(doc.paid_on)
		self.assertRaises(frappe.ValidationError, honorarium.update_honorarium, name, amount=1)

	def test_menu_item_registered(self):
		"""The Panel Honorarium page is in the app menu."""
		from pathways.api.access import MENU_ITEMS

		self.assertIn("honorarium", [m["key"] for m in MENU_ITEMS])

	# ------------------------------------------------------------ print format + legacy

	def test_print_format_renders(self):
		"""Step 18: the standard Interview Assessment print format renders the scores, comments and the
		'confirmed on the platform' line when there is no drawn signature.
		"""
		self.assertTrue(frappe.db.exists("Print Format", {"name": "Interview Assessment", "doc_type": "Interview Assessment", "standard": "Yes"}))
		app = self._application("print", "Not Selected")
		interview = frappe.db.get_value("Interview", {"application": app}, "name")
		doc = frappe.get_doc(
			{
				"doctype": "Interview Assessment",
				"interview": interview,
				"application": app,
				"candidate_name": "SC print",
				"job_title": self.job.job_title,
				"panelist": self.panel[0],
				"verdict": "Recommended",
				"recommendation": "Strong answers",
				"panelist_signature_confirmed": 1,
				"criteria": [{"criterion_label": "Domain Knowledge", "max_score": 20, "score_given": 15}],
			}
		)
		doc.flags.ignore_validate = True
		doc.flags.ignore_links = True
		doc.insert(ignore_permissions=True)
		html = frappe.get_print("Interview Assessment", doc.name, print_format="Interview Assessment")
		self.assertIn("INTERVIEW ASSESSMENT FORM", html)
		self.assertIn("DOMAIN KNOWLEDGE", html)
		self.assertIn("Strong answers", html)
		self.assertIn("Confirmed on the recruitment platform", html)

	def test_legacy_endpoints_removed(self):
		"""The old interview-scoring endpoints are gone from both the backend and the frontend
		service, so only the validated panel endpoints are used.
		"""
		from pathways.api import scoring

		self.assertFalse(hasattr(scoring, "submit_interview_assessment"))
		self.assertFalse(hasattr(scoring, "consolidate_scores"))
		with open(frappe.get_app_path("pathways", "..", "frontend", "src", "services", "scoring.js")) as f:
			source = f.read()
		self.assertNotIn("submit_interview_assessment", source)
		self.assertNotIn("consolidate_scores", source)

	# ------------------------------------------------------- Selection module

	def test_selection_list_tracks_progress(self):
		"""Selection module list: a job with final interviews shows its decisions, regrets still to
		send and the next step; it moves on once regrets and thanks are done."""
		selected = self._application("mod-sel", "Selected")
		self._application("mod-rej", "Not Selected")
		undecided = self._application("mod-und", None)

		row = next(r for r in selection.list_selection_jobs() if r["name"] == self.job.name)
		self.assertEqual(row["candidates"], 3)
		self.assertEqual((row["outcomes"]["Selected"], row["outcomes"]["Not Selected"], row["undecided"]), (1, 1, 1))
		self.assertEqual(row["regrets"]["pending"], 1)
		self.assertEqual(row["next_step"], "scores")

		frappe.db.set_value("Application", undecided, {"selection_outcome": "Waitlisted"})
		with patch("pathways.utils.communication.send_event"):
			selection.send_post_interview_regrets(self.job.name)
			honorarium.send_panel_thanks(self.job.name)
		row = next(r for r in selection.list_selection_jobs() if r["name"] == self.job.name)
		self.assertTrue(row["done"]["scores"] and row["done"]["regrets"])
		self.assertEqual(row["next_step"], "green_sheet")

		job = selection.get_selection_job(self.job.name)
		offers = {c["application"]: c for c in job["candidates_for_offer"]}
		self.assertEqual(set(offers), {selected, undecided})
		self.assertEqual(offers[selected]["outcome"], "Selected")
		self.assertIsNone(offers[selected]["offer"])

	def test_selection_module_is_for_the_recruitment_team(self):
		"""A panellist (no Interview create right) cannot open the Selection module or see its menu."""
		self._application("mod-perm", "Selected")
		frappe.set_user(self.panel[0])
		self.assertRaises(frappe.PermissionError, selection.list_selection_jobs)
		self.assertRaises(frappe.PermissionError, selection.get_selection_job, self.job.name)
		from pathways.api.access import get_my_access

		self.assertNotIn("selection", get_my_access().get("menu", []))
