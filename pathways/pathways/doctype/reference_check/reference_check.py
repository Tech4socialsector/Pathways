# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""One referee's feedback on one application (workflow step 21).

The referee answers either through a tokenised public form or over the
phone, recorded by the recruiter (pathways.api.reference_checks). Only a
hash of the referee's link token is stored, so the database never holds a
usable link. Candidates have no Role Permission on this DocType: they never
see what their referees said."""

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class ReferenceCheck(Document):
	def validate(self):
		if self.application and not self.candidate_name:
			candidate = frappe.db.get_value("Application", self.application, "candidate")
			self.candidate_name = frappe.db.get_value("Candidate", candidate, "full_name") if candidate else None
		if self.status == "Completed" and not self.completed_on:
			self.completed_on = now_datetime()
