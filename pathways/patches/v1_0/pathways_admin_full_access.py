# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Pathways Admin gets full access to Pathways.

* The DocType grants (submit / cancel the Post-Interview Green Sheet,
  export the audit logs, manage candidates' drafts) ship in the DocType
  JSON; a DocType whose permissions were customised on the Roles &
  Permissions screen gets them here too, keeping every other change.
* Pathways Settings: Admin reviews appointment orders, and overrides
  application statuses where that is still left to System Manager only.
  Signing appointment orders stays with its signatories."""

import frappe

ADMIN = "Pathways Admin"
GRANTS = {
	"Post-Interview Green Sheet": ("submit", "cancel"),
	"Application Status History": ("export", "report"),
	"Communication Log": ("export", "report"),
	"Application Draft": ("read", "delete", "report"),
}


def execute():
	if not frappe.db.exists("Role", ADMIN):
		return
	for doctype, ptypes in GRANTS.items():
		if not frappe.db.exists("Custom DocPerm", {"parent": doctype}):
			continue  # the shipped permissions apply
		name = frappe.db.get_value("Custom DocPerm", {"parent": doctype, "role": ADMIN, "permlevel": 0, "if_owner": 0}, "name")
		if name:
			frappe.db.set_value("Custom DocPerm", name, {p: 1 for p in ptypes})
		else:
			frappe.get_doc(
				{
					"doctype": "Custom DocPerm", "parent": doctype, "parenttype": "DocType", "parentfield": "permissions",
					"role": ADMIN, "permlevel": 0, **{p: 1 for p in ptypes},
				}
			).insert(ignore_permissions=True)
		frappe.clear_cache(doctype=doctype)

	settings = frappe.get_single("Pathways Settings")
	settings.flags.ignore_mandatory = True
	changed = False
	if ADMIN not in [r.role for r in settings.get("offer_reviewer_roles") or []]:
		settings.append("offer_reviewer_roles", {"role": ADMIN})
		changed = True
	# System Manager may always override; a site that picked another role keeps it.
	if settings.get("status_override_role") in (None, "", "System Manager"):
		settings.status_override_role = ADMIN
		changed = True
	if changed:
		settings.save(ignore_permissions=True)
