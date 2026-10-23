# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Advertising and closing (workflow steps 3 and 6), the public job feeds,
tagging colleagues on a job (step 7), editing the shortlisting committee
(step 8) and the historical application import."""

import base64
import random
import xml.etree.ElementTree as ET
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from pathways.api import application_import, job_opening, public_feed, scoring
from pathways.pathways.doctype.pre_recruitment_green_sheet.pre_recruitment_green_sheet import sync_job_opening
from pathways.permissions import TAGGED_ROLE


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


def _mobile():
	return "9" + "".join(random.choice("0123456789") for _ in range(9))


def _events(send, event):
	return [c for c in send.call_args_list if c.args and c.args[0] == event]


class TestPlatform(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.track = frappe.db.get_value("Recruitment Track", {}, "name")
		self.department = frappe.db.get_value("Pathways Department", {}, "name")
		self.committed = []  # records that outlive the test's rollback

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		for doctype, name in reversed(self.committed):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True, ignore_missing=True)
		if self.committed:
			frappe.db.commit()

	def _job(self, title="Platform Test Post", status="Draft", deadline_days=10):
		job = frappe.get_doc(
			{
				"doctype": "Job Opening",
				"job_title": f"{title} {frappe.generate_hash(length=5)}",
				"track": self.track,
				"department": self.department,
				"employment_type": "Permanent",
				"vacancies": 1,
				"jd_text": "<p>Teach and research.</p>",
			}
		)
		job.flags.ignore_mandatory = True
		with patch("pathways.utils.communication.send_event"):
			job.insert(ignore_permissions=True)
		updates = {"status": status, "application_deadline": add_days(now_datetime(), deadline_days)}
		if status == "Advertised":
			updates["advertisement_url"] = f"http://test/pathways/portal/jobs/{job.name}"
		frappe.db.set_value("Job Opening", job.name, updates)
		return frappe.get_doc("Job Opening", job.name)

	def _application(self, job, status="Submitted"):
		candidate = frappe.get_doc(
			{"doctype": "Candidate", "full_name": "Platform Candidate", "email": f"plat-{frappe.generate_hash(length=8)}@example.com", "mobile_number": _mobile()}
		)
		candidate.flags.ignore_validate = True
		candidate.insert(ignore_permissions=True)
		app = frappe.get_doc({"doctype": "Application", "candidate": candidate.name, "job_opening": job})
		app.flags.ignore_validate = True
		app.flags.ignore_mandatory = True
		app.insert(ignore_permissions=True)
		frappe.db.set_value("Application", app.name, "status", status)
		return app.name

	# ------------------------------------------------------------ step 3

	def test_approval_requests_official_notification_once(self):
		"""Step 3: approving the pre-recruitment green sheet approves the job and asks the
		Registrar/Communications for the official notification, once only.
		"""
		job = self._job()
		sheet = frappe._dict(name="PWY-PREGS-TEST", job_opening=job.name, docstatus=1, status="Approved")
		with patch("pathways.utils.communication.send_event") as send:
			sync_job_opening(sheet)
			self.assertEqual(frappe.db.get_value("Job Opening", job.name, "status"), "Approved")
			calls = _events(send, "notification_requested")
			self.assertEqual(len(calls), 1)
			self.assertEqual(calls[0].args[2], job.name)
			self.assertEqual(calls[0].args[3]["green_sheet"], "PWY-PREGS-TEST")
			# The job is already Approved: a later update sends nothing more.
			sync_job_opening(sheet)
			self.assertEqual(len(_events(send, "notification_requested")), 1)
		self.assertTrue(frappe.db.exists("Recruitment Email Rule", "notification_requested"))

	def test_publishing_tracker_by_communications(self):
		"""Step 3: Communications can record where the ad is published (records who did it), and
		links that are not full URLs are rejected.
		"""
		from pathways.api import job_notice

		job = self._job(status="Advertised")
		comms = _user("plat-comms@example.com", "Comms", roles=("Pathways Communications",))
		frappe.set_user(comms)
		out = job_notice.save_publishing(job.name, {"linkedin_url": "https://www.linkedin.com/posts/x", "linkedin_published_on": "2026-10-20"})
		self.assertEqual(out["publishing"]["linkedin_url"], "https://www.linkedin.com/posts/x")
		self.assertEqual(out["publishing"]["published_by"], comms)
		with self.assertRaises(frappe.ValidationError):
			job_notice.save_publishing(job.name, {"website_url": "www.nls.ac.in"})

	# ------------------------------------------------------------ step 6

	def test_auto_close_syncs_notification_and_emails_once(self):
		"""Step 6: the hourly job closes an advertised job past its deadline, removes the public link,
		closes its notification and emails 'ad closed' once, even if it runs again.
		"""
		from pathways.tasks import close_expired_job_openings

		job = self._job(status="Advertised", deadline_days=-1)
		notification = frappe.get_doc(
			{"doctype": "Recruitment Notification", "job_opening": job.name, "notification_type": "Informal", "status": "Published"}
		).insert(ignore_permissions=True)
		frappe.db.commit()
		self.committed += [("File", job.files_folder), ("Job Opening", job.name), ("Recruitment Notification", notification.name)]

		with patch("pathways.utils.communication.send_event") as send:
			close_expired_job_openings()
			mine = [c for c in _events(send, "ad_closed") if c.args[2] == job.name]
			self.assertEqual(len(mine), 1)
			self.assertEqual(frappe.db.get_value("Job Opening", job.name, "status"), "Closed")
			self.assertIsNone(frappe.db.get_value("Job Opening", job.name, "advertisement_url"))
			self.assertEqual(frappe.db.get_value("Recruitment Notification", notification.name, "status"), "Closed")
			close_expired_job_openings()
			self.assertEqual(len([c for c in _events(send, "ad_closed") if c.args[2] == job.name]), 1)

	# ------------------------------------------------------------ feeds

	def test_feeds_list_only_open_advertised_jobs(self):
		"""The Indeed XML and website JSON feeds list only open, advertised jobs with the required
		tags, and expose only public fields.
		"""
		open_job = self._job("Feed Open", status="Advertised")
		draft_job = self._job("Feed Draft", status="Draft")
		expired = self._job("Feed Expired", status="Advertised", deadline_days=-1)

		root = ET.fromstring(public_feed.build_indeed_xml())
		self.assertEqual(root.tag, "source")
		refs = [j.findtext("referencenumber") for j in root.findall("job")]
		self.assertIn(open_job.name, refs)
		self.assertNotIn(draft_job.name, refs)
		self.assertNotIn(expired.name, refs)
		node = next(j for j in root.findall("job") if j.findtext("referencenumber") == open_job.name)
		for tag in ("title", "date", "url", "company", "city", "country", "description", "jobtype"):
			self.assertTrue(node.findtext(tag), tag)
		self.assertEqual(node.findtext("jobtype"), "fulltime")

		feed = public_feed.build_json_feed()
		ids = [j["id"] for j in feed["jobs"]]
		self.assertIn(open_job.name, ids)
		self.assertNotIn(draft_job.name, ids)
		allowed = {
			"id", "title", "department", "track", "designation", "vacancies", "employment_type", "tenure", "pay_level",
			"application_start", "application_deadline", "posted_on", "url", "jd_url", "description_html",
			"notification_number", "notification_url",
		}
		self.assertTrue(set(feed["jobs"][0]) <= allowed)
		self.assertTrue(public_feed.JobFeedPage("jobs-feed.xml").can_render())
		self.assertFalse(public_feed.JobFeedPage("jobs-feed.html").can_render())

	# ------------------------------------------------------------ step 7

	def test_tagged_colleague_reads_only_tagged_job(self):
		"""Step 7: tagging a colleague emails them once and grants read-only access to that job and its
		applications only. Holding the role without a tag gives nothing, and untagging removes
		the role.
		"""
		job = self._job("Tagged Job")
		other = self._job("Untagged Job")
		app = self._application(job.name)
		other_app = self._application(other.name)
		colleague = _user("plat-colleague@example.com", "Colleague")
		outsider = _user("plat-outsider@example.com", "Outsider", roles=(TAGGED_ROLE,))

		with patch("pathways.utils.communication.send_event") as send:
			job_opening.set_job_colleagues(job.name, [{"user": colleague, "access_note": "HoD review"}])
			tagged = _events(send, "colleague_tagged")
			self.assertEqual(len(tagged), 1)
			self.assertEqual(tagged[0].kwargs["approvers"], [colleague])
			# Saving again with the same list does not re-notify.
			job_opening.set_job_colleagues(job.name, [{"user": colleague, "access_note": "HoD review"}])
			self.assertEqual(len(_events(send, "colleague_tagged")), 1)
		self.assertIn(TAGGED_ROLE, frappe.get_roles(colleague))

		frappe.set_user(colleague)
		self.assertTrue(frappe.has_permission("Application", "read", doc=app))
		self.assertFalse(frappe.has_permission("Application", "write", doc=app))
		self.assertFalse(frappe.has_permission("Application", "read", doc=other_app))
		visible = frappe.get_list("Application", pluck="name", limit_page_length=0)
		self.assertIn(app, visible)
		self.assertNotIn(other_app, visible)
		self.assertTrue(frappe.has_permission("Job Opening", "read", doc=job.name))
		self.assertFalse(frappe.has_permission("Job Opening", "read", doc=other.name))

		frappe.set_user(outsider)
		self.assertFalse(frappe.has_permission("Application", "read", doc=app))
		self.assertNotIn(app, frappe.get_list("Application", pluck="name", limit_page_length=0))

		frappe.set_user("Administrator")
		with patch("pathways.utils.communication.send_event"):
			job_opening.set_job_colleagues(job.name, [])
		self.assertNotIn(TAGGED_ROLE, frappe.get_roles(colleague))

	def test_job_folder_created_idempotently(self):
		"""Step 7: each job gets a file folder under Home/Pathways, and asking again returns the same
		folder instead of creating another.
		"""
		from pathways.utils.folders import ensure_job_folder

		job = self._job("Folder Job")
		folder = frappe.db.get_value("Job Opening", job.name, "files_folder")
		self.assertTrue(folder and folder.startswith("Home/Pathways/"))
		self.assertTrue(frappe.db.exists("File", {"name": folder, "is_folder": 1}))
		self.assertEqual(ensure_job_folder(job.name), folder)

	# ------------------------------------------------------------ step 8

	def test_update_committee_emails_only_new_members(self):
		"""Step 8: editing the shortlisting committee updates members, office order and deadline, and
		emails only the newly added member.
		"""
		job = self._job("Committee Job")
		a, b, c = (_user(f"plat-member-{i}@example.com", f"Member {i}") for i in "abc")
		with patch("pathways.utils.communication.send_event"):
			scoring.create_shortlisting_committee(job.name, [a, b], "OO/1", shortlisting_deadline="2026-12-01")
		with patch("pathways.utils.communication.send_event") as send:
			res = scoring.update_shortlisting_committee(
				job.name, members=[a, c], office_order_reference="OO/2", shortlisting_deadline="2026-12-15",
				office_order_attachment="/private/files/oo.pdf",
			)
			self.assertEqual(res["added"], [c])
			calls = _events(send, "committee_assigned")
			self.assertEqual(len(calls), 1)
			self.assertEqual([r["email"] for r in calls[0].kwargs["recipients"]], [c])
			self.assertIsNone(calls[0].kwargs.get("job_opening"))
		committee = frappe.get_doc("Shortlisting Committee", {"job_opening": job.name})
		self.assertEqual([m.member for m in committee.members], [a, c])
		self.assertEqual(committee.office_order_attachment, "/private/files/oo.pdf")
		self.assertEqual(str(committee.shortlisting_deadline), "2026-12-15")

	# ------------------------------------------------------------ historical import

	def _csv(self, job, statuses):
		lines = ["Job Opening ID,Full Name,Email,Mobile Number,Status"]
		for i, status in enumerate(statuses):
			lines.append(f"{job},Past Person {i},past-{frappe.generate_hash(length=8)}@example.com,{_mobile()},{status}")
		return "data:text/csv;base64," + base64.b64encode("\n".join(lines).encode()).decode()

	def test_historical_import_statuses_and_no_emails(self):
		"""Historical import accepts past statuses (with aliases such as Not Shortlisted), rejects
		unknown ones, and never creates portal logins or sends acknowledgements; a normal import
		refuses past statuses.
		"""
		job = self._job("Past Cycle", status="Closed")
		content = self._csv(job.name, ["Joined", "Not Shortlisted", "Interview Completed", "Bogus"])

		# A normal import refuses past statuses.
		normal = application_import.preview_import("past.csv", content)
		self.assertEqual(normal["valid"], 0)

		preview = application_import.preview_import("past.csv", content, historical=1)
		self.assertEqual(preview["valid"], 3)
		bad = [r for r in preview["rows"] if r["errors"]]
		self.assertEqual(len(bad), 1)
		self.assertIn("Status", bad[0]["errors"][0])

		with patch("pathways.utils.candidate_account.queue_portal_account") as portal, patch("frappe.enqueue") as enqueue:
			result = application_import.run_import("past.csv", content, send_login=1, send_acknowledgement=1, historical=1)
			portal.assert_not_called()
			self.assertFalse([c for c in enqueue.call_args_list if "send_acknowledgement" in str(c)])
		self.assertEqual(len(result["done"]), 3)
		statuses = sorted(frappe.db.get_value("Application", d["name"], "status") for d in result["done"])
		self.assertEqual(statuses, sorted(["Joined", "Not Selected", "Interview Completed"]))
