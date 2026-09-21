# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class Application(Document):
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


@frappe.whitelist()
def check_duplicate(email, mobile_number, job_opening):
	"""Server-side duplicate check used by the public Candidate Application
	web form, ahead of insert. Frontend validation is UX-only per policy;
	this is the authoritative check.
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
