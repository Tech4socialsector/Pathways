# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class Interview(Document):
	def validate(self):
		self.set_applicant_details()
		self.validate_round_specific_fields()
		self.validate_hr_assessors()

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

	def validate_hr_assessors(self):
		"""Round 1 (HR interaction) only; at most the number set in Pathways
		Settings (2 by default), each person once."""
		if self.round_type != "HR Interaction":
			self.set("hr_assessors", [])
			return
		limit = cint(frappe.get_cached_doc("Pathways Settings").get("hr_assessors_per_interview")) or 2
		seen = set()
		for row in self.hr_assessors:
			if row.assessor in seen:
				frappe.throw(_("{0} is listed twice as an HR assessor.").format(row.assessor))
			seen.add(row.assessor)
			row.assessor_name = frappe.utils.get_fullname(row.assessor)
		if len(seen) > limit:
			frappe.throw(_("A Round 1 interview can have at most {0} HR assessors.").format(limit))

	def hr_assessor_list(self):
		return [row.assessor for row in self.get("hr_assessors") or []]
