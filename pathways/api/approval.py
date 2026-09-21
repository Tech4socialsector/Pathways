# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe

from pathways.pathways.doctype.pre_recruitment_green_sheet.pre_recruitment_green_sheet import (
	record_approval_action as _record_pre_recruitment_approval,
)
from pathways.pathways.doctype.post_interview_green_sheet.post_interview_green_sheet import (
	record_approval_action as _record_post_interview_approval,
)

GREEN_SHEET_HANDLERS = {
	"Pre-Recruitment Green Sheet": _record_pre_recruitment_approval,
	"Post-Interview Green Sheet": _record_post_interview_approval,
}


@frappe.whitelist()
def get_my_pending_approvals():
	"""Green Sheets currently sitting at an approval level this user's
	roles can act on — backs the "My Pending Approvals" workspace/page.
	"""
	user_roles = set(frappe.get_roles(frappe.session.user))
	pending = []

	for doctype in ("Pre-Recruitment Green Sheet", "Post-Interview Green Sheet"):
		docs = frappe.get_all(
			doctype,
			filters={"status": "Under Approval"},
			fields=["name", "job_opening", "approval_chain_template", "current_approval_level"],
		)
		for doc in docs:
			if not doc.approval_chain_template:
				continue
			chain = frappe.get_cached_doc("Approval Chain Template", doc.approval_chain_template)
			step = next((s for s in chain.steps if s.sequence == doc.current_approval_level), None)
			if step and step.approver_role in user_roles:
				pending.append(
					{
						"doctype": doctype,
						"name": doc.name,
						"job_opening": doc.job_opening,
						"approver_label": step.approver_label,
					}
				)

	return pending


@frappe.whitelist()
def record_approval_action(doctype, docname, action, remarks=None, channel="Digital"):
	handler = GREEN_SHEET_HANDLERS.get(doctype)
	if not handler:
		frappe.throw(f"Approval actions are not supported for {doctype}.")
	return handler(docname, action, remarks, channel)


@frappe.whitelist()
def get_approval_chain_status(doctype, docname):
	if doctype not in GREEN_SHEET_HANDLERS:
		frappe.throw(f"{doctype} is not a supported Green Sheet type.")

	doc = frappe.get_doc(doctype, docname)
	if not doc.approval_chain_template:
		return {"steps": [], "current_level": 0, "status": doc.status}

	chain = frappe.get_doc("Approval Chain Template", doc.approval_chain_template)
	steps = [
		{
			"sequence": s.sequence,
			"approver_role": s.approver_role,
			"approver_label": s.approver_label,
			"completed": s.sequence < doc.current_approval_level
			or doc.status == "Approved"
			and s.sequence <= doc.current_approval_level,
		}
		for s in chain.steps
	]
	return {
		"steps": steps,
		"current_level": doc.current_approval_level,
		"status": doc.status,
		"log": [
			{
				"sequence": row.sequence,
				"approver": row.approver,
				"approver_role": row.approver_role,
				"action": row.action,
				"channel": row.channel,
				"remarks": row.remarks,
				"acted_on": row.acted_on,
			}
			for row in doc.approval_log
		],
	}
