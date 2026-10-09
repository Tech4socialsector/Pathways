# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class InterviewAssessment(Document):
	def validate(self):
		self.validate_one_per_panelist()
		self.set_interview_details()
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

	def set_interview_details(self):
		"""Who and which job, so the list in Desk reads without opening the Interview."""
		iv = frappe.db.get_value("Interview", self.interview, ["application", "candidate_name", "job_title"], as_dict=True)
		if iv:
			self.application, self.candidate_name, self.job_title = iv.application, iv.candidate_name, iv.job_title

	def populate_rubric_criteria(self):
		if not self.interview or self.criteria:
			return
		rubric = interview_rubric(self.interview)
		if not rubric:
			return
		for row in rubric.criteria:
			self.append(
				"criteria",
				{"criterion_label": row.criterion_label, "max_score": row.max_score, "score_given": 0},
			)

	def compute_total_score(self):
		for row in self.criteria:
			if flt(row.score_given) < 0 or flt(row.score_given) > flt(row.max_score):
				frappe.throw(f"{row.criterion_label}: the score must be between 0 and {flt(row.max_score):g}.")
		self.total_score = sum(flt(row.score_given) for row in self.criteria)
		self.max_score = sum(flt(row.max_score) for row in self.criteria)
		self.score_percent = round(self.total_score * 100 / self.max_score, 2) if self.max_score else 0


def interview_rubric(interview):
	"""The active Final Interview rubric of the interview's job track."""
	application = frappe.db.get_value("Interview", interview, "application")
	job_opening = frappe.db.get_value("Application", application, "job_opening") if application else None
	track = frappe.db.get_value("Job Opening", job_opening, "track") if job_opening else None
	if not track:
		return None
	name = frappe.db.get_value("Scoring Rubric Template", {"track": track, "stage": "Final Interview", "is_active": 1}, "name")
	return frappe.get_doc("Scoring Rubric Template", name) if name else None
