# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe

from pathways.install import seed_application_masters, seed_settings
from pathways.utils.approval import APPROVABLE_DOCTYPES


def execute():
	seed_settings()
	seed_application_masters()
	freeze_in_flight_steps()


def freeze_in_flight_steps():
	"""Sheets submitted before steps were frozen still read the live
	template; copy it onto them now so later template edits can't change
	an approval in progress."""
	frappe.db.sql("update `tabApproval Chain Step` set approver_type = 'Role' where ifnull(approver_type, '') = ''")
	for doctype in APPROVABLE_DOCTYPES:
		for sheet in frappe.get_all(
			doctype,
			filters={"docstatus": 1, "approval_chain_template": ["is", "set"]},
			fields=["name", "approval_chain_template"],
		):
			if frappe.db.exists("Approval Chain Step", {"parenttype": doctype, "parent": sheet.name}):
				continue
			if not frappe.db.exists("Approval Chain Template", sheet.approval_chain_template):
				continue
			template = frappe.get_doc("Approval Chain Template", sheet.approval_chain_template)
			for idx, step in enumerate(sorted(template.steps, key=lambda s: s.sequence), start=1):
				frappe.get_doc(
					{
						"doctype": "Approval Chain Step",
						"parenttype": doctype,
						"parentfield": "approval_steps",
						"parent": sheet.name,
						"idx": idx,
						"sequence": step.sequence,
						"approver_type": step.approver_type or "Role",
						"approver_role": step.approver_role,
						"approver_user": step.approver_user,
						"approver_label": step.approver_label,
					}
				).db_insert()
