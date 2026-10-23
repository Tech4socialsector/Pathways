# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Round 1 / HR interaction (workflow step 13), the final shortlist and
Shortlisting Note (14), the Selection Committee calendar block (15),
job-level panel files (16) and the drawn signature on assessment forms
(18)."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, get_datetime, now_datetime

from pathways.api import interviews, panel, panel_documents
from pathways.permissions import SELECTION_ROLE

SIGNATURE = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


def _user(email, first_name, roles=()):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": first_name, "user_type": "System User", "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	missing = [r for r in roles if r not in [x.role for x in user.roles]]
	if missing:
		user.add_roles(*missing)
	return email


def _set_settings(**values):
	for field, value in values.items():
		frappe.db.set_single_value("Pathways Settings", field, value)
	frappe.clear_document_cache("Pathways Settings", "Pathways Settings")


class TestHRRound(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.saved = {
			f: frappe.db.get_single_value("Pathways Settings", f)
			for f in ("require_assessment_signature", "hr_assessors_per_interview", "committee_block_hours")
		}
		_set_settings(require_assessment_signature=0, hr_assessors_per_interview=2, committee_block_hours=3)
		track = "Admin" if frappe.db.exists("Recruitment Track", "Admin") else frappe.db.get_value("Recruitment Track", {}, "name")
		department = frappe.db.get_value("Pathways Department", {}, "name")
		self.job = frappe.get_doc(
			{"doctype": "Job Opening", "job_title": "Test HR Round Post", "track": track, "department": department, "employment_type": "Permanent", "vacancies": 1}
		)
		self.job.flags.ignore_mandatory = True
		self.job.insert(ignore_permissions=True)
		self.hr1 = _user("hr-assessor-1@example.com", "HR One")
		self.hr2 = _user("hr-assessor-2@example.com", "HR Two")
		self.outsider = _user("hr-outsider@example.com", "Outsider", roles=(SELECTION_ROLE,))
		self.panel = [_user(f"hr-panel-{i}@example.com", f"Panel {i}") for i in range(3)]
		self.app = self._application("one")
		self.start = get_datetime(add_days(now_datetime(), 3)).replace(hour=10, minute=0, second=0, microsecond=0)

	def tearDown(self):
		frappe.set_user("Administrator")
		_set_settings(**{k: v or 0 for k, v in self.saved.items()})

	def _application(self, label):
		candidate = frappe.get_doc(
			{
				"doctype": "Candidate",
				"full_name": f"HR {label}",
				"email": f"hr-{label}-{frappe.generate_hash(length=6)}@example.com",
				"mobile_number": "97" + frappe.generate_hash(length=8).translate(str.maketrans("abcdef", "123456"))[:8],
			}
		)
		candidate.flags.ignore_validate = True
		candidate.insert(ignore_permissions=True)
		app = frappe.get_doc({"doctype": "Application", "candidate": candidate.name, "job_opening": self.job.name, "resume_attachment": "/private/files/hr-test-cv.pdf"})
		app.flags.ignore_validate = True
		app.flags.ignore_mandatory = True
		app.insert(ignore_permissions=True)
		frappe.db.set_value("Application", app.name, "status", "Shortlisted")
		return app.name

	def _schedule_hr(self, assessors=None):
		with patch("pathways.utils.communication.send_event") as send:
			result = interviews.schedule_interviews(
				self.job.name, [self.app], "HR Interaction", str(self.start), slot_minutes=20,
				meeting_link="https://zoom.us/j/1", hr_assessors=assessors if assessors is not None else [self.hr1, self.hr2], send_invite=0,
			)
		return result["interviews"][0], send

	def _committee(self, **kwargs):
		with patch("pathways.utils.communication.send_event"):
			return interviews.save_selection_committee(self.job.name, [{"member": m} for m in self.panel], **kwargs)

	# ---------------------------------------------------- HR assessors (13)

	def test_hr_assessors_get_access_and_email(self):
		iv, send = self._schedule_hr()
		doc = frappe.get_doc("Interview", iv)
		self.assertEqual(doc.hr_assessor_list(), [self.hr1, self.hr2])
		emailed = [c for c in send.call_args_list if c.args[0] == "hr_assessor_assigned"]
		self.assertEqual(len(emailed), 1)
		self.assertEqual(sorted(emailed[0].kwargs["approvers"]), sorted([self.hr1, self.hr2]))
		self.assertIn(SELECTION_ROLE, frappe.get_roles(self.hr1))

		frappe.set_user(self.hr1)
		app = frappe.get_doc("Application", self.app)
		self.assertTrue(frappe.has_permission("Application", "read", doc=app))
		self.assertFalse(frappe.has_permission("Application", "write", doc=app))
		self.assertIn(self.app, frappe.get_list("Application", pluck="name"))
		brief = panel.candidate_brief(self.app, self.hr1)
		self.assertTrue(any(d["file_url"] == "/private/files/hr-test-cv.pdf" for d in brief["documents"]))
		self.assertIn(iv, [r.name for r in panel.get_my_panel()["interviews"]])

		frappe.set_user(self.outsider)
		self.assertFalse(frappe.has_permission("Application", "read", doc=frappe.get_doc("Application", self.app)))
		self.assertNotIn(iv, [r.name for r in panel.get_my_panel()["interviews"]])

	def test_hr_assessor_limit_and_reassign(self):
		frappe.set_user("Administrator")
		third = _user("hr-assessor-3@example.com", "HR Three")
		with self.assertRaises(frappe.ValidationError):
			self._schedule_hr([self.hr1, self.hr2, third])
		iv, _send = self._schedule_hr([self.hr1])
		with patch("pathways.utils.communication.send_event") as send:
			interviews.update_interview(iv, hr_assessors=[self.hr1, third], send_invite=0)
		self.assertEqual(frappe.get_doc("Interview", iv).hr_assessor_list(), [self.hr1, third])
		emailed = [c for c in send.call_args_list if c.args[0] == "hr_assessor_assigned"]
		# Only the new assessor; the time did not change.
		self.assertEqual([c.kwargs["approvers"] for c in emailed], [[third]])

	# ---------------------------------------------------- HR scoring

	def test_hr_assessment_and_outcome(self):
		iv, _send = self._schedule_hr()
		frappe.set_user(self.hr1)
		form = panel.get_assessment_form(iv)
		self.assertEqual(form["is_hr"], 1)
		self.assertTrue(form["can_score"])
		labels = [c["label"] for c in form["rubric"]["criteria"]]
		self.assertIn("Communication", labels)
		scores = {c["label"]: c["max_score"] / 2 for c in form["rubric"]["criteria"]}
		with self.assertRaises(frappe.ValidationError):
			panel.submit_assessment(iv, scores, additional_comments="note")
		saved = panel.submit_assessment(
			iv, scores, additional_comments="Clear communicator.", hr_outcome="Recommend for final", expected_salary="12 LPA", notice_period="30 days"
		)
		self.assertEqual(saved["score_percent"], 50)
		row = frappe.db.get_value("Interview Assessment", saved["name"], ["round_type", "hr_outcome", "verdict"], as_dict=True)
		self.assertEqual((row.round_type, row.hr_outcome, row.verdict or None), ("HR Interaction", "Recommend for final", None))

		frappe.set_user("Administrator")
		brief = panel.candidate_brief(self.app)
		self.assertEqual(brief["round1"]["assessments"][0]["hr_outcome"], "Recommend for final")
		self.assertEqual(brief["round1"]["assessments"][0]["notice_period"], "30 days")
		hr = interviews.get_hr_interaction(self.app)
		self.assertEqual(hr["interviews"][0]["assessments"][0]["note"], "Clear communicator.")

		frappe.set_user(self.outsider)
		with self.assertRaises(frappe.PermissionError):
			panel.submit_assessment(iv, scores, hr_outcome="Hold")

	# ---------------------------------------------------- final shortlist (14)

	def test_final_shortlist_and_note(self):
		frappe.set_user("Administrator")
		other = self._application("two")
		result = interviews.set_final_shortlist(self.job.name, [self.app], 1, remarks="Strong Round 1")
		self.assertEqual(result["count"], 1)
		# Idempotent
		interviews.set_final_shortlist(self.job.name, [self.app], 1)
		note = frappe.get_doc("Shortlisting Note", result["shortlisting_note"])
		self.assertEqual([r.application for r in note.final_shortlist], [self.app])
		self.assertEqual(note.final_shortlist[0].remarks, "Strong Round 1")
		self.assertEqual(frappe.db.get_value("Application", self.app, "status"), "Shortlisted")

		data = interviews.get_job_interviews(self.job.name)
		flags = {c["name"]: c["final_shortlisted"] for c in data["candidates"]}
		self.assertEqual(flags, {self.app: 1, other: 0})
		todo = {c["name"]: c for j in interviews.list_to_schedule() if j["job_opening"] == self.job.name for c in j["candidates"]}
		self.assertEqual(todo[self.app]["next_round"], "Final")
		self.assertEqual(todo[other]["next_round"], "HR Interaction")

		saved = interviews.save_shortlisting_note(self.job.name, note="<p>Two rounds held.</p>", remarks={self.app: "Top candidate"})
		self.assertEqual(saved["final_shortlist"][0]["remarks"], "Top candidate")
		with patch("frappe.utils.pdf.get_pdf", side_effect=lambda html, *a, **k: html.encode()) as pdf:
			content = interviews.shortlisting_note_pdf(self.job.name)
		pdf.assert_called_once()
		self.assertIn(b"Two rounds held.", content)
		self.assertIn(b"Top candidate", content)

		interviews.set_final_shortlist(self.job.name, [self.app], 0)
		self.assertFalse(frappe.get_doc("Shortlisting Note", result["shortlisting_note"]).final_shortlist)

	# ---------------------------------------------------- calendar block (15)

	def test_committee_calendar_block_is_idempotent(self):
		registrar = _user("hr-registrar@example.com", "Registrar", roles=("Pathways Registrar",))
		settings = frappe.get_single("Pathways Settings")
		if "Pathways Registrar" not in [r.role for r in settings.calendar_block_roles]:
			settings.append("calendar_block_roles", {"role": "Pathways Registrar"})
			settings.flags.ignore_mandatory = True
			settings.save(ignore_permissions=True)
		day = add_days(now_datetime().date(), 10)
		first = self._committee(scheduled_date=str(day), scheduled_time="10:00:00")
		event = first["calendar_event"]
		self.assertTrue(event)
		ev = frappe.get_doc("Event", event)
		emails = {p.email for p in ev.event_participants}
		self.assertTrue(set(self.panel) <= emails)
		self.assertIn(registrar, emails)
		self.assertEqual(get_datetime(ev.starts_on), get_datetime(f"{day} 10:00:00"))
		self.assertTrue(frappe.db.exists("DocShare", {"share_doctype": "Event", "share_name": event, "user": registrar}))

		again = self._committee(scheduled_date=str(day), scheduled_time="14:30:00")
		self.assertEqual(again["calendar_event"], event)
		self.assertEqual(frappe.db.count("Event", {"reference_doctype": "Selection Committee", "reference_docname": first["name"]}), 1)
		self.assertEqual(get_datetime(frappe.db.get_value("Event", event, "starts_on")), get_datetime(f"{day} 14:30:00"))

		self._committee(scheduled_date=None, scheduled_time=None)
		self.assertEqual(frappe.db.get_value("Event", event, "status"), "Cancelled")

	# ---------------------------------------------------- panel files (16)

	def test_job_files_shared_with_panel(self):
		self._committee(scheduled_date=str(add_days(now_datetime().date(), 10)), scheduled_time="10:00:00")
		interviews.set_final_shortlist(self.job.name, [self.app], 1)
		labels = [f["label"] for f in panel_documents.job_files(self.job.name)]
		for label in (panel_documents.PANEL_DETAILS, panel_documents.BLANK_FORMS, panel_documents.SHORTLISTING_NOTE):
			self.assertIn(label, labels)
		with patch("pathways.utils.communication.send_event") as send:
			result = panel_documents.share_job_files(self.job.name, {self.panel[0]: {panel_documents.PANEL_DETAILS: True, panel_documents.SHORTLISTING_NOTE: True}})
		self.assertEqual(result["added"], 2)
		self.assertEqual(send.call_args.args[0], "panel_job_files_shared")

		frappe.set_user(self.panel[0])
		rows = panel_documents.get_shared_documents()["job_files"]
		self.assertEqual([f["label"] for f in rows[0]["files"]], [panel_documents.PANEL_DETAILS, panel_documents.SHORTLISTING_NOTE])
		with patch("frappe.utils.pdf.get_pdf", return_value=b"%PDF"):
			panel_documents.download_job_file(self.job.name, panel_documents.PANEL_DETAILS)
		with self.assertRaises(frappe.PermissionError):
			panel_documents.download_job_file(self.job.name, panel_documents.HR_NOTES)

	def test_interview_schedule_export(self):
		self._schedule_hr()
		data = interviews.schedule_data(self.job.name, "HR Interaction")
		self.assertEqual(len(data["rows"]), 1)
		self.assertEqual(data["rows"][0]["login_time"], "9:50 AM")
		self.assertIn("HR One", data["panel"])
		self.assertTrue(interviews.schedule_xlsx(self.job.name, "HR Interaction").startswith(b"PK"))

	# ---------------------------------------------------- signature (18)

	def test_signature_required_when_switched_on(self):
		iv, _send = self._schedule_hr()
		_set_settings(require_assessment_signature=1)
		frappe.set_user(self.hr1)
		form = panel.get_assessment_form(iv)
		self.assertEqual(form["signature_required"], 1)
		scores = {c["label"]: 5 for c in form["rubric"]["criteria"]}
		with self.assertRaises(frappe.ValidationError):
			panel.submit_assessment(iv, scores, hr_outcome="Hold")
		with self.assertRaises(frappe.ValidationError):
			panel.submit_assessment(iv, scores, hr_outcome="Hold", signature="javascript:alert(1)")
		saved = panel.submit_assessment(iv, scores, hr_outcome="Hold", signature=SIGNATURE)
		doc = frappe.get_doc("Interview Assessment", saved["name"])
		self.assertEqual(doc.panelist_signature, SIGNATURE)
		self.assertTrue(doc.signed_on)
		# Updating later keeps the signature without drawing it again.
		panel.submit_assessment(iv, scores, hr_outcome="Recommend for final")
		self.assertEqual(frappe.db.get_value("Interview Assessment", saved["name"], "panelist_signature"), SIGNATURE)

		# The recruitment team typing in a signed paper form does not draw one.
		frappe.set_user("Administrator")
		self.assertEqual(panel.get_assessment_form(iv, self.hr2)["signature_required"], 0)
		panel.submit_assessment(iv, scores, hr_outcome="Hold", panelist=self.hr2)

	def test_signature_on_printed_final_form(self):
		committee = self._committee(scheduled_date=str(add_days(now_datetime().date(), 10)), scheduled_time="10:00:00")
		with patch("pathways.utils.communication.send_event"):
			iv = interviews.schedule_interviews(self.job.name, [self.app], "Final", str(self.start), meeting_link="https://zoom.us/j/2", send_invite=0)["interviews"][0]
		self.assertTrue(committee["name"])
		frappe.set_user(self.panel[0])
		form = panel.get_assessment_form(iv)
		scores = {c["label"]: c["max_score"] for c in form["rubric"]["criteria"]}
		panel.submit_assessment(iv, scores, verdict="Recommended", signature=SIGNATURE)
		frappe.set_user("Administrator")
		with patch("frappe.utils.pdf.get_pdf", side_effect=lambda html, *a, **k: html.encode()):
			content, _name = panel.assessment_forms_pdf(self.job.name, panelist=self.panel[0])
			blank, blank_name = panel.assessment_forms_pdf(self.job.name, blank=1, members_override=[{"user": self.panel[1], "full_name": "Panel 1"}])
		self.assertIn(SIGNATURE.encode(), content)
		self.assertNotIn(SIGNATURE.encode(), blank)
		self.assertIn("blank", blank_name)
