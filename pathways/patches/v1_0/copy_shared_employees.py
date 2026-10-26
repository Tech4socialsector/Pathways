# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Second half of the Employee -> Pathways Employee move, for sites where
"Employee" was NOT renamed in place (another app such as ERPNext defines
it, so its table is shared).

- Copies the Employee rows Pathways created (they carry a Source
  Application) into Pathways Employee under the same name, so
  Joining.employee links stay valid. ERPNext's own employees have no
  Source Application and stay where they are. The source table is only
  read, never changed.
- If Pathways had last written the shared "Employee" definition, the owning
  app's definition is reloaded. Otherwise migrate's orphan cleanup would
  drop the DocType record (module Pathways, no controller any more) and
  break that app.
"""

import frappe

from pathways.patches.v1_0.rename_department_doctype import other_apps_defining
from pathways.patches.v1_0.rename_employee_doctype import NEW, OLD

STATUSES = ("Active", "Inactive")
EMPLOYMENT_TYPES = ("Permanent", "Consultant", "Grant-funded", "Contract")


def execute():
	# Renamed in place before sync (no other app defines Employee).
	if not frappe.db.table_exists(OLD):
		return

	copy_rows()
	restore_owner()


def copy_rows():
	if not frappe.db.has_column(OLD, "source_application"):
		return

	rows = frappe.db.sql(
		f"select * from `tab{OLD}` where ifnull(source_application, '') != ''", as_dict=True
	)
	for row in rows:
		if frappe.db.exists(NEW, row.name):
			continue
		if not frappe.db.exists("Application", row.source_application):
			continue

		doc = frappe.get_doc(
			{
				"doctype": NEW,
				"naming_series": row.get("naming_series") or "PWY-EMP-.YYYY.-",
				"employee_name": row.get("employee_name"),
				"designation": valid_link("Pathways Designation", row.get("designation")),
				"department": valid_link("Pathways Department", row.get("department")),
				"date_of_joining": row.get("date_of_joining"),
				"employment_type": row.get("employment_type") if row.get("employment_type") in EMPLOYMENT_TYPES else None,
				"status": row.get("status") if row.get("status") in STATUSES else "Active",
				"source_application": row.source_application,
				"user": valid_link("User", row.get("user")),
				"owner": row.get("owner") or "Administrator",
				"creation": row.get("creation"),
				"modified": row.get("modified"),
				"modified_by": row.get("modified_by") or "Administrator",
			}
		)
		doc.name = row.name
		doc.db_insert()


def valid_link(doctype, value):
	return value if value and frappe.db.exists(doctype, value) else None


def restore_owner():
	if frappe.db.get_value("DocType", OLD, "module") != "Pathways":
		return
	owners = other_apps_defining(OLD)
	if owners:
		_app, module = owners[0]
		frappe.reload_doc(frappe.scrub(module), "doctype", frappe.scrub(OLD), force=True)
