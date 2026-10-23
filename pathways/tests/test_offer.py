# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Offers and appointment orders (workflow steps 22-29): the green-sheet
gate, review / return, Registrar signature, sending with the PDF, the
candidate's accept / decline / signed copy, and expiry."""

import base64
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from pathways.api import offer as api
from pathways.permissions import CANDIDATE_ROLE

DOCTYPE = "Offer Appointment Order"
# A 1x1 PNG, as the signature pad would send it.
SIGNATURE = "data:image/png;base64," + base64.b64encode(
	bytes.fromhex(
		"89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63f8cfc0f01f0005000201"
		"a5c1a4a40000000049454e44ae426082"
	)
).decode()
LETTER_FIELDS = {
	"designation": "Assistant Manager",
	"proposed_doj": add_days(today(), 30),
	"pay_level": "Level 10, VII CPC",
	"gross_monthly_salary": 95000,
	"place_of_posting": "NLSIU, Bengaluru",
	"reporting_to": "Registrar",
	"probation_period": "one year",
	"compensation_remarks": "As advertised; Level 10 entry pay.",
	"verbal_offer_date": today(),
	"verbal_offer_compensation": "Rs 95,000 gross per month",
	"verbal_offer_notes": "Candidate can join in a month.",
}


def _pdf(text):
	from frappe.utils.pdf import get_pdf

	return get_pdf(f"<p>{text}</p>")


def _user(role, prefix="offer", user_type="System User"):
	email = f"{prefix}-{frappe.scrub(role)}-{frappe.generate_hash(length=6)}@example.com"
	frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": role.replace("Pathways ", ""),
			"send_welcome_email": 0,
			"user_type": user_type,
			"roles": [{"role": role}],
		}
	).insert(ignore_permissions=True)
	return email


