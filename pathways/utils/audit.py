# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime


def log_application_status_change(doc, method=None):
	"""Hooked to Application's on_update via hooks.py doc_events.
	Writes an immutable Application Status History row whenever the
	status field actually changes value.
	"""
	if doc.is_new():
		return

	previous_status = doc.get_doc_before_save() and doc.get_doc_before_save().status
	if previous_status is None or previous_status == doc.status:
		return

	history = frappe.new_doc("Application Status History")
	history.application = doc.name
	history.previous_status = previous_status
	history.new_status = doc.status
	history.changed_by = frappe.session.user
	history.changed_on = now_datetime()
	history.source = "Manual" if frappe.session.user != "Administrator" else "System"
	history.insert(ignore_permissions=True)
