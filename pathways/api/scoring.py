# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_rubric_for_job_opening(job_opening, stage):
	track = frappe.db.get_value("Job Opening", job_opening, "track")
	if not track:
		return None

	rubric_name = frappe.db.get_value(
		"Scoring Rubric Template", {"track": track, "stage": stage, "is_active": 1}, "name"
	)
	if not rubric_name:
		return None

	rubric = frappe.get_doc("Scoring Rubric Template", rubric_name)
	return {
		"name": rubric.name,
		"scoring_mode": rubric.scoring_mode,
		"pass_threshold_percent": rubric.pass_threshold_percent,
		"max_total_score": rubric.max_total_score,
		"criteria": [
			{"criterion_label": row.criterion_label, "max_score": row.max_score, "guidance_text": row.guidance_text}
			for row in rubric.criteria
		],
	}


@frappe.whitelist()
def submit_shortlisting_score(application, shortlisting_committee, is_shortlisted, remarks, criteria=None):
	if isinstance(criteria, str):
		criteria = frappe.parse_json(criteria)

	existing = frappe.db.exists("Shortlisting Score", {"application": application})
	score = frappe.get_doc("Shortlisting Score", existing) if existing else frappe.new_doc("Shortlisting Score")

	score.application = application
	score.shortlisting_committee = shortlisting_committee
	score.is_shortlisted = is_shortlisted
	score.remarks = remarks

	if criteria:
		score.criteria = []
		for row in criteria:
			score.append(
				"criteria",
				{
					"criterion_label": row.get("criterion_label"),
					"max_score": row.get("max_score"),
					"score_given": row.get("score_given"),
				},
			)

	if existing:
		score.save(ignore_permissions=True)
	else:
		score.insert(ignore_permissions=True)

	frappe.db.commit()
	return score.name


@frappe.whitelist()
def submit_interview_assessment(interview, panelist, criteria, recommendation=None):
	if isinstance(criteria, str):
		criteria = frappe.parse_json(criteria)

	existing = frappe.db.exists("Interview Assessment", {"interview": interview, "panelist": panelist})
	assessment = (
		frappe.get_doc("Interview Assessment", existing) if existing else frappe.new_doc("Interview Assessment")
	)

	assessment.interview = interview
	assessment.panelist = panelist
	assessment.recommendation = recommendation
	assessment.panelist_signature_confirmed = 1

	assessment.criteria = []
	for row in criteria:
		assessment.append(
			"criteria",
			{
				"criterion_label": row.get("criterion_label"),
				"max_score": row.get("max_score"),
				"score_given": row.get("score_given"),
			},
		)

	if existing:
		assessment.save(ignore_permissions=True)
	else:
		assessment.insert(ignore_permissions=True)

	frappe.db.commit()
	return assessment.name


@frappe.whitelist()
def consolidate_scores(interview):
	"""Replaces the manual 'Consolidated Score Sheet' Excel step —
	aggregates every panelist's Interview Assessment for a given
	Interview into one summary, parameterized for any rubric size.
	"""
	assessments = frappe.get_all(
		"Interview Assessment",
		filters={"interview": interview},
		fields=["name", "panelist", "total_score"],
	)
	if not assessments:
		return {"panelists": [], "average": 0, "total_of_all": 0}

	total = sum(a.total_score or 0 for a in assessments)
	average = total / len(assessments)

	return {
		"panelists": assessments,
		"total_of_all": total,
		"average": round(average, 2),
		"panelist_count": len(assessments),
	}
