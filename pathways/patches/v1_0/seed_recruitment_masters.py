# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe

from pathways.install import seed_application_masters
from pathways.master_data import ADMIN_POST_INTERVIEW_STEPS, chain_steps, seed_master_data


def execute():
	seed_application_masters()
	seed_master_data()
	replace_placeholder_admin_post_interview_chain()


def replace_placeholder_admin_post_interview_chain():
	"""Sites set up before the master data had a one-step System Manager
	stand-in as the Admin post-interview chain. Give it the green sheet's
	real signatories — only while it is still exactly that stand-in.
	Sheets already submitted keep their own frozen steps."""
	name = "Admin - Post-Interview Green Sheet"
	if not frappe.db.exists("Approval Chain Template", name):
		return
	template = frappe.get_doc("Approval Chain Template", name)
	if [(s.approver_type, s.approver_role, s.approver_user) for s in template.steps] != [
		("Role", "System Manager", None)
	]:
		return
	template.set("steps", chain_steps(ADMIN_POST_INTERVIEW_STEPS))
	template.save(ignore_permissions=True)
