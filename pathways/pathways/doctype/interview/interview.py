# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Interview(Document):
	def validate(self):
		self.set_applicant_details()
		self.validate_round_specific_fields()

	def set_applicant_details(self):
		"""Name, job and position shown in lists and links (from the application)."""
		app = frappe.db.get_value("Application", self.application, ["candidate", "job_opening"], as_dict=True) or {}
		self.candidate = app.get("candidate")
		self.candidate_name = frappe.db.get_value("Candidate", app.get("candidate"), "full_name") if app.get("candidate") else None
		job = frappe.db.get_value("Job Opening", app.get("job_opening"), ["job_title", "position"], as_dict=True) or {}
		self.job_title = job.get("job_title")
		self.position = job.get("position")

	def validate_round_specific_fields(self):
		if self.round_type == "Final" and not self.selection_committee:
			frappe.throw("A Selection Committee must be linked for a Final round Interview.")