class TestOffer(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		from pathways.patches.v1_0.offer_appointment_orders import execute

		execute()
		settings = frappe.get_single("Pathways Settings")
		settings.set("offer_reviewer_roles", [{"role": "Pathways PNCO"}])
		settings.set("offer_signatory_roles", [{"role": "Pathways Registrar"}])
		settings.offer_requires_green_sheet = 1
		settings.flags.ignore_permissions = True
		settings.save()
		cls.department = frappe.db.get_value("Pathways Department", {}, "name")
		cls.recruiter = _user("Pathways Recruiter")
		cls.reviewer = _user("Pathways PNCO")
		cls.registrar = _user("Pathways Registrar")
		cls.template = frappe.db.get_value("Appointment Order Template", {"is_active": 1}, "name")

	def setUp(self):
		frappe.set_user("Administrator")
		self.job = frappe.get_doc(
			{
				"doctype": "Job Opening",
				"job_title": TEST_JOB_TITLE,
				"track": "Admin" if frappe.db.exists("Recruitment Track", "Admin") else None,
				"department": self.department,
				"employment_type": "Permanent",
				"vacancies": 1,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.app, self.candidate_user = self._application("Asha Rao")
		self.events = []
		patcher = patch.object(api, "send_event", side_effect=lambda event, *a, **kw: self.events.append((event, kw)))
		patcher.start()
		self.addCleanup(patcher.stop)

	def tearDown(self):
		frappe.set_user("Administrator")

	# ------------------------------------------------------------ helpers

	def _application(self, name):
		user = _user(CANDIDATE_ROLE, prefix="cand", user_type="Website User")
		candidate = frappe.get_doc(
			{"doctype": "Candidate", "full_name": name, "email": user, "mobile_number": "9876543210", "address": "12 MG Road\nBengaluru"}
		).insert(ignore_permissions=True)
		app = frappe.get_doc(
			{
				"doctype": "Application",
				"candidate": candidate.name,
				"job_opening": self.job.name,
				"qualifications": [{"degree_level": "Postgraduate", "degree_name": "MBA"}],
			}
		).insert(ignore_permissions=True)
		# Candidates read their applications as owner (if_owner permission).
		app.db_set({"selection_outcome": "Selected", "status": "Selected", "owner": user})
		return app.name, user

	def _approved_sheet(self, recommended=None, waitlist=None):
		sheet = frappe.new_doc("Post-Interview Green Sheet")
		sheet.update(
			{
				"job_opening": self.job.name,
				"recommended_application": recommended,
				"waitlist_application": waitlist,
				"status": "Approved",
				"docstatus": 1,
			}
		)
		sheet.set_new_name()
		sheet.db_insert()  # skip the approval walk; only the outcome matters here
		return sheet.name

	def _draft(self):
		self._approved_sheet(recommended=self.app)
		frappe.set_user(self.recruiter)
		name = api.create_offer(self.app, {**LETTER_FIELDS, "appointment_order_template": self.template})
		return name

	def _to_signature(self, name):
		frappe.set_user(self.recruiter)
		api.submit_for_review(name)
		frappe.set_user(self.reviewer)
		api.approve_offer(name, "Checked against pay scales.")

	def _to_sent(self, name):
		self._to_signature(name)
		frappe.set_user(self.registrar)
		api.sign_offer(name, signature=SIGNATURE)
		frappe.set_user(self.recruiter)
		api.send_offer(name)

	# -------------------------------------------------------------- tests

	def test_green_sheet_gate(self):
		"""Steps 24-26: an offer cannot be created until an approved post-interview green sheet names
		the candidate (recommended or waitlisted). The new offer starts in Draft with a template,
		links the sheet, and a second offer for the same application is refused.
		"""
		frappe.set_user(self.recruiter)
		self.assertRaises(frappe.ValidationError, api.create_offer, self.app)

		# Waitlisted on an approved sheet is enough.
		frappe.set_user("Administrator")
		sheet = self._approved_sheet(recommended=None, waitlist=self.app)
		frappe.set_user(self.recruiter)
		name = api.create_offer(self.app)
		offer = frappe.get_doc(DOCTYPE, name)
		self.assertEqual(offer.status, "Draft")
		self.assertEqual(offer.post_interview_green_sheet, sheet)
		self.assertTrue(offer.appointment_order_template)
		self.assertEqual(offer.status_log[0].to_status, "Draft")
		# One offer per application.
		self.assertRaises(frappe.ValidationError, api.create_offer, self.app)

	def test_green_sheet_requirement_can_be_relaxed(self):
		"""Turning off 'offer requires green sheet' in Pathways Settings lets an offer be created
		without one.
		"""
		frappe.db.set_single_value("Pathways Settings", "offer_requires_green_sheet", 0)
		frappe.clear_document_cache("Pathways Settings", "Pathways Settings")
		try:
			frappe.set_user(self.recruiter)
			name = api.create_offer(self.app)
			self.assertFalse(frappe.db.get_value(DOCTYPE, name, "post_interview_green_sheet"))
		finally:
			frappe.set_user("Administrator")
			frappe.db.set_single_value("Pathways Settings", "offer_requires_green_sheet", 1)
			frappe.clear_document_cache("Pathways Settings", "Pathways Settings")

	def test_review_return_and_approve(self):
		"""Step 26: an incomplete offer cannot go for review. Under review it is locked for the
		drafter; the reviewer must give remarks to return it, which emails the drafter, and
		approving emails the Registrar to sign. The signatory can also return it to Draft.
		"""
		self._approved_sheet(recommended=self.app)
		frappe.set_user(self.recruiter)
		name = api.create_offer(self.app, {"appointment_order_template": self.template})
		# Incomplete: no joining date or pay.
		self.assertRaises(frappe.ValidationError, api.submit_for_review, name)
		api.update_offer(name, LETTER_FIELDS)
		api.submit_for_review(name)
		self.assertEqual(frappe.db.get_value(DOCTYPE, name, "status"), "Under Review")
		self.assertEqual(self.events[-1][0], "offer_review_requested")
		self.assertIn(self.reviewer, self.events[-1][1]["approvers"])
		# Not editable and not approvable by the drafter.
		self.assertRaises(frappe.ValidationError, api.update_offer, name, {"pay_level": "x"})
		self.assertRaises(frappe.PermissionError, api.approve_offer, name)

		frappe.set_user(self.reviewer)
		self.assertRaises(frappe.ValidationError, api.return_offer, name, "")
		api.return_offer(name, "Probation should be six months.")
		offer = frappe.get_doc(DOCTYPE, name)
		self.assertEqual(offer.status, "Draft")
		self.assertEqual(offer.review_remarks, "Probation should be six months.")
		self.assertEqual(self.events[-1][0], "offer_returned")
		self.assertEqual(self.events[-1][1]["approvers"], [self.recruiter])

		frappe.set_user(self.recruiter)
		api.update_offer(name, {"probation_period": "six months"})
		api.submit_for_review(name)
		frappe.set_user(self.reviewer)
		api.approve_offer(name)
		offer = frappe.get_doc(DOCTYPE, name)
		self.assertEqual(offer.status, "Approved for Signature")
		self.assertEqual(offer.reviewed_by, self.reviewer)
		self.assertEqual(self.events[-1][0], "offer_signature_requested")
		self.assertIn(self.registrar, self.events[-1][1]["approvers"])

		# The signatory can also send it back.
		frappe.set_user(self.registrar)
		api.return_offer(name, "Wrong reporting officer.")
		self.assertEqual(frappe.db.get_value(DOCTYPE, name, "status"), "Draft")
		actions = [r.action for r in frappe.get_doc(DOCTYPE, name).status_log]
		self.assertTrue(any("signing" in (a or "") for a in actions))

	def test_sign_with_drawn_and_saved_signature(self):
		"""Step 27: only the signatory role can sign, and only with a real image. Signing stamps
		who and when, generates the letter PDF with the signature and can save it as the default;
		a second offer can then be signed with the saved signature.
		"""
		name = self._draft()
		self._to_signature(name)
		frappe.set_user(self.reviewer)
		self.assertRaises(frappe.PermissionError, api.sign_offer, name, SIGNATURE)
		frappe.set_user(self.registrar)
		self.assertRaises(frappe.ValidationError, api.sign_offer, name, "not-an-image")
		api.sign_offer(name, signature=SIGNATURE, save_as_default=1)
		offer = frappe.get_doc(DOCTYPE, name)
		self.assertEqual(offer.status, "Signed by Registrar")
		self.assertEqual(offer.signed_by, self.registrar)
		self.assertEqual(offer.signature_source, "Drawn")
		self.assertTrue(offer.signed_on)
		self.assertTrue(offer.letter_pdf)
		self.assertTrue(frappe.db.exists("File", {"file_url": offer.letter_pdf, "attached_to_name": name}))
		html = api.preview_letter(name)
		self.assertIn("Asha Rao", html)
		self.assertIn(SIGNATURE[:40], html)
		self.assertNotIn("Signature pending", html)
		self.assertTrue(frappe.get_cached_doc("Pathways Settings").registrar_signature_image)

		# A second offer signed with the saved signature.
		frappe.set_user("Administrator")
		app2, _user2 = self._application("Second Candidate")
		self._approved_sheet(recommended=app2)
		frappe.set_user(self.recruiter)
		name2 = api.create_offer(app2, {**LETTER_FIELDS, "appointment_order_template": self.template})
		self._to_signature(name2)
		frappe.set_user(self.registrar)
		api.sign_offer(name2, use_saved_signature=1)
		offer2 = frappe.get_doc(DOCTYPE, name2)
		self.assertEqual(offer2.signature_source, "Saved Signature")
		self.assertTrue(offer2.registrar_signature.startswith("data:image/"))

	def test_send_and_candidate_accepts(self):
		"""Steps 28-29: sending emails the candidate with the PDF attached and moves the application
		to Offer Extended. Only that candidate can view the letter; accepting needs a joining date
		and records the signed copy. Staff can then upload the Registrar-signed scan.
		"""
		name = self._draft()
		self._to_sent(name)
		offer = frappe.get_doc(DOCTYPE, name)
		self.assertEqual(offer.status, "Sent")
		self.assertEqual(str(offer.offer_date), today())
		self.assertTrue(offer.acceptance_deadline)
		self.assertEqual(frappe.db.get_value("Application", self.app, "status"), "Offer Extended")
		event, kwargs = self.events[-1]
		self.assertEqual(event, "appointment_order")
		self.assertEqual(kwargs["candidate"]["email"], self.candidate_user)
		# The PDF is a File on the offer, so the rule's "attach record files" sends it.
		self.assertEqual(frappe.db.count("File", {"attached_to_doctype": DOCTYPE, "attached_to_name": name, "attached_to_field": "letter_pdf"}), 1)

		# Another candidate cannot see it.
		frappe.set_user("Administrator")
		_other_app, other_user = self._application("Other Person")
		frappe.set_user(other_user)
		self.assertRaises(frappe.PermissionError, api.preview_letter, name)

		frappe.set_user(self.candidate_user)
		mine = api.get_my_offer(self.app)
		self.assertEqual(mine["status"], "Sent")
		self.assertTrue(mine["can_respond"])
		self.assertIn("Asha Rao", api.preview_letter(name))
		self.assertRaises(frappe.ValidationError, api.respond_to_offer, name, "Accepted")  # no joining date
		frappe.set_user("Administrator")
		upload = frappe.get_doc(
			{"doctype": "File", "file_name": "signed.pdf", "content": _pdf("signed"), "is_private": 1}
		)
		upload.insert(ignore_permissions=True)
		upload.db_set("owner", self.candidate_user)
		frappe.set_user(self.candidate_user)
		doj = add_days(today(), 20)
		api.respond_to_offer(name, "Accepted", confirmed_doj=doj, signed_copy_attachment=upload.file_url)
		offer.reload()
		self.assertEqual(offer.status, "Accepted")
		self.assertEqual(str(offer.candidate_confirmed_doj), doj)
		self.assertEqual(offer.signed_copy_attachment, upload.file_url)
		self.assertEqual(frappe.db.get_value("Application", self.app, "status"), "Offer Accepted")

		# Step 29: staff file the scanned Registrar-signed order.
		frappe.set_user("Administrator")
		scan = frappe.get_doc({"doctype": "File", "file_name": "scan.pdf", "content": _pdf("scan"), "is_private": 1})
		scan.insert(ignore_permissions=True)
		scan.db_set("owner", self.recruiter)
		frappe.set_user(self.recruiter)
		api.upload_registrar_scan(name, scan.file_url)
		self.assertEqual(frappe.db.get_value(DOCTYPE, name, "registrar_signed_scan"), scan.file_url)

	def test_candidate_declines(self):
		"""A candidate can decline with a reason; the application becomes Offer Declined and the
		offer can no longer be accepted.
		"""
		name = self._draft()
		self._to_sent(name)
		frappe.set_user(self.candidate_user)
		api.respond_to_offer(name, "Declined", decline_reason="Accepted another offer.")
		offer = frappe.get_doc(DOCTYPE, name)
		self.assertEqual(offer.status, "Declined")
		self.assertEqual(offer.decline_reason, "Accepted another offer.")
		self.assertEqual(frappe.db.get_value("Application", self.app, "status"), "Offer Declined")
		self.assertRaises(frappe.ValidationError, api.respond_to_offer, name, "Accepted", today())

	def test_candidate_does_not_see_internal_drafts(self):
		"""A candidate cannot see or open their offer while it is still an internal draft."""
		name = self._draft()
		frappe.set_user(self.candidate_user)
		self.assertIsNone(api.get_my_offer(self.app))
		self.assertRaises(frappe.PermissionError, api.preview_letter, name)
		self.assertRaises(frappe.PermissionError, api.get_offer, name)

	def test_expiry(self):
		"""The daily job expires a sent offer past its acceptance deadline, logs it, marks the
		application Not Selected, and the candidate can no longer respond.
		"""
		from pathways.tasks import expire_overdue_offers

		name = self._draft()
		self._to_sent(name)
		frappe.set_user("Administrator")
		frappe.db.set_value(DOCTYPE, name, "acceptance_deadline", add_days(today(), -1))
		self.assertIn(name, expire_overdue_offers())
		offer = frappe.get_doc(DOCTYPE, name)
		self.assertEqual(offer.status, "Expired")
		self.assertEqual(offer.status_log[-1].to_status, "Expired")
		self.assertEqual(frappe.db.get_value("Application", self.app, "status"), "Not Selected")
		frappe.set_user(self.candidate_user)
		self.assertRaises(frappe.ValidationError, api.respond_to_offer, name, "Declined")


TEST_JOB_TITLE = "Assistant Manager - Test Offers"


def delete_leftovers():
	"""One-off cleanup for records an earlier version of these tests
	committed (it called respond_to_offer, which used to commit). The tests
	now roll back; run with bench execute pathways.tests.test_offer.delete_leftovers."""
	jobs = frappe.get_all("Job Opening", filters={"job_title": TEST_JOB_TITLE}, pluck="name")
	if not jobs:
		return {}
	apps = frappe.get_all("Application", filters={"job_opening": ["in", jobs]}, fields=["name", "candidate"])
	app_names = [a.name for a in apps]
	candidates = [a.candidate for a in apps if a.candidate]
	emails = frappe.get_all("Candidate", filters={"name": ["in", candidates or [""]]}, pluck="email")
	offers = frappe.get_all(DOCTYPE, filters={"application": ["in", app_names or [""]]}, pluck="name")
	sheets = frappe.get_all("Post-Interview Green Sheet", filters={"job_opening": ["in", jobs]}, pluck="name")
	for f in frappe.get_all("File", filters={"attached_to_doctype": DOCTYPE, "attached_to_name": ["in", offers or [""]]}, pluck="name"):
		frappe.delete_doc("File", f, ignore_permissions=True, force=True)
	for name in offers:
		frappe.db.delete("Offer Status Log", {"parent": name})
		frappe.db.delete(DOCTYPE, {"name": name})
	for table in ("Compensation Table Row", "Approval Chain Step", "Green Sheet Approval Log"):
		frappe.db.delete(table, {"parenttype": "Post-Interview Green Sheet", "parent": ["in", sheets or [""]]})
	frappe.db.delete("Post-Interview Green Sheet", {"name": ["in", sheets or [""]]})
	for name in app_names:
		frappe.delete_doc("Application", name, ignore_permissions=True, force=True)
	for name in candidates:
		frappe.delete_doc("Candidate", name, ignore_permissions=True, force=True)
	for name in jobs:
		frappe.delete_doc("Job Opening", name, ignore_permissions=True, force=True)
	staff = frappe.get_all("User", filters={"name": ["like", "offer-%@example.com"]}, pluck="name")
	for user in [*emails, *staff]:
		if user and frappe.db.exists("User", user):
			frappe.delete_doc("User", user, ignore_permissions=True, force=True)
	frappe.db.commit()
	return {"jobs": len(jobs), "applications": len(app_names), "offers": len(offers), "green_sheets": len(sheets), "users": len(emails) + len(staff)}
