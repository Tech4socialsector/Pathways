# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Fill the guidance text of the Faculty shortlisting criteria, which the
seed left empty (shortlisting_rubrics_from_sheets looked for an older
rubric name). Only empty guidance is filled; text staff edited stays."""

import frappe

from pathways.master_data import FACULTY_SHORTLISTING_GUIDANCE


def execute():
	for rubric in frappe.get_all("Scoring Rubric Template", {"track": "Faculty", "stage": "Shortlisting"}, pluck="name"):
		for row in frappe.get_all(
			"Scoring Criterion Row",
			{"parent": rubric, "parenttype": "Scoring Rubric Template"},
			["name", "criterion_label", "guidance_text"],
		):
			guidance = FACULTY_SHORTLISTING_GUIDANCE.get(row.criterion_label)
			if guidance and not (row.guidance_text or "").strip():
				frappe.db.set_value("Scoring Criterion Row", row.name, "guidance_text", guidance, update_modified=False)
