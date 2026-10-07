# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Per-user list preferences (which columns a table shows, and in what
order), kept as user defaults so they follow the user across browsers."""

import json
import re

import frappe

KEY = re.compile(r"^[a-z0-9_-]{1,60}$")


def _key(list_key):
	if not KEY.match(list_key or ""):
		frappe.throw(frappe._("Invalid list."))
	# Underscores only: Frappe reads a default whose key changes under
	# scrub() (e.g. contains "-") as a user-permission key.
	return f"pathways_columns_{list_key.replace('-', '_')}"


@frappe.whitelist()
def get_list_columns(list_key):
	value = frappe.defaults.get_user_default(_key(list_key))
	try:
		return json.loads(value) if value else None
	except ValueError:
		return None


@frappe.whitelist(methods=["POST"])
def save_list_columns(list_key, settings=None):
	"""settings: {"order": [column keys], "hidden": [column keys]}; empty
	resets the list to its default columns."""
	key = _key(list_key)
	if isinstance(settings, str):
		settings = frappe.parse_json(settings) if settings else None
	if not settings:
		frappe.defaults.clear_user_default(key)
		return None
	clean = {
		"order": [str(k)[:60] for k in (settings.get("order") or [])][:80],
		"hidden": [str(k)[:60] for k in (settings.get("hidden") or [])][:80],
	}
	frappe.defaults.set_user_default(key, json.dumps(clean))
	return clean
