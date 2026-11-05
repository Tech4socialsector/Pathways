# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Candidates no longer see the status of their applications on the portal:
the portal login emails stop promising it. Only the old sentences are
replaced, so other edits made on the Email Setup page are kept."""

import frappe

OLD_NEW = (
	("We will email you about each update.", "We will email you when there is news about your application."),
	("Your NLSIU Careers login: track your application", "Your NLSIU Careers login"),
	(
		"You can now log in to the NLSIU Careers portal to track the status of your application(s) and view what you submitted.",
		"You can now log in to the NLSIU Careers portal to view what you submitted and reply to interview invitations. "
		"We will email you about each update.",
	),
	(
		"log in to the NLSIU Careers portal, track the status of your application(s) and view what you submitted.",
		"log in to the NLSIU Careers portal, view what you submitted and reply to interview invitations. We will email you about each update.",
	),
)


def execute():
	for name in ("Candidate Portal Login", "Candidate Portal Login (Existing Account)"):
		if not frappe.db.exists("Email Template", name):
			continue
		doc = frappe.get_doc("Email Template", name)
		changed = False
		for field in ("subject", "response", "response_html"):
			value = doc.get(field) or ""
			for old, new in OLD_NEW:
				if old in value:
					value = value.replace(old, new)
					changed = True
			doc.set(field, value)
		if changed:
			doc.save(ignore_permissions=True)
