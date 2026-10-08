# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Master Setup landing page data. The registry lives in
pathways.utils.master_setup; records themselves are maintained through
the framework's standard list/form views, which enforce permissions,
validation and version history on their own.
"""

from urllib.parse import quote

import frappe
from frappe import _

from pathways.utils.master_setup import MASTER_SETUP, can_manage, get_active_field, get_master


@frappe.whitelist()
def has_access():
	"""Cheap check for the sidebar — no record counts."""
	return any(can_manage(m["doctype"]) for category in MASTER_SETUP for m in category["masters"])


@frappe.whitelist()
def get_master_setup():
	"""Categories with only the masters the session user may manage.
	Raises PermissionError (HTTP 403) when there are none, so direct URL
	access by an unauthorised user gets a proper permission response."""
	categories = []
	for category in MASTER_SETUP:
		masters = [_describe(m) for m in category["masters"] if can_manage(m["doctype"])]
		if masters:
			categories.append({"key": category["key"], "label": _(category["label"]), "masters": masters})

	if not categories:
		frappe.throw(_("You do not have permission to access Master Setup."), frappe.PermissionError)

	return categories


def _describe(master):
	doctype = master["doctype"]
	meta = frappe.get_meta(doctype)
	active_field, active_value = get_active_field(meta)
	route = "/desk/" + doctype.lower().replace(" ", "-")

	return {
		"doctype": doctype,
		"label": _(master.get("label") or doctype),
		"singular": _(master.get("singular") or doctype),
		"description": _(master.get("description") or ""),
		"icon": master.get("icon") or "database",
		"keywords": master.get("keywords") or [],
		"route": route,
		"new_route": route + "/new",
		"can_create": bool(frappe.has_permission(doctype, "create")),
		"total": frappe.db.count(doctype),
		"inactive": frappe.db.count(doctype, {active_field: ["!=", active_value]}) if active_field else None,
		"last_updated": (frappe.get_all(doctype, fields=["modified"], order_by="modified desc", limit=1) or [{}])[0].get("modified"),
	}


@frappe.whitelist()
def get_master_records(doctype, limit=8):
	"""Master Setup detail panel: the latest records of one master."""
	allowed = {m["doctype"] for category in MASTER_SETUP for m in category["masters"]}
	if doctype not in allowed or not can_manage(doctype):
		frappe.throw(_("You do not have permission to view this master."), frappe.PermissionError)
	meta = frappe.get_meta(doctype)
	active_field, active_value = get_active_field(meta)
	title_field = meta.title_field if meta.title_field and meta.has_field(meta.title_field) else None
	fields = ["name", "modified"] + ([title_field] if title_field else []) + ([active_field] if active_field else [])
	route = "/desk/" + doctype.lower().replace(" ", "-")
	rows = frappe.get_list(doctype, fields=fields, order_by="modified desc", limit_page_length=frappe.utils.cint(limit) or 8)
	return [
		{
			"name": r.name,
			"title": (r.get(title_field) if title_field else None) or r.name,
			"active": None if not active_field else frappe.utils.cint(r.get(active_field)) == active_value,
			"modified": r.modified,
			"route": f"{route}/{quote(r.name, safe='')}",
		}
		for r in rows
	]


# --- In-app list and form -------------------------------------------------
# The Vue Master Setup pages create and edit masters without going to the
# desk. Every call is limited to the registry's DocTypes and to users who can
# manage them; saving and deleting go through the normal Document API, so
# DocType validation, the guards in pathways.utils.master_setup and version
# history all still apply.

LAYOUT_FIELDTYPES = ("Section Break", "Column Break", "Tab Break")
NO_VALUE_FIELDTYPES = (*LAYOUT_FIELDTYPES, "HTML", "Button", "Heading", "Image", "Fold")
FIELD_PROPS = (
	"fieldname",
	"fieldtype",
	"label",
	"reqd",
	"default",
	"depends_on",
	"mandatory_depends_on",
	"read_only_depends_on",
	"read_only",
	"fetch_from",
	"fetch_if_empty",
	"in_list_view",
	"description",
	"length",
	"collapsible",
)


def _check_master(doctype):
	if not get_master(doctype) or not can_manage(doctype):
		frappe.throw(_("You do not have permission to manage this master."), frappe.PermissionError)


def _fields(meta):
	"""Fields in form order, minus hidden ones. A hidden section hides
	everything in it, as on the desk form."""
	out = []
	skipping_section = False
	for df in meta.fields:
		if df.fieldtype in ("Section Break", "Tab Break"):
			skipping_section = bool(df.hidden)
		if skipping_section or df.hidden or df.fieldtype in ("HTML", "Button", "Image", "Fold"):
			continue
		field = {prop: df.get(prop) for prop in FIELD_PROPS}
		field["label"] = _(df.label) if df.label else ""
		field["description"] = _(df.description) if df.description else ""
		if df.fieldtype == "Select":
			field["options"] = (df.options or "").split("\n")
		else:
			field["options"] = df.options
		out.append(field)
	return out


def _name_field(meta):
	autoname = (meta.autoname or "").strip()
	return autoname[len("field:") :] if autoname.startswith("field:") else None


@frappe.whitelist()
def get_master_form(doctype):
	"""Field layout and permissions for the in-app master form."""
	_check_master(doctype)
	meta = frappe.get_meta(doctype)
	master = get_master(doctype)
	active_field, active_value = get_active_field(meta)
	child_tables = {
		df.options: {"fields": _fields(frappe.get_meta(df.options))}
		for df in meta.get_table_fields()
		if not df.hidden
	}
	return {
		"doctype": doctype,
		"label": _(master.get("label") or doctype),
		"singular": _(master.get("singular") or doctype),
		"description": _(master.get("description") or ""),
		"icon": master.get("icon") or "database",
		"title_field": meta.title_field if meta.title_field and meta.has_field(meta.title_field) else None,
		"name_field": _name_field(meta),
		"active_field": active_field,
		"active_value": active_value,
		"fields": _fields(meta),
		"child_tables": child_tables,
		"can_create": bool(frappe.has_permission(doctype, "create")),
		"can_write": bool(frappe.has_permission(doctype, "write")),
		"can_delete": bool(frappe.has_permission(doctype, "delete")),
	}


@frappe.whitelist()
def get_master_list(doctype, txt="", status="", start=0, page_length=20):
	"""One page of a master's records for the in-app list."""
	_check_master(doctype)
	meta = frappe.get_meta(doctype)
	active_field, active_value = get_active_field(meta)
	title_field = meta.title_field if meta.title_field and meta.has_field(meta.title_field) else None

	columns = [
		df
		for df in meta.fields
		if df.in_list_view
		and not df.hidden
		and df.fieldtype not in NO_VALUE_FIELDTYPES
		and df.fieldtype not in frappe.model.table_fields
		# The name column already shows the title and the naming field.
		and df.fieldname not in (active_field, title_field, _name_field(meta))
	][:4]

	fields = ["name", "modified", *([title_field] if title_field else []), *(df.fieldname for df in columns)]
	if active_field:
		fields.append(active_field)

	filters = {}
	if active_field and status == "active":
		filters[active_field] = active_value
	elif active_field and status == "inactive":
		filters[active_field] = ["!=", active_value]

	or_filters = None
	txt = (txt or "").strip()
	if txt:
		searchable = {"name", *([title_field] if title_field else [])}
		searchable.update(df.fieldname for df in columns if df.fieldtype in ("Data", "Link", "Select", "Small Text"))
		like = "%" + txt.replace("%", r"\%").replace("_", r"\_") + "%"
		or_filters = [[f, "like", like] for f in sorted(searchable)]

	start = max(frappe.utils.cint(start), 0)
	page_length = min(max(frappe.utils.cint(page_length) or 20, 1), 100)
	rows = frappe.get_list(
		doctype,
		fields=fields,
		filters=filters,
		or_filters=or_filters,
		order_by="modified desc",
		start=start,
		page_length=page_length,
	)
	total = len(frappe.get_list(doctype, filters=filters, or_filters=or_filters, pluck="name", limit_page_length=0))

	return {
		"columns": [{"fieldname": df.fieldname, "label": _(df.label), "fieldtype": df.fieldtype} for df in columns],
		"rows": [
			{
				**r,
				"title": (r.get(title_field) if title_field else None) or r.name,
				"active": None if not active_field else frappe.utils.cint(r.get(active_field)) == active_value,
			}
			for r in rows
		],
		"total": total,
	}


