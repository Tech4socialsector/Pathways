# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Frappe's Google Settings, edited from Pathways Settings > Google Meet
instead of the desk. The Client Secret never leaves the server: the panel
only learns whether one is stored, and a blank secret on save keeps it."""

import frappe
from frappe import _

FIELDS = ("enable", "client_id", "api_key", "google_drive_picker_enabled", "app_id")


def _doc():
	doc = frappe.get_single("Google Settings")
	# get_single() does not check permissions on its own.
	doc.check_permission("read")
	return doc


def _out(doc):
	return {
		**{field: doc.get(field) for field in FIELDS},
		"has_client_secret": bool(doc.get_password("client_secret", raise_exception=False)),
		"can_edit": bool(frappe.has_permission("Google Settings", "write")),
	}


@frappe.whitelist()
def get_google_settings():
	return _out(_doc())


@frappe.whitelist(methods=["POST"])
def save_google_settings(data):
	data = frappe.parse_json(data) or {}
	doc = _doc()

	for field in ("enable", "google_drive_picker_enabled"):
		if field in data:
			doc.set(field, 1 if frappe.utils.cint(data[field]) else 0)
	for field in ("client_id", "api_key", "app_id"):
		if field in data:
			doc.set(field, (data[field] or "").strip())
	secret = (data.get("client_secret") or "").strip()
	if secret:
		doc.client_secret = secret

	has_secret = bool(secret) or bool(doc.get_password("client_secret", raise_exception=False))
	if doc.enable and not (doc.client_id and has_secret):
		frappe.throw(_("Enter the Client ID and Client Secret before enabling Google."))
	if doc.google_drive_picker_enabled and not (doc.client_id and doc.app_id):
		frappe.throw(_("Google Drive Picker needs the Client ID and the App ID."))

	# save() checks write permission (System Manager by default).
	doc.save()
	return _out(doc)
