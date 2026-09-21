# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ShortlistingScore(Document):
	def validate(self):
		self.validate_committee_matches_application()
		self.populate_rubric_criteria()
		self.compute_total_score()

	def validate_committee_matches_application(self):
		if not (self.application and self.shortlisting_committee):
			return

		app_job_opening = frappe.db.get_value("Application", self.application, "job_opening")
		committee_job_opening = frappe.db.get_value(
			"Shortlisting Committee", self.shortlisting_committee, "job_opening"
		)
		if app_job_opening != committee_job_opening:
			frappe.throw(
				"This Shortlisting Committee is not assigned to the Job Opening of the given Application."
			)

	def populate_rubric_criteria(self):
		if not self.application:
			return

		track = frappe.db.get_value(
			"Job Opening",
			frappe.db.get_value("Application", self.application, "job_opening"),
			"track",
		)
		if not track:
			return

		rubric_name = frappe.db.get_value(
			"Scoring Rubric Template",
			{"track": track, "stage": "Shortlisting", "is_active": 1},
			"name",
		)
		if not rubric_name:
			return

		self.rubric = rubric_name

		if self.criteria:
			return

		rubric = frappe.get_doc("Scoring Rubric Template", rubric_name)
		if rubric.scoring_mode != "Weighted Score":
			return

		for row in rubric.criteria:
			self.append(
				"criteria",
				{"criterion_label": row.criterion_label, "max_score": row.max_score, "score_given": 0},
			)

	def compute_total_score(self):
		self.total_score = sum(row.score_given or 0 for row in self.criteria)
