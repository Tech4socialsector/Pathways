# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_my_roles():
	"""Roles for the current session user, filtered to Pathways-* roles
	plus System Manager, so the frontend can drive role-aware navigation
	without ever trusting a client-supplied role list.

	"Pathways Candidate" is dropped for System Users: a real candidate
	is always a Website User, so a System User carrying that role only
	means frappe.get_roles() returned every role in the system (as it
	does for Administrator) — surfacing it here would make the frontend
	misclassify an admin/staff account as a candidate.
	"""
	user = frappe.session.user
	all_roles = frappe.get_roles(user)
	roles = [r for r in all_roles if r.startswith("Pathways") or r == "System Manager"]

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
