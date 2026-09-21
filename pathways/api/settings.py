# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_settings():
	"""Pathways Settings values for the in-app settings panel.

	Unlike doc.save(), frappe.get_single()/get_doc() do NOT enforce
	permissions on read by default (check_permission is opt-in) — the
	explicit check below is what actually restricts this to System
	Manager / Pathways Admin, per the doctype's own permission rows.
	"""
	doc = frappe.get_single("Pathways Settings")
	doc.check_permission("read")
	return {
		"default_sender_email": doc.default_sender_email,
		"recruitment_contact_email": doc.recruitment_contact_email,
		"acceptance_deadline_days": doc.acceptance_deadline_days,
		"interview_login_buffer_minutes": doc.interview_login_buffer_minutes,
		"default_shortlisting_ratio": doc.default_shortlisting_ratio,
		"min_shortlisting_committee_size": doc.min_shortlisting_committee_size,
		"max_shortlisting_committee_size": doc.max_shortlisting_committee_size,
		"min_selection_committee_size": doc.min_selection_committee_size,
		"max_selection_committee_size": doc.max_selection_committee_size,
		"default_general_conditions": doc.default_general_conditions,
	}


@frappe.whitelist()
def update_settings(data):
	"""Updates Pathways Settings. save() enforces write permission on its
	own — only System Manager / Pathways Admin hold write on this single
	doctype.
	"""
	if isinstance(data, str):
		data = frappe.parse_json(data)

	doc = frappe.get_single("Pathways Settings")
	doc.update(data)
	doc.save()
	return get_settings()
