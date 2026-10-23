# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ShortlistingNote(Document):
	"""Workflow step 14: the job's final shortlist after Round 1 and the
	Shortlisting Note that goes to the Selection Committee. One per job."""

	def validate(self):
		seen = set()
		for row in self.final_shortlist:
			if row.application in seen:
				frappe.throw(_("{0} is on the final shortlist twice.").format(row.application))
			seen.add(row.application)
			app = frappe.db.get_value("Application", row.application, ["job_opening", "application_id", "candidate"], as_dict=True)
			if not app or app.job_opening != self.job_opening:
				frappe.throw(_("{0} is not an application for this job.").format(row.application))
			row.application_id = app.application_id
			row.candidate_name = frappe.db.get_value("Candidate", app.candidate, "full_name")
		self.prepared_on = frappe.utils.now_datetime()
