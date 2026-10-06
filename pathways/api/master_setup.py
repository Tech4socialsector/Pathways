# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Master Setup landing page data. The registry lives in
pathways.utils.master_setup; records themselves are maintained through
the framework's standard list/form views, which enforce permissions,
validation and version history on their own.
"""

import frappe
from frappe import _

from pathways.utils.master_setup import MASTER_SETUP, can_manage, get_active_field


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
	route = "/app/" + doctype.lower().replace(" ", "-")

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
	}
