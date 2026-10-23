# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Post-interview regrets and panel thanks (workflow steps 32-33) went live.

ensure_email_events() never overwrites a rule staff may have edited, so the
two facts that changed are applied here, each only while the rule still has
the old default: the post-interview regret moves to its own "Regret After
Interview" template, and the panel thank-you goes to the panellists the code
names (it had no recipients while it was never sent). Also seeds who
approves honoraria. Safe to run again."""

import frappe

from pathways.utils.email_events import ensure_email_events

DEFAULT_APPROVER_ROLES = ("Pathways CFO", "Pathways Admin")


def execute():
	ensure_email_events()
	repoint_rules()
	seed_honorarium_settings()


def repoint_rules():
	rule = frappe.db.get_value("Recruitment Email Rule", "regret_after_interview", ["email_template"], as_dict=True)
	if rule and rule.email_template == "Regret Mail" and frappe.db.exists("Email Template", "Regret After Interview"):
		frappe.db.set_value("Recruitment Email Rule", "regret_after_interview", "email_template", "Regret After Interview", update_modified=False)

	if frappe.db.exists("Recruitment Email Rule", "panel_thanks"):
		rule = frappe.get_doc("Recruitment Email Rule", "panel_thanks")
		has_recipients = (
			rule.send_to_candidate or rule.send_to_committee or rule.send_to_approvers or rule.recipient_roles or (rule.extra_recipients or "").strip()
		)
		if not has_recipients:
			frappe.db.set_value("Recruitment Email Rule", "panel_thanks", "send_to_approvers", 1, update_modified=False)


def seed_honorarium_settings():
	settings = frappe.get_single("Pathways Settings")
	changed = False
	if not settings.get("honorarium_approver_roles"):
		for role in DEFAULT_APPROVER_ROLES:
			if frappe.db.exists("Role", role):
				settings.append("honorarium_approver_roles", {"role": role})
				changed = True
	stored = frappe.db.sql("select 1 from `tabSingles` where doctype='Pathways Settings' and field='honorarium_external_only'")
	if not stored:
		settings.honorarium_external_only = 1
		changed = True
	if changed:
		settings.flags.ignore_permissions = True
		settings.flags.ignore_mandatory = True
		settings.save()
