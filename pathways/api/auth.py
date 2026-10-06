# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.rate_limiter import rate_limit

from pathways.permissions import get_pathways_roles


@frappe.whitelist()
def get_my_roles():
	"""Roles for the current session user, filtered to the configured
	Pathways roles plus System Manager, so the frontend can drive role-aware navigation
	without ever trusting a client-supplied role list.

	"Pathways Candidate" is dropped for System Users: a real candidate
	is always a Website User, so a System User carrying that role only
	means frappe.get_roles() returned every role in the system (as it
	does for Administrator) — surfacing it here would make the frontend
	misclassify an admin/staff account as a candidate.
	"""
	user = frappe.session.user
	pathways_roles = get_pathways_roles()
	roles = [r for r in frappe.get_roles(user) if r in pathways_roles or r == "System Manager"]

	if frappe.db.get_value("User", user, "user_type") == "System User":
		roles = [r for r in roles if r != "Pathways Candidate"]

	return roles


@frappe.whitelist()
def get_my_profile():
	"""Minimal profile info for the session user — used by the frontend
	shell to render name/avatar without a separate User doctype fetch
	from the client (which could over-expose fields).
	"""
	user = frappe.session.user
	if user == "Guest":
		return None

	user_doc = frappe.db.get_value(
		"User", user, ["full_name", "user_image", "email"], as_dict=True
	)
	candidate = frappe.db.get_value("Candidate", {"email": user}, "name")
	return {
		"email": user,
		"full_name": user_doc.full_name if user_doc else user,
		"user_image": user_doc.user_image if user_doc else None,
		"candidate": candidate,
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=5, seconds=60 * 60)
def register_candidate(email, full_name, redirect_to=None):
	"""Candidate self-registration for the careers portal, independent of
	the site-wide "Disable Signup" switch (which stays on for Desk).

	Creates a Website User with the Candidate role and emails a
	set-password link — clicking it is what proves the candidate owns the
	address, so nobody can apply in someone else's name. The response is
	identical whether or not the email is already registered (an existing
	account just gets a password-reset email), so it cannot be used to
	discover who has an account.
	"""
	from frappe.utils import escape_html, random_string, validate_email_address

	from pathways.permissions import CANDIDATE_ROLE

	email = (email or "").strip().lower()
	full_name = (full_name or "").strip()
	if not validate_email_address(email):
		frappe.throw(frappe._("Enter a valid email address."))
	if not full_name:
		frappe.throw(frappe._("Enter your full name."))

	message = frappe._(
		"Check your inbox at {0} for a link to set your password, then log in to apply."
	).format(email)

	existing = frappe.db.get_value("User", email, ["name", "enabled"], as_dict=True)
	if existing:
		if existing.enabled and existing.name not in ("Administrator", "Guest"):
			frappe.get_doc("User", existing.name)._reset_password(send_email=True)
		return message

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": escape_html(full_name),
			"enabled": 1,
			"new_password": random_string(16),
			"user_type": "Website User",
			"send_welcome_email": 1,
		}
	)
	user.flags.ignore_permissions = True
	user.flags.ignore_password_policy = True
	user.insert()
	user.add_roles(CANDIDATE_ROLE)
	if redirect_to:
		from frappe.www.login import sanitize_redirect

		frappe.cache.hset("redirect_after_login", user.name, sanitize_redirect(redirect_to))
	return message
