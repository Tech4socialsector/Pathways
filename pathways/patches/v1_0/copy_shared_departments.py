# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Second half of the Department -> Pathways Department move, for sites
where "Department" was NOT renamed in place (another app such as SLCM
defines it, so its table is shared).

- Copies every Department row into Pathways Department under the same
  name, so existing Job Opening / Employee / Position links stay valid.
  The source table is only read, never changed.
- If Pathways had last written the shared "Department" definition, the
  owning app's definition is reloaded. Otherwise migrate's orphan cleanup
  would drop the DocType record (module Pathways, no controller any more)
  and break that app.
"""

import frappe

from pathways.patches.v1_0.rename_department_doctype import NEW, OLD, other_apps_defining


def execute():
	# Renamed in place before sync (no other app defines Department).
	if not frappe.db.table_exists(OLD):
		return

	copy_rows()
	restore_owner()


def copy_rows():
	columns = set(frappe.db.get_table_columns(OLD))
	rows = frappe.db.sql(f"select * from `tab{OLD}`", as_dict=True)

	copied = []
	for row in rows:
		if frappe.db.exists(NEW, row.name):
			continue

		department_name = row.get("department_name") or row.name
		if frappe.db.exists(NEW, {"department_name": department_name}):
			department_name = row.name

		code = row.get("department_code") or None
		if code and frappe.db.exists(NEW, {"department_code": code}):
			code = None

		head = row.get("head_of_department") or None
		if head and not frappe.db.exists("User", head):
			head = None

		if "is_active" in columns:
			is_active = 1 if row.get("is_active") else 0
		elif "disabled" in columns:
			is_active = 0 if row.get("disabled") else 1
		else:
			is_active = 1

		doc = frappe.get_doc(
			{
				"doctype": NEW,
				"department_name": department_name,
				"department_code": code,
				"head_of_department": head,
				"is_active": is_active,
				"owner": row.get("owner") or "Administrator",
				"creation": row.get("creation"),
				"modified": row.get("modified"),
				"modified_by": row.get("modified_by") or "Administrator",
			}
		)
		doc.name = row.name
		doc.db_insert()
		copied.append(row)

	# Parents only once every row exists, and only if the parent came across.
	for row in copied:
		parent = row.get("parent_department")
		if parent and parent != row.name and frappe.db.exists(NEW, parent):
			frappe.db.set_value(NEW, row.name, "parent_department", parent, update_modified=False)


def restore_owner():
	if frappe.db.get_value("DocType", OLD, "module") != "Pathways":
		return
	owners = other_apps_defining(OLD)
	if owners:
		_app, module = owners[0]
		frappe.reload_doc(frappe.scrub(module), "doctype", frappe.scrub(OLD), force=True)
