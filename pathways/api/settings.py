# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe

from pathways.permissions import get_pathways_roles

# Plain fields editable from the in-app Settings dialog. Role tables
# (Pathways Roles, duty roles) are managed from Roles & Permissions / Desk.
APPEARANCE_FIELDS = ("app_name", "app_logo", "brand_color", "body_font", "heading_font")

EDITABLE_FIELDS = (
	*APPEARANCE_FIELDS,
	"default_sender_email",
	"recruitment_contact_email",
	"acceptance_deadline_days",
	"interview_login_buffer_minutes",
	"default_shortlisting_ratio",
	"min_shortlisting_committee_size",
	"max_shortlisting_committee_size",
	"min_selection_committee_size",
	"max_selection_committee_size",
	"default_general_conditions",
	"approval_override_role",
	"allow_same_approver_multiple_steps",
	"status_override_role",
	"application_max_file_size_mb",
	"application_allowed_formats",
	"application_declaration",
	"application_instructions",
)


@frappe.whitelist()
def get_settings():
	"""Pathways Settings values for the in-app settings panel.

	frappe.get_single() does NOT enforce permissions on read — the explicit
	check below restricts this to roles with read on Pathways Settings.
	"""
	doc = frappe.get_single("Pathways Settings")
	doc.check_permission("read")
	out = {field: doc.get(field) for field in EDITABLE_FIELDS}
	out["role_options"] = sorted(get_pathways_roles() | {"System Manager"})
	out["document_verifier_roles"] = [row.role for row in doc.document_verifier_roles]
	out["corrigendum_signer_roles"] = [row.role for row in doc.corrigendum_signer_roles]
	return out


@frappe.whitelist(methods=["POST"])
def update_settings(data):
	"""Updates Pathways Settings. save() enforces write permission."""
	if isinstance(data, str):
		data = frappe.parse_json(data)

	doc = frappe.get_single("Pathways Settings")
	doc.update({field: data[field] for field in EDITABLE_FIELDS if field in data})
	for table in ("document_verifier_roles", "corrigendum_signer_roles"):
		if table in data:
			doc.set(table, [{"role": role} for role in data[table] or [] if role])
	doc.save()
	return get_settings()


@frappe.whitelist(allow_guest=True)
def get_appearance():
	"""Branding only (name, logo, colour, fonts) — public, so the candidate
	portal and login page are themed too. Nothing sensitive is returned."""
	doc = frappe.get_cached_doc("Pathways Settings")
	return {field: doc.get(field) for field in APPEARANCE_FIELDS}
