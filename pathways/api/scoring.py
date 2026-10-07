# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_application_for_review(application):
	"""Full application detail for a shortlisting/selection committee
	member — candidate profile, CV/SOP, qualifications, and any score
	already submitted. Deliberately separate from
	pathways.api.application.get_application_status, which is the
	candidate-facing view and excludes exactly this data.

	frappe.get_doc() does not auto-check permissions on read (unlike
	doc.save() for writes) — the explicit check below is what actually
	restricts this to a privileged role or a committee member assigned
	to this application's job opening, via has_application_permission
	in permissions.py.
	"""
	app = frappe.get_doc("Application", application)
	app.check_permission("read")

	candidate = frappe.get_doc("Candidate", app.candidate)

	shortlisting_committee = frappe.db.get_value(
		"Shortlisting Committee", {"job_opening": app.job_opening}, "name"
	)
	existing_score = None
	if shortlisting_committee:
		existing_score_name = frappe.db.exists(
			"Shortlisting Score", {"application": application, "shortlisting_committee": shortlisting_committee}
		)
		if existing_score_name:
			score_doc = frappe.get_doc("Shortlisting Score", existing_score_name)
			existing_score = {
				"is_shortlisted": score_doc.is_shortlisted,
				"remarks": score_doc.remarks,
				"criteria": [
					{
						"criterion_label": row.criterion_label,
						"max_score": row.max_score,
						"score_given": row.score_given,
					}
					for row in score_doc.criteria
				],
			}

	return {
		"name": app.name,
		"application_id": app.application_id,
		"job_opening": app.job_opening,
		"track": app.track,
		"status": app.status,
		"shortlisting_committee": shortlisting_committee,
		# Lets the score panel offer to set up the committee in place.
		"can_create_committee": not shortlisting_committee and bool(frappe.has_permission("Shortlisting Committee", "create")),
		"existing_shortlisting_score": existing_score,
		"candidate": {
			"full_name": candidate.full_name,
			"email": candidate.email,
			"gender": candidate.gender,
			"category": candidate.category,
		},
		"current_salary": app.current_salary,
		"expected_salary": app.expected_salary,
		"earliest_doj": app.earliest_doj,
		"resume_attachment": app.resume_attachment,
		"sop_attachment": app.sop_attachment,
		"qualifications": [
			{
				"degree_level": row.degree_level,
				"degree_name": row.degree_name,
				"institution": row.institution or row.other_institution,
				"year_of_graduation": row.year_of_graduation,
				"percentage_or_cgpa": row.percentage_or_cgpa,
				"specialization": row.specialization,
			}
			for row in app.qualifications
		],
		"employment_history": [
			{
				"designation": row.designation,
				"employer_name": row.employer_name,
				"from_date": row.from_date,
				"to_date": row.to_date,
			}
			for row in app.employment_history
		],
		"publications": [
			{"title": row.title, "journal_name": row.journal_name, "pdf_attachment": row.pdf_attachment}
			for row in app.publications
		],
	}


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

	job_opening = frappe.db.get_value("Application", application, "job_opening")
	if not shortlisting_committee:
		shortlisting_committee = frappe.db.get_value("Shortlisting Committee", {"job_opening": job_opening}, "name")
	if not shortlisting_committee:
		frappe.throw(
			_(
				"No Shortlisting Committee has been set up for Job Opening {0}. "
				"Create one (with its members) before recording shortlisting scores."
			).format(job_opening),
			title=_("Shortlisting Committee Missing"),
		)

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

	# check_permission reads shortlisting_committee off the doc, so it only
	# works once that field is set above — this is what actually restricts
	# submission to a member of THIS job opening's committee (has_permission
	# hook in permissions.py), not just anyone holding the committee role.
	score.check_permission("write" if existing else "create")

	if existing:
		score.save(ignore_permissions=True)
	else:
		score.insert(ignore_permissions=True)

	status = apply_shortlisting_decision(score)
	frappe.db.commit()
	return {"name": score.name, "status": status}


# Statuses a shortlisting decision may move an application out of: once a
# candidate is past shortlisting (interview, offer...), re-scoring never
# pulls them back.
SHORTLISTING_STAGE = ("Submitted", "Under Review", "Shortlisted", "Not Selected")


def apply_shortlisting_decision(score):
	"""The committee's decision sets the application's status:
	Shortlist -> Shortlisted, Reject -> Not Selected. Returns the status."""
	app = frappe.get_doc("Application", score.application)
	decision = "Shortlisted" if frappe.utils.cint(score.is_shortlisted) else "Not Selected"
	if app.status not in SHORTLISTING_STAGE or app.status == decision:
		return app.status

	previous = app.status
	app.status = decision
	# The committee member deciding may not have write access to the
	# Application itself; the decision is theirs to make.
	app.save(ignore_permissions=True)
	app.add_comment(
		"Info",
		_("Shortlisting decision by {0}: {1} (score {2}). Status changed from {3} to {4}.").format(
			frappe.utils.get_fullname(frappe.session.user),
			_("Shortlisted") if decision == "Shortlisted" else _("Rejected"),
			frappe.format(score.get("total_score")),
			previous,
			decision,
		),
	)
	return app.status


@frappe.whitelist()
def submit_interview_assessment(interview, criteria, recommendation=None):
	"""panelist is always the calling user, never a client-supplied value
	— otherwise one panelist could submit an assessment attributed to
	another.
	"""
	if isinstance(criteria, str):
		criteria = frappe.parse_json(criteria)

	panelist = frappe.session.user
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

	# See submit_shortlisting_score — check_permission restricts this to a
	# member of the interview's own Selection Committee, not just anyone
	# holding the committee role.
	assessment.check_permission("write" if existing else "create")

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


def _committee_size():
	settings = frappe.get_cached_doc("Pathways Settings")
	return settings.min_shortlisting_committee_size or 2, settings.max_shortlisting_committee_size or 3


@frappe.whitelist()
def get_committee_options():
	"""Staff who can sit on a shortlisting committee, and the size limits —
	for the "Set up committee" dialog on the application page."""
	if not frappe.has_permission("Shortlisting Committee", "create"):
		frappe.throw(_("You cannot set up shortlisting committees."), frappe.PermissionError)
	minimum, maximum = _committee_size()
	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Guest"]]},
		fields=["name", "full_name"],
		order_by="full_name asc",
	)
	return {"min": minimum, "max": maximum, "users": users}


@frappe.whitelist(methods=["POST"])
def create_shortlisting_committee(job_opening, members, office_order_reference=None):
	"""Create the job's Shortlisting Committee. insert() enforces create
	permission and the committee-size rule."""
	if isinstance(members, str):
		members = frappe.parse_json(members)
	existing = frappe.db.get_value("Shortlisting Committee", {"job_opening": job_opening}, "name")
	if existing:
		frappe.throw(_("Job Opening {0} already has a Shortlisting Committee ({1}).").format(job_opening, existing))
	doc = frappe.get_doc(
		{
			"doctype": "Shortlisting Committee",
			"job_opening": job_opening,
			"office_order_reference": office_order_reference,
			"members": [{"member": user} for user in dict.fromkeys(members or [])],
		}
	).insert()
	return doc.name