@frappe.whitelist()
def get_master_doc(doctype, name):
	_check_master(doctype)
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	return doc.as_dict(no_default_fields=False, convert_dates_to_str=True)


def _link_targets():
	targets = set()
	for category in MASTER_SETUP:
		for master in category["masters"]:
			if not frappe.db.exists("DocType", master["doctype"]):
				continue
			meta = frappe.get_meta(master["doctype"])
			for m in (meta, *(frappe.get_meta(df.options) for df in meta.get_table_fields())):
				targets.update(df.options for df in m.get_link_fields() if df.options)
	return targets


@frappe.whitelist()
def search_link(doctype, txt="", page_length=20):
	"""Link-field search for the master forms. Only active records are
	offered, since the inactive-link guard would reject them on save."""
	if not any(can_manage(m["doctype"]) for c in MASTER_SETUP for m in c["masters"]) or doctype not in _link_targets():
		frappe.throw(_("You do not have permission to search {0}.").format(_(doctype)), frappe.PermissionError)

	from frappe.desk.search import search_link as desk_search_link

	active_field, active_value = get_active_field(frappe.get_meta(doctype))
	filters = {active_field: active_value} if active_field else {}
	if doctype == "User":
		filters["user_type"] = "System User"
	return desk_search_link(doctype, txt or "", filters=filters or None, page_length=min(frappe.utils.cint(page_length) or 20, 50))


@frappe.whitelist(methods=["POST"])
def save_master(doctype, doc):
	"""Insert or update one master record. An update carries the `modified`
	it was loaded with, so a save over someone else's newer change fails
	with Frappe's usual "Document has been modified" error."""
	_check_master(doctype)
	data = frappe.parse_json(doc) or {}
	if not isinstance(data, dict):
		frappe.throw(_("Invalid record."))

	meta = frappe.get_meta(doctype)
	data = {k: v for k, v in data.items() if not k.startswith("__")}
	data["doctype"] = doctype
	for df in meta.get_table_fields():
		rows = data.get(df.fieldname) or []
		data[df.fieldname] = [
			{
				**{k: v for k, v in row.items() if not k.startswith("__") and k not in ("parent", "parenttype", "parentfield")},
				"doctype": df.options,
			}
			for row in rows
			if isinstance(row, dict)
		]

	# A new record never carries a name (the DocType names it on insert). An
	# update to a record deleted meanwhile fails in save() rather than
	# quietly re-creating it.
	if not data.get("name"):
		data.pop("name", None)
		record = frappe.get_doc(data)
		record.insert()
	else:
		if not data.get("modified"):
			frappe.throw(_("Reload the record before saving it."))
		record = frappe.get_doc(data)
		record.save()

	return record.as_dict(no_default_fields=False, convert_dates_to_str=True)


@frappe.whitelist(methods=["POST"])
def delete_master(doctype, name):
	_check_master(doctype)
	frappe.delete_doc(doctype, name)
