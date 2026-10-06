# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Server-side permission scoping for candidate-facing and
committee-facing DocTypes.

What a role may do on a DocType (read/write/create/...) is plain Frappe
Role Permissions, editable by a System Manager from Pathways > Roles &
Permissions — nothing here names a staff role. This module only adds the
row-level rules Role Permissions cannot express:

	Candidate                      only their own records
	Shortlisting/Selection member  only Job Openings whose committee they sit on

Those three roles are behavioural: the code must know which role *means*
"candidate" or "committee member", so they are constants. Every other
role that is granted read on a DocType sees all of its records
(has_full_access) — so granting a new role read from the Roles &
Permissions screen takes effect immediately, with no code change.
"""

import frappe

CANDIDATE_ROLE = "Pathways Candidate"
SHORTLISTING_ROLE = "Pathways Shortlisting Committee Member"
SELECTION_ROLE = "Pathways Selection Committee Member"
SCOPED_ROLES = frozenset({CANDIDATE_ROLE, SHORTLISTING_ROLE, SELECTION_ROLE})

# Seeded into Pathways Settings > Pathways Roles on install; after that the
# list is maintained from the Roles & Permissions screen.
DEFAULT_PATHWAYS_ROLES = (
	"Pathways Admin",
	"Pathways Recruiter",
	"Pathways PNCO",
	"Pathways Director People Culture",
	"Pathways Dean Academics",
	"Pathways Dean Research",
	"Pathways Senior Manager Research",
	"Pathways CFO",
	"Pathways Registrar",
	"Pathways Vice Chancellor",
	SHORTLISTING_ROLE,
	SELECTION_ROLE,
	"Pathways Communications",
	"Pathways IT Facilities",
	CANDIDATE_ROLE,
)


def get_pathways_roles():
	"""Roles that belong to the Pathways app (configurable)."""
	settings = frappe.get_cached_doc("Pathways Settings")
	roles = {row.role for row in settings.get("pathways_roles") or [] if row.role}
	return roles or set(DEFAULT_PATHWAYS_ROLES)


def _roles(user=None):
	return set(frappe.get_roles(user or frappe.session.user))


def has_full_access(doctype, user=None):
	"""True if a non-scoped role of this user is granted read on `doctype`
	(Role Permissions incl. Custom DocPerm, via the cached meta)."""
	roles = _roles(user)
	return any(
		perm.read and not perm.if_owner and not perm.permlevel and perm.role in roles and perm.role not in SCOPED_ROLES
		for perm in frappe.get_meta(doctype).permissions
	)


def has_duty(settings_field, user=None):
	"""Is the user in one of the roles listed in a Pathways Settings
	duty-role table (e.g. document_verifier_roles)?"""
	settings = frappe.get_cached_doc("Pathways Settings")
	duty_roles = {row.role for row in settings.get(settings_field) or [] if row.role}
	return bool(duty_roles & _roles(user))


def has_app_permission():
	"""Gate for the Pathways tile on the /apps screen and the Desk navbar."""
	return bool(_roles() & (get_pathways_roles() | {"System Manager"}))


def extend_bootinfo(bootinfo):
	bootinfo.pathways_has_access = has_app_permission()


# ---------------------------------------------------------------- helpers


def _sql_in(values):
	return ", ".join(frappe.db.escape(v) for v in values)


def _candidate_for(user):
	return frappe.db.get_value("Candidate", {"email": user}, "name")


def _candidate_applications(user):
	candidate = _candidate_for(user)
	if not candidate:
		return []
	return frappe.get_all("Application", filters={"candidate": candidate}, pluck="name")


def _committee_names(committee_doctype, user):
	return frappe.get_all(
		committee_doctype,
		filters=[["Committee Member Row", "member", "=", user]],
		pluck="name",
	)


def _committee_job_openings(user, roles):
	job_openings = set()
	if SHORTLISTING_ROLE in roles:
		job_openings |= set(
			frappe.get_all(
				"Shortlisting Committee",
				filters=[["Committee Member Row", "member", "=", user]],
				pluck="job_opening",
			)
		)
	if SELECTION_ROLE in roles:
		job_openings |= set(
			frappe.get_all(
				"Selection Committee",
				filters=[["Committee Member Row", "member", "=", user]],
				pluck="job_opening",
			)
		)
	return job_openings


def _owns_application(application_name, user):
	if not application_name:
		return False
	candidate = frappe.db.get_value("Application", application_name, "candidate")
	return bool(candidate) and frappe.db.get_value("Candidate", candidate, "email") == user


def _candidate_condition(table, user, fieldname="application"):
	applications = _candidate_applications(user)
	if not applications:
		return "1=0"
	return f"`tab{table}`.{fieldname} in ({_sql_in(applications)})"


# ------------------------------------------------------------- Application


def get_application_permission_query_conditions(user):
	user = user or frappe.session.user
	if has_full_access("Application", user):
		return ""
	roles = _roles(user)

	conditions = []
	if roles & {SHORTLISTING_ROLE, SELECTION_ROLE}:
		job_openings = _committee_job_openings(user, roles)
		conditions.append(f"`tabApplication`.job_opening in ({_sql_in(job_openings)})" if job_openings else "1=0")

	if CANDIDATE_ROLE in roles:
		candidate = _candidate_for(user)
		conditions.append(f"`tabApplication`.candidate = {frappe.db.escape(candidate)}" if candidate else "1=0")

	return " or ".join(f"({c})" for c in conditions) if conditions else "1=0"


def has_application_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if has_full_access("Application", user):
		return True
	roles = _roles(user)

	if CANDIDATE_ROLE in roles and frappe.db.get_value("Candidate", doc.candidate, "email") == user:
		return True

	# Committee members only ever read applications.
	if permission_type not in (None, "read", "print"):
		return False
	if SHORTLISTING_ROLE in roles and frappe.db.exists(
		"Shortlisting Committee",
		[["Committee Member Row", "member", "=", user], ["job_opening", "=", doc.job_opening]],
	):
		return True
	if SELECTION_ROLE in roles and frappe.db.exists(
		"Selection Committee",
		[["Committee Member Row", "member", "=", user], ["job_opening", "=", doc.job_opening]],
	):
		return True

	return False


# --------------------------------------------------------------- Interview


def get_interview_permission_query_conditions(user):
	user = user or frappe.session.user
	if has_full_access("Interview", user):
		return ""
	roles = _roles(user)

	conditions = []
	if CANDIDATE_ROLE in roles:
		conditions.append(_candidate_condition("Interview", user))
	if SELECTION_ROLE in roles:
		committees = _committee_names("Selection Committee", user)
		conditions.append(f"`tabInterview`.selection_committee in ({_sql_in(committees)})" if committees else "1=0")

	return " or ".join(f"({c})" for c in conditions) if conditions else "1=0"


def has_interview_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if has_full_access("Interview", user):
		return True
	roles = _roles(user)

	if CANDIDATE_ROLE in roles and _owns_application(doc.application, user):
		return True
	if SELECTION_ROLE in roles and doc.selection_committee:
		return bool(
			frappe.db.exists(
				"Selection Committee",
				[["Committee Member Row", "member", "=", user], ["name", "=", doc.selection_committee]],
			)
		)
	return False


# ------------------------------------- candidate-owned post-selection docs


def _candidate_scoped_query(doctype, user):
	user = user or frappe.session.user
	if has_full_access(doctype, user):
		return ""
	if CANDIDATE_ROLE in _roles(user):
		return _candidate_condition(doctype, user)
	return "1=0"


def _candidate_scoped_has_permission(doctype, doc, user):
	user = user or frappe.session.user
	if has_full_access(doctype, user):
		return True
	if CANDIDATE_ROLE in _roles(user):
		return _owns_application(doc.application, user)
	return False


def get_document_collection_permission_query_conditions(user):
	return _candidate_scoped_query("Document Collection", user)


def has_document_collection_permission(doc, user=None, permission_type=None):
	return _candidate_scoped_has_permission("Document Collection", doc, user)


def get_offer_permission_query_conditions(user):
	return _candidate_scoped_query("Offer Appointment Order", user)


def has_offer_permission(doc, user=None, permission_type=None):
	return _candidate_scoped_has_permission("Offer Appointment Order", doc, user)


def get_joining_permission_query_conditions(user):
	return _candidate_scoped_query("Joining", user)


def has_joining_permission(doc, user=None, permission_type=None):
	return _candidate_scoped_has_permission("Joining", doc, user)


# ------------------------------------------------------ committee scoring


def get_shortlisting_score_permission_query_conditions(user):
	user = user or frappe.session.user
	if has_full_access("Shortlisting Score", user):
		return ""
	if SHORTLISTING_ROLE in _roles(user):
		committees = _committee_names("Shortlisting Committee", user)
		if committees:
			return f"`tabShortlisting Score`.shortlisting_committee in ({_sql_in(committees)})"
	return "1=0"


def has_shortlisting_score_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if has_full_access("Shortlisting Score", user):
		return True
	if SHORTLISTING_ROLE in _roles(user):
		return bool(
			frappe.db.exists(
				"Shortlisting Committee",
				[["Committee Member Row", "member", "=", user], ["name", "=", doc.shortlisting_committee]],
			)
		)
	return False


def get_interview_assessment_permission_query_conditions(user):
	user = user or frappe.session.user
	if has_full_access("Interview Assessment", user):
		return ""
	if SELECTION_ROLE in _roles(user):
		committees = _committee_names("Selection Committee", user)
		if committees:
			interviews = frappe.get_all("Interview", filters={"selection_committee": ["in", committees]}, pluck="name")
			if interviews:
				return f"`tabInterview Assessment`.interview in ({_sql_in(interviews)})"
	return "1=0"


def has_interview_assessment_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if has_full_access("Interview Assessment", user):
		return True
	if SELECTION_ROLE in _roles(user):
		selection_committee = frappe.db.get_value("Interview", doc.interview, "selection_committee")
		if not selection_committee:
			return False
		return bool(
			frappe.db.exists(
				"Selection Committee",
				[["Committee Member Row", "member", "=", user], ["name", "=", selection_committee]],
			)
		)
	return False
