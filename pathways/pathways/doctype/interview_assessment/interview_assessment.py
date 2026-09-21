# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InterviewAssessment(Document):
	def validate(self):
		self.validate_one_per_panelist()
		self.populate_rubric_criteria()
		self.compute_total_score()

	def validate_one_per_panelist(self):
		existing = frappe.db.exists(
			"Interview Assessment",
			{
				"interview": self.interview,
				"panelist": self.panelist,
				"name": ["!=", self.name or ""],
			},
		)
		if existing:
			frappe.throw(
				f"An Interview Assessment from this panelist for this Interview already exists ({existing})."
			)

	def populate_rubric_criteria(self):
		if not self.interview or self.criteria:
			return

		application = frappe.db.get_value("Interview", self.interview, "application")
		if not application:
			return

		track = frappe.db.get_value(
			"Job Opening", frappe.db.get_value("Application", application, "job_opening"), "track"
		)
		if not track:
			return

		rubric_name = frappe.db.get_value(
			"Scoring Rubric Template",
			{"track": track, "stage": "Final Interview", "is_active": 1},
			"name",
		)
		if not rubric_name:
			return

		rubric = frappe.get_doc("Scoring Rubric Template", rubric_name)
		for row in rubric.criteria:
			self.append(
				"criteria",
				{"criterion_label": row.criterion_label, "max_score": row.max_score, "score_given": 0},
			)

	def compute_total_score(self):
		self.total_score = sum(row.score_given or 0 for row in self.criteria)
