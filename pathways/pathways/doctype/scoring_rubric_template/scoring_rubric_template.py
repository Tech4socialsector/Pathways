# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ScoringRubricTemplate(Document):
	def validate(self):
		# A Shortlisting rubric without criteria is a shortlist / reject
		# decision with remarks (e.g. Admin); interview rounds are scored.
		if not self.criteria and self.stage != "Shortlisting":
			frappe.throw("At least one Scoring Criterion is required for the {0} stage.".format(self.stage))

	@property
	def max_total_score(self):
		return sum(row.max_score or 0 for row in self.criteria)
