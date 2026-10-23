# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""The Pathways Tagged Colleague role (workflow step 7): created, listed in
Pathways Settings > Pathways Roles so tagged colleagues see the app, and
existing jobs get their department folder."""

import frappe

from pathways.permissions import TAGGED_ROLE


def execute():
	ensure_tagged_role()
	from pathways.utils.folders import ensure_job_folder

	for name in frappe.get_all("Job Opening", filters={"files_folder": ["is", "not set"]}, pluck="name"):
		try:
			ensure_job_folder(name)
		except Exception:
			frappe.log_error(title=f"Pathways: could not create the folder for {name}")


def ensure_tagged_role():
	if not frappe.db.exists("Role", TAGGED_ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": TAGGED_ROLE, "desk_access": 1}).insert(ignore_permissions=True)
	settings = frappe.get_single("Pathways Settings")
	if settings.get("pathways_roles") and TAGGED_ROLE not in [r.role for r in settings.pathways_roles]:
		settings.append("pathways_roles", {"role": TAGGED_ROLE})
		settings.flags.ignore_permissions = True
		settings.flags.ignore_mandatory = True
		settings.save()
