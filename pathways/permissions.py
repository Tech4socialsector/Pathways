# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Server-side permission scoping for candidate-facing and
committee-facing DocTypes, per the architecture blueprint's role/
permission matrix. Role Permissions alone cannot express "only your
own record" or "only your assigned Job Opening" — that logic lives
here as query conditions (for list views/reports) and has_permission
checks (for direct document access), so it can never be bypassed by
the frontend.
"""

import frappe

PRIVILEGED_ROLES = {
	"Pathways Admin",
	"Pathways Recruiter",
	"Pathways PNCO",
	"System Manager",
}

PATHWAYS_ROLES = {
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
	"Pathways Shortlisting Committee Member",
	"Pathways Selection Committee Member",
	"Pathways Communications",
	"Pathways IT Facilities",
	"Pathways Candidate",
}


def _user_roles():
	return set(frappe.get_roles(frappe.session.user))


def _is_privileged():
	return bool(_user_roles() & PRIVILEGED_ROLES)


def has_app_permission():
	"""Gate for the Pathways tile on the /apps screen (add_to_apps_screen hook).

	Anyone holding a Pathways role may open the app; System Manager is
	included so admins can always reach it to configure the app itself.
	"""
	return bool(_user_roles() & (PATHWAYS_ROLES | {"System Manager"}))


def get_application_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	roles = set(frappe.get_roles(user))
	if roles & PRIVILEGED_ROLES:
		return ""

	conditions = []

	if "Pathways Shortlisting Committee Member" in roles or "Pathways Selection Committee Member" in roles:
		job_openings = set()
		if "Pathways Shortlisting Committee Member" in roles:
			job_openings |= set(
				frappe.get_all(
					"Shortlisting Committee",
					filters=[["Committee Member Row", "member", "=", user]],
					pluck="job_opening",
				)
			)
		if "Pathways Selection Committee Member" in roles:
			job_openings |= set(
				frappe.get_all(
					"Selection Committee",
					filters=[["Committee Member Row", "member", "=", user]],
					pluck="job_opening",
				)
			)
		if job_openings:
			job_opening_list = ", ".join(frappe.db.escape(j) for j in job_openings)
			conditions.append(f"`tabApplication`.job_opening in ({job_opening_list})")
		else:
			conditions.append("1=0")

	if "Pathways Candidate" in roles:
		candidate = frappe.db.get_value("Candidate", {"email": user}, "name")
		if candidate:
			conditions.append(f"`tabApplication`.candidate = {frappe.db.escape(candidate)}")
		else:
			conditions.append("1=0")

	if not conditions:
		return "1=0"

	return " or ".join(conditions)


def has_application_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if roles & PRIVILEGED_ROLES:
		return True

	if "Pathways Candidate" in roles:
		candidate_email = frappe.db.get_value("Candidate", doc.candidate, "email")
		return candidate_email == user

	if "Pathways Shortlisting Committee Member" in roles:
		assigned = frappe.db.exists(
			"Shortlisting Committee",
			[["Committee Member Row", "member", "=", user], ["job_opening", "=", doc.job_opening]],
		)
		if assigned:
			return True

	if "Pathways Selection Committee Member" in roles:
		assigned = frappe.db.exists(
			"Selection Committee",
			[["Committee Member Row", "member", "=", user], ["job_opening", "=", doc.job_opening]],
		)
		if assigned:
			return True

	return False


def get_interview_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	roles = set(frappe.get_roles(user))
	if roles & PRIVILEGED_ROLES:
		return ""

	if "Pathways Candidate" in roles:
		candidate = frappe.db.get_value("Candidate", {"email": user}, "name")
		if not candidate:
			return "1=0"
		application_list = frappe.get_all("Application", filters={"candidate": candidate}, pluck="name")
		if not application_list:
			return "1=0"
		app_list_sql = ", ".join(frappe.db.escape(a) for a in application_list)
		return f"`tabInterview`.application in ({app_list_sql})"

	if "Pathways Selection Committee Member" in roles:
		committees = frappe.get_all(
			"Selection Committee",
			filters=[["Committee Member Row", "member", "=", user]],
			pluck="name",
		)
		if not committees:
			return "1=0"
		committee_list = ", ".join(frappe.db.escape(c) for c in committees)
		return f"`tabInterview`.selection_committee in ({committee_list})"

	return "1=0"


def has_interview_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if roles & PRIVILEGED_ROLES:
		return True

	if "Pathways Candidate" in roles:
		application = frappe.get_doc("Application", doc.application)
		candidate_email = frappe.db.get_value("Candidate", application.candidate, "email")
		return candidate_email == user

	if "Pathways Selection Committee Member" in roles and doc.selection_committee:
		return bool(
			frappe.db.exists(
				"Selection Committee",
				[["Committee Member Row", "member", "=", user], ["name", "=", doc.selection_committee]],
			)
		)

	return False


def _candidate_owns_via_application(doctype, docname, application_fieldname="application"):
	user = frappe.session.user
	application_name = frappe.db.get_value(doctype, docname, application_fieldname)
	if not application_name:
		return False
	candidate = frappe.db.get_value("Application", application_name, "candidate")
	candidate_email = frappe.db.get_value("Candidate", candidate, "email") if candidate else None
	return candidate_email == user


def _candidate_scoped_query_conditions(doctype, table_name, application_fieldname="application"):
	user = frappe.session.user
	candidate = frappe.db.get_value("Candidate", {"email": user}, "name")
	if not candidate:
		return "1=0"
	application_list = frappe.get_all("Application", filters={"candidate": candidate}, pluck="name")
	if not application_list:
		return "1=0"
	app_list_sql = ", ".join(frappe.db.escape(a) for a in application_list)
	return f"`tab{table_name}`.{application_fieldname} in ({app_list_sql})"


def get_document_collection_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	if _is_privileged() or "Pathways PNCO" in frappe.get_roles(user):
		return ""
	if "Pathways Candidate" in frappe.get_roles(user):
		return _candidate_scoped_query_conditions("Document Collection", "Document Collection")
	return "1=0"


def has_document_collection_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if roles & PRIVILEGED_ROLES or "Pathways PNCO" in roles:
		return True
	if "Pathways Candidate" in roles:
		return _candidate_owns_via_application("Document Collection", doc.name)
	return False


def get_offer_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	if _is_privileged() or "Pathways PNCO" in frappe.get_roles(user) or "Pathways Registrar" in frappe.get_roles(user):
		return ""
	if "Pathways Candidate" in frappe.get_roles(user):
		return _candidate_scoped_query_conditions("Offer Appointment Order", "Offer Appointment Order")
	return "1=0"


def has_offer_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if roles & PRIVILEGED_ROLES or "Pathways PNCO" in roles or "Pathways Registrar" in roles:
		return True
	if "Pathways Candidate" in roles:
		return _candidate_owns_via_application("Offer Appointment Order", doc.name)
	return False


def get_joining_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	if _is_privileged() or "Pathways PNCO" in frappe.get_roles(user):
		return ""
	if "Pathways Candidate" in frappe.get_roles(user):
		return _candidate_scoped_query_conditions("Joining", "Joining")
	return "1=0"


def has_joining_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if roles & PRIVILEGED_ROLES or "Pathways PNCO" in roles:
		return True
	if "Pathways Candidate" in roles:
		return _candidate_owns_via_application("Joining", doc.name)
	return False
