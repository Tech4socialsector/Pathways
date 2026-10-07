# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import today


class Application(Document):
	def before_insert(self):
		if not self.application_date:
			self.application_date = today()

		# Job Application web form (pathways/web_form/job_application): the
		# form has no candidate field, so the applicant is always the
		# logged-in user — never a value sent by the browser.
		if frappe.flags.in_web_form:
			self.validate_web_form_submission()
			self.candidate = get_or_create_candidate_for_user(frappe.session.user)

	def validate_web_form_submission(self):
		"""The web form is a plain DocType form: it cannot collect screening
		answers or required documents, which api.application.submit_application
		validates. Accept it only where those would not apply, with the same
		gates as the portal (open job, candidate account)."""
		from pathways.utils.application_form import get_required_documents, is_accepting_applications, not_accepting_message

		if frappe.db.get_value("User", frappe.session.user, "user_type") != "Website User":
			frappe.throw("Staff accounts cannot apply. Please register with a personal email address.")

		job = frappe.get_doc("Job Opening", self.job_opening)
		if not is_accepting_applications(job):
			frappe.throw(not_accepting_message(job))
		if job.screening_questions or any(d["mandatory"] for d in get_required_documents(job)):
			frappe.throw(
				"This position needs screening answers or documents. Please apply through the job posting: "
				f"{frappe.utils.get_url('/pathways/portal/jobs/' + job.name)}"
			)

	def validate(self):
		self.check_duplicate()
		self.set_application_id()

	def check_duplicate(self):
		if not (self.candidate and self.job_opening):
			return

		existing = frappe.db.exists(
			"Application",
			{
				"candidate": self.candidate,
				"job_opening": self.job_opening,
				"name": ["!=", self.name or ""],
				"status": ["!=", "Withdrawn"],
			},
		)
		if existing:
			frappe.throw(
				f"An application from this candidate for this Job Opening already exists ({existing}). "
				f"Duplicate applications are not permitted."
			)

	def set_application_id(self):
		if not self.application_id:
			self.application_id = make_autoname("PWY-APP-.YYYY.-.######")


def check_duplicate(email, mobile_number, job_opening):
	"""Internal duplicate lookup by email (falling back to mobile). Not an
	endpoint: exposing it let anyone probe who had applied where. The
	authoritative check for submissions is in api.application.submit_application.
	"""
	candidate_name = frappe.db.get_value(
		"Candidate", {"email": (email or "").strip().lower()}, "name"
	)
	if not candidate_name:
		candidate_by_mobile = frappe.db.get_value(
			"Candidate", {"mobile_number": mobile_number}, "name"
		)
		candidate_name = candidate_by_mobile

	if not candidate_name:
		return {"duplicate": False}

	existing = frappe.db.exists(
		"Application",
		{
			"candidate": candidate_name,
			"job_opening": job_opening,
			"status": ["!=", "Withdrawn"],
		},
	)
	return {"duplicate": bool(existing), "candidate": candidate_name}


def get_or_create_candidate_for_user(user):
	"""Candidate whose email is the user's login — the same link the
	candidate portal uses (get_my_applications)."""
	if user == "Guest":
		frappe.throw("Please log in to apply.", frappe.PermissionError)

	email = user.strip().lower()
	candidate = frappe.db.get_value("Candidate", {"email": email}, "name")
	if candidate:
		return candidate

	full_name, mobile_no, phone = frappe.db.get_value("User", user, ["full_name", "mobile_no", "phone"])
	mobile = mobile_no or phone
	if not mobile:
		frappe.throw(
			"Please add your mobile number under My Account before applying.",
			title="Mobile Number Required",
		)

	doc = frappe.new_doc("Candidate")
	doc.update({"full_name": full_name or email, "email": email, "mobile_number": mobile})
	doc.insert(ignore_permissions=True)
	return doc.name
