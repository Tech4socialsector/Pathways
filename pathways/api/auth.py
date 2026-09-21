# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_my_roles():
	"""Roles for the current session user, filtered to Pathways-* roles
	plus System Manager, so the frontend can drive role-aware navigation
	without ever trusting a client-supplied role list.
	"""
	all_roles = frappe.get_roles(frappe.session.user)
	return [r for r in all_roles if r.startswith("Pathways") or r == "System Manager"]


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
