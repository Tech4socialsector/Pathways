# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Second half of the Designation -> Pathways Designation move, for sites
where "Designation" was NOT renamed in place (another app such as ERPNext
defines it, so its table is shared).

- Copies the Designation rows Pathways uses into Pathways Designation under
  the same name, so existing Position / Job Opening / Offer / Joining links
  stay valid: rows carrying recruitment details (a track) and rows any
  Pathways record links to. The other app's own rows (ERPNext's setup
  defaults such as "Accountant") have no track and stay out of the
  recruitment masters. The source table is only read, never changed.
- If Pathways had last written the shared "Designation" definition, the
  owning app's definition is reloaded. Otherwise migrate's orphan cleanup
  would drop the DocType record (module Pathways, no controller any more)
  and break that app.
"""

import frappe

from pathways.patches.v1_0.rename_designation_doctype import NEW, OLD
from pathways.patches.v1_0.rename_department_doctype import other_apps_defining


def execute():
	# Renamed in place before sync (no other app defines Designation).
	if not frappe.db.table_exists(OLD):
		return

	copy_rows()
	restore_owner()


def copy_rows():
	columns = set(frappe.db.get_table_columns(OLD))
	linked = linked_designations()
	rows = frappe.db.sql(f"select * from `tab{OLD}`", as_dict=True)

	for row in rows:
		if not (row.get("track") or row.name in linked):
			continue
		if frappe.db.exists(NEW, row.name):
			continue

		designation_name = row.get("designation_name") or row.name
		if frappe.db.exists(NEW, {"designation_name": designation_name}):
			designation_name = row.name

		code = row.get("designation_code") or None
		if code and frappe.db.exists(NEW, {"designation_code": code}):
			code = None

		track = row.get("track") or None
		if track and not frappe.db.exists("Recruitment Track", track):
			track = None

		doc = frappe.get_doc(
			{
				"doctype": NEW,
				"designation_name": designation_name,
				"designation_code": code,
				"track": track,
				"employment_type": row.get("employment_type") or None,
				"pay_level_range": row.get("pay_level_range") or None,
				"superannuation_age": row.get("superannuation_age") or 0,
				"is_active": (1 if row.get("is_active") else 0) if "is_active" in columns else 1,
				"owner": row.get("owner") or "Administrator",
				"creation": row.get("creation"),
				"modified": row.get("modified"),
				"modified_by": row.get("modified_by") or "Administrator",
			}
		)
		doc.name = row.name
		doc.db_insert()


def linked_designations():
	"""Every value a Pathways Link field (now pointing at the new DocType)
	holds, so none of those links is left dangling."""
	fields = frappe.get_all("DocField", {"fieldtype": "Link", "options": NEW}, ["parent", "fieldname"])
	fields += frappe.get_all("Custom Field", {"fieldtype": "Link", "options": NEW}, ["dt as parent", "fieldname"])

	names = set()
	for field in fields:
		if not frappe.db.table_exists(field.parent) or not frappe.db.has_column(field.parent, field.fieldname):
			continue
		names.update(
			frappe.db.sql_list(
				f"select distinct `{field.fieldname}` from `tab{field.parent}` where ifnull(`{field.fieldname}`, '') != ''"
			)
		)
	return names


def restore_owner():
	if frappe.db.get_value("DocType", OLD, "module") != "Pathways":
		return
	owners = other_apps_defining(OLD)
	if owners:
		_app, module = owners[0]
		frappe.reload_doc(frappe.scrub(module), "doctype", frappe.scrub(OLD), force=True)
