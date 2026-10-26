# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Pathways' "Department" DocType becomes "Pathways Department" so it no
longer clashes with the SLCM app's own "Department" (two apps cannot own
one DocType name — whichever migrates last overwrites the other).

pre_model_sync: on sites where no other app defines "Department", rename
the DocType in place. frappe.rename_doc moves the table, Link options,
permissions, Custom Fields/Property Setters, User Permissions and version
history, and record names stay the same, so every existing link value
(Job Opening.department, Employee.department, ...) stays valid.

Where another app does define "Department", its table is shared and must
stay with that app — copy_shared_departments (post_model_sync) handles it.
"""

import os

import frappe

OLD = "Department"
NEW = "Pathways Department"


def other_apps_defining(doctype):
	"""[(app, module)] of installed apps other than Pathways that ship a
	standard DocType with this name."""
	folder = frappe.scrub(doctype)
	found = []
	for app in frappe.get_installed_apps():
		if app == "pathways":
			continue
		for module in frappe.get_module_list(app):
			path = frappe.get_app_path(app, frappe.scrub(module), "doctype", folder, f"{folder}.json")
			if os.path.exists(path):
				found.append((app, module))
	return found


def execute():
	if frappe.db.exists("DocType", NEW) or not frappe.db.exists("DocType", OLD):
		return
	if frappe.db.get_value("DocType", OLD, "module") != "Pathways":
		return
	if other_apps_defining(OLD):
		return

	frappe.rename_doc("DocType", OLD, NEW, force=True, show_alert=False)
	move_list_view_settings()


def move_list_view_settings(old=OLD, new=NEW):
	"""rename_doc leaves users' saved list settings (columns, filters)
	under the old name; carry them over unless the user already has some."""
	frappe.db.sql(
		"""update `__UserSettings` old_s
		left join `__UserSettings` new_s on new_s.user = old_s.user and new_s.doctype = %(new)s
		set old_s.doctype = %(new)s
		where old_s.doctype = %(old)s and new_s.user is null""",
		{"old": old, "new": new},
	)
