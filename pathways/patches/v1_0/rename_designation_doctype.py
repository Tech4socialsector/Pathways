# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Pathways' "Designation" DocType becomes "Pathways Designation" so it no
longer clashes with ERPNext's own "Designation" (two apps cannot own one
DocType name — whichever migrates last overwrites the other).

pre_model_sync: on sites where no other app defines "Designation", rename
the DocType in place. frappe.rename_doc moves the table, Link options,
permissions, Custom Fields/Property Setters, User Permissions and version
history, and record names stay the same, so every existing link value
(Position.designation, Job Opening.designation, ...) stays valid.

Where another app does define "Designation", its table is shared and must
stay with that app — copy_shared_designations (post_model_sync) handles it.
"""

import frappe

from pathways.patches.v1_0.rename_department_doctype import move_list_view_settings, other_apps_defining

OLD = "Designation"
NEW = "Pathways Designation"


def execute():
	if frappe.db.exists("DocType", NEW) or not frappe.db.exists("DocType", OLD):
		return
	if frappe.db.get_value("DocType", OLD, "module") != "Pathways":
		return
	if other_apps_defining(OLD):
		return

	frappe.rename_doc("DocType", OLD, NEW, force=True, show_alert=False)
	move_list_view_settings(OLD, NEW)
