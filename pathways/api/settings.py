# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.file_manager import get_max_file_size

from pathways.permissions import SCOPED_ROLES, get_pathways_roles

# Plain fields editable from the in-app Settings dialog. Pathways Roles are
# managed from Roles & Permissions; the reply-to address
# (recruitment_contact_email) from Email Setup.
APPEARANCE_FIELDS = ("app_name", "app_logo", "brand_color", "body_font", "heading_font")

EDITABLE_FIELDS = (
	*APPEARANCE_FIELDS,
	"acceptance_deadline_days",
	"default_shortlisting_ratio",
	"min_shortlisting_committee_size",
	"max_shortlisting_committee_size",
	"min_selection_committee_size",
	"max_selection_committee_size",
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
	out["document_verifier_roles"] = [row.role for row in doc.document_verifier_roles]
	out["corrigendum_signer_roles"] = [row.role for row in doc.corrigendum_signer_roles]
	# Overrides and duties are staff powers, so candidate and committee-member
	# roles are not offered. Roles already chosen stay listed so they show.
	chosen = {
		doc.approval_override_role,
		doc.status_override_role,
		*out["document_verifier_roles"],
		*out["corrigendum_signer_roles"],
	}
	out["role_options"] = sorted(((get_pathways_roles() - SCOPED_ROLES) | {"System Manager"} | chosen) - {None, ""})
	out["max_upload_mb"] = get_max_file_size() / (1024 * 1024)
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
