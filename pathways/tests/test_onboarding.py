# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Onboarding (steps 31, 34, folder 12): offer accepted -> checklist, draft
joining and onboarding email (once); joining confirmed -> IT request and
intimation; joined -> application status and Employee; document upload,
verification and resubmission; IT completion; row-level permissions."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from pathways.api import documents as documents_api
from pathways.api import it_requests as it_api
from pathways.api import joining as joining_api
from pathways.utils import onboarding


def _user(email, first_name, roles, user_type="System User"):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"user_type": user_type,
				"send_welcome_email": 0,
				"roles": [{"role": r} for r in roles],
			}
		).insert(ignore_permissions=True)
	return email


def _blank_pdf():
	from io import BytesIO

	from pypdf import PdfWriter

	writer = PdfWriter()
	writer.add_blank_page(width=72, height=72)
	out = BytesIO()
	writer.write(out)
	return out.getvalue()


def _events(mock, event):
	return [c for c in mock.call_args_list if c.args and c.args[0] == event]


class TestOnboarding(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.track = frappe.db.get_value("Recruitment Track", {}, "name")
		self.department = frappe.db.get_value("Pathways Department", {}, "name")
		self.job = frappe.get_doc(
			{
				"doctype": "Job Opening",
				"job_title": "Test Onboarding Post",
				"track": self.track,
				"department": self.department,
				"employment_type": "Contract",
				"vacancies": 1,
			}
		)
		self.job.flags.ignore_mandatory = True
		self.job.insert(ignore_permissions=True)
		self.sent = patch("pathways.utils.onboarding.send_event")
		self.send_event = self.sent.start()
		self.addCleanup(self.sent.stop)

	def tearDown(self):
		frappe.set_user("Administrator")

	# ------------------------------------------------------------ helpers

	def _candidate(self, label):
		email = f"onb-{label}-{frappe.generate_hash(length=6)}@example.com"
		_user(email, f"Onb {label}", ["Pathways Candidate"], user_type="Website User")
		candidate = frappe.get_doc(
			{
				"doctype": "Candidate",
				"full_name": f"Onb {label}",
				"email": email,
				"mobile_number": "98" + frappe.generate_hash(length=8).translate(str.maketrans("abcdef", "123456"))[:8],
			}
		)
		candidate.flags.ignore_validate = True
		candidate.insert(ignore_permissions=True)
		app = frappe.get_doc({"doctype": "Application", "candidate": candidate.name, "job_opening": self.job.name})
		app.flags.ignore_validate = True
		app.flags.ignore_mandatory = True
		app.insert(ignore_permissions=True)
		# As on the portal: the candidate owns their records.
		frappe.db.set_value("Candidate", candidate.name, "owner", email)
		frappe.db.set_value("Application", app.name, {"status": "Offer Extended", "owner": email})
		return candidate, app

	def _offer(self, app, doj=None):
		"""Only fields that exist on the (evolving) Offer DocType are set."""
		meta = frappe.get_meta("Offer Appointment Order")
		values = {"doctype": "Offer Appointment Order", "application": app.name, "status": "Sent"}
		for field, value in (("candidate", app.candidate), ("job_opening", self.job.name), ("offer_date", today())):
			if meta.has_field(field):
				values[field] = value
		offer = frappe.get_doc(values)
		offer.flags.ignore_validate = True
		offer.flags.ignore_mandatory = True
		offer.insert(ignore_permissions=True)
		offer.reload()
		offer.status = "Accepted"
		offer.candidate_confirmed_doj = doj or add_days(today(), 10)
		offer.flags.ignore_validate = True
		offer.flags.ignore_mandatory = True
		offer.save(ignore_permissions=True)
		return offer

	def _accepted(self, label, doj=None):
		candidate, app = self._candidate(label)
		offer = self._offer(app, doj)
		joining = frappe.get_doc("Joining", {"application": app.name})
		return candidate, app, offer, joining

	# -------------------------------------------------------------- tests

	def test_offer_accepted_starts_onboarding_once(self):
		"""Step 34: accepting an offer creates the document checklist and a draft joining with the
		candidate's date, and sends one onboarding email with the portal link. Saving the offer
		again or restarting onboarding creates nothing twice.
		"""
		_candidate, app, offer, joining = self._accepted("accept")
		collection = frappe.get_doc("Document Collection", {"application": app.name})
		self.assertTrue(collection.checklist)
		self.assertTrue(all(row.requirement for row in collection.checklist))
		self.assertTrue(collection.onboarding_email_sent_on)
		self.assertEqual(joining.status, "Draft")
		self.assertEqual(str(joining.confirmed_doj), str(offer.candidate_confirmed_doj))
		self.assertTrue(joining.reporting_location)
		self.assertEqual(len(_events(self.send_event, "onboarding")), 1)
		context = _events(self.send_event, "onboarding")[0].kwargs["context"]
		self.assertIn("/pathways/portal/applications/", context["portal_link"])

		# Saving the accepted offer again, or starting again, changes nothing.
		offer.reload()
		offer.flags.ignore_validate = True
		offer.save(ignore_permissions=True)
		onboarding.start_onboarding(offer.name)
		self.assertEqual(len(_events(self.send_event, "onboarding")), 1)
		self.assertEqual(frappe.db.count("Joining", {"application": app.name}), 1)
		self.assertEqual(frappe.db.count("Document Collection", {"application": app.name}), 1)

	def test_confirm_creates_it_request_and_reschedule_updates_it(self):
		"""Step 31 / IT intimation: confirming a joining creates the IT & Facilities request and
		emails IT. Changing the date records the reschedule, updates the request and sends IT an
		'updated' email.
		"""
		_candidate, _app, _offer, joining = self._accepted("confirm")
		self.assertFalse(joining.it_facilities_request)
		joining_api.set_status(joining.name, "Confirmed", {"reporting_manager": "Dr. Manager"})
		joining.reload()
		self.assertEqual(joining.status, "Confirmed")
		self.assertEqual(joining.confirmed_by, "Administrator")
		self.assertTrue(joining.it_facilities_request)
		request = frappe.get_doc("IT Facilities Provisioning Request", joining.it_facilities_request)
		self.assertEqual(str(request.date_of_joining), str(joining.confirmed_doj))
		calls = _events(self.send_event, "it_facilities")
		self.assertEqual(len(calls), 1)
		self.assertFalse(calls[0].kwargs["context"]["updated"])

		new_doj = add_days(today(), 20)
		joining_api.save_joining(joining.name, {"confirmed_doj": new_doj, "reschedule_reason": "Notice period"})
		joining.reload()
		self.assertEqual(joining.reschedule_count, 1)
		self.assertTrue(joining.previous_doj)
		self.assertEqual(str(frappe.db.get_value("IT Facilities Provisioning Request", request.name, "date_of_joining")), str(new_doj))
		calls = _events(self.send_event, "it_facilities")
		self.assertEqual(len(calls), 2)
		self.assertTrue(calls[1].kwargs["context"]["updated"])

	def test_joined_sets_application_status_and_employee(self):
		"""Step 31: a joiner cannot be marked Joined before the date of joining. Marking Joined sets
		the application status and history; the Employee record is created only once all
		mandatory documents are verified.
		"""
		_candidate, app, _offer, joining = self._accepted("joined", doj=add_days(today(), 3))
		joining_api.set_status(joining.name, "Confirmed")
		# Not before the date of joining.
		self.assertRaises(frappe.ValidationError, joining_api.set_status, joining.name, "Joined")
		joining_api.save_joining(joining.name, {"confirmed_doj": today()})
		joining_api.set_status(joining.name, "Joined")
		joining.reload()
		self.assertEqual(frappe.db.get_value("Application", app.name, "status"), "Joined")
		self.assertTrue(frappe.db.exists("Application Status History", {"application": app.name, "new_status": "Joined"}))
		self.assertEqual(str(joining.actual_joining_date), today())
		# Documents not verified yet: no Employee until they are.
		self.assertFalse(joining.employee)

		collection = frappe.get_doc("Document Collection", {"application": app.name})
		for row in collection.checklist:
			row.attachment = "/private/files/test-onboarding.pdf"
			row.status = "Submitted"
		collection.save(ignore_permissions=True)
		for row in collection.checklist:
			if row.requirement == "Mandatory":
				documents_api.verify_document(collection.name, row.document_type, True)
		collection.reload()
		self.assertEqual(collection.overall_status, "Complete")
		joining.reload()
		self.assertTrue(joining.employee)
		employee = frappe.get_doc("Pathways Employee", joining.employee)
		self.assertEqual(employee.source_application, app.name)
		# Joined is not stepped back to Documents Verified.
		self.assertEqual(frappe.db.get_value("Application", app.name, "status"), "Joined")

	def test_upload_and_resubmission(self):
		"""Step 34: a candidate's upload is attached to their checklist row. Asking for resubmission
		needs a reason, which is emailed to the candidate. A candidate can never verify documents.
		"""
		candidate, app, _offer, _joining = self._accepted("upload")
		collection = frappe.get_doc("Document Collection", {"application": app.name})
		row = next(r for r in collection.checklist if r.requirement == "Mandatory")

		frappe.set_user(candidate.email)
		file = frappe.get_doc(
			{"doctype": "File", "file_name": f"onboarding-{frappe.generate_hash(length=6)}.pdf", "is_private": 1, "content": _blank_pdf()}
		).insert(ignore_permissions=True)
		formats = frappe.db.get_value("Document Type Master", row.document_type, "allowed_formats") or ""
		if formats and "pdf" not in formats.lower():
			frappe.db.set_value("Document Type Master", row.document_type, "allowed_formats", formats + ", PDF")
		documents_api.upload_document(collection.name, row.document_type, file.file_url)
		frappe.set_user("Administrator")
		collection.reload()
		uploaded = next(r for r in collection.checklist if r.document_type == row.document_type)
		self.assertEqual(uploaded.status, "Submitted")
		self.assertEqual(frappe.db.get_value("File", file.name, "attached_to_name"), collection.name)

		# A reason is required to ask for resubmission; the candidate is emailed.
		self.assertRaises(frappe.ValidationError, documents_api.verify_document, collection.name, row.document_type, False, "")
		documents_api.verify_document(collection.name, row.document_type, False, "Scan is unreadable")
		collection.reload()
		self.assertEqual(collection.overall_status, "Resubmission Requested")
		calls = _events(self.send_event, "document_resubmission")
		self.assertEqual(len(calls), 1)
		self.assertEqual(calls[0].kwargs["context"]["rejection_reason"], "Scan is unreadable")

		# A candidate can never verify.
		frappe.set_user(candidate.email)
		self.assertRaises(frappe.PermissionError, documents_api.verify_document, collection.name, row.document_type, True)

	def test_it_request_completion_notifies(self):
		"""IT intimation: an IT request cannot be completed until the laptop and official email are
		done; completing it emails the recruitment team once and locks the request.
		"""
		_candidate, _app, _offer, joining = self._accepted("it")
		joining_api.set_status(joining.name, "Confirmed")
		request = frappe.db.get_value("Joining", joining.name, "it_facilities_request")
		self.assertRaises(frappe.ValidationError, it_api.save_request, request, {"laptop_arranged": 1}, True)
		row = it_api.save_request(request, {"laptop_arranged": 1, "official_email_created": 1, "official_email": "new.joiner@nls.ac.in"})
		self.assertEqual(row.status, "In Progress")
		row = it_api.save_request(request, {"access_card_issued": 1, "seating_arranged": 1}, True)
		self.assertEqual(row.status, "Completed")
		self.assertEqual(len(_events(self.send_event, "it_facilities_completed")), 1)
		self.assertRaises(frappe.ValidationError, it_api.save_request, request, {"remarks": "again"})

	def test_permissions(self):
		"""Row-level access: a candidate sees only their own joining and document checklist, never
		IT requests or another candidate's records; IT staff see IT requests but not joinings.
		"""
		cand_a, app_a, _offer_a, joining_a = self._accepted("perm-a")
		_cand_b, app_b, _offer_b, joining_b = self._accepted("perm-b")
		joining_api.set_status(joining_a.name, "Confirmed")
		it_user = _user("onb-it-staff@example.com", "IT Staff", ["Pathways IT Facilities"])

		frappe.set_user(cand_a.email)
		self.assertEqual(set(frappe.get_list("Joining", pluck="name")), {joining_a.name})
		self.assertEqual(set(frappe.get_list("Document Collection", pluck="application")), {app_a.name})
		self.assertFalse(frappe.has_permission("Joining", doc=joining_b.name))
		self.assertFalse(frappe.has_permission("IT Facilities Provisioning Request", "read"))
		checklist = documents_api.get_my_document_checklist(app_a.name)
		self.assertTrue(checklist["checklist"])
		self.assertRaises(frappe.PermissionError, documents_api.get_my_document_checklist, app_b.name)

		frappe.set_user(it_user)
		requests = it_api.list_requests()
		self.assertIn(frappe.db.get_value("Joining", joining_a.name, "it_facilities_request"), [r.name for r in requests["requests"]])
		self.assertTrue(requests["can_write"])
		self.assertFalse(frappe.has_permission("Joining", "read"))
