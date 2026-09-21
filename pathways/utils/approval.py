# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime

APPROVAL_LOG_CHILD_TABLE_FIELD = "approval_log"


def set_approval_chain_template(doc, applies_to):
	"""Auto-select the active Approval Chain Template for this doc's track
	and the given `applies_to` document type, if one isn't already set.
	"""
	if doc.approval_chain_template or not doc.track:
		return

	template = frappe.db.get_value(
		"Approval Chain Template",
		{"track": doc.track, "applies_to": applies_to, "is_active": 1},
		"name",
	)
	if template:
		doc.approval_chain_template = template


def record_approval_action(doctype, docname, action, remarks=None, channel="Digital"):
	"""Shared chain-walking engine for any Green Sheet doctype that has:
	approval_chain_template (Link), current_approval_level (Int),
	status (Select incl. Under Approval/Approved/Returned for Revision),
	and an `approval_log` child table using the Green Sheet Approval Log doctype.
	"""
	if action not in ("Approved", "Returned for Revision"):
		frappe.throw("Invalid action.")

	doc = frappe.get_doc(doctype, docname)

	if doc.status != "Under Approval":
		frappe.throw(f"This document is not currently Under Approval (status: {doc.status}).")

	if not doc.approval_chain_template:
		frappe.throw("This document has no Approval Chain Template configured.")

	chain = frappe.get_doc("Approval Chain Template", doc.approval_chain_template)
	current_step = next(
		(step for step in chain.steps if step.sequence == doc.current_approval_level), None
	)
	if not current_step:
		frappe.throw("Could not resolve the current approval step.")

	user_roles = frappe.get_roles(frappe.session.user)
	if current_step.approver_role not in user_roles and "Pathways Admin" not in user_roles:
		frappe.throw(
			f"You are not authorised to act on this approval step "
			f"(requires role: {current_step.approver_role})."
		)

	doc.append(
		APPROVAL_LOG_CHILD_TABLE_FIELD,
		{
			"sequence": doc.current_approval_level,
			"approver": frappe.session.user,
			"approver_role": current_step.approver_label,
			"action": action,
			"channel": channel,
			"remarks": remarks,
			"acted_on": now_datetime(),
		},
	)

	if action == "Returned for Revision":
		doc.status = "Returned for Revision"
		doc.current_approval_level = 0
	else:
		is_last_step = doc.current_approval_level >= max(step.sequence for step in chain.steps)
		if is_last_step:
			doc.status = "Approved"
		else:
			doc.current_approval_level += 1

	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return doc.status
