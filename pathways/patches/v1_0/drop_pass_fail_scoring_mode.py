# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Scoring Mode lost its "Pass/Fail Only" option. A rubric without criteria
(Admin shortlisting) still means a shortlist / reject decision with remarks,
so only the stored mode changes."""

import frappe


def execute():
	frappe.db.set_value(
		"Scoring Rubric Template",
		{"scoring_mode": "Pass/Fail Only"},
		"scoring_mode",
		"Weighted Score",
		update_modified=False,
	)
