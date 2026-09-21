# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ScoringRubricTemplate(Document):
	def validate(self):
		if self.scoring_mode == "Weighted Score" and not self.criteria:
			frappe.throw("At least one Scoring Criterion is required when Scoring Mode is 'Weighted Score'.")

	@property
	def max_total_score(self):
		return sum(row.max_score or 0 for row in self.criteria)
