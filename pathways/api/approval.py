# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from pathways.utils.approval import (
	APPROVABLE_DOCTYPES,
	get_chain_status,
	get_pending_for_user,
)
from pathways.utils.approval import (
	record_approval_action as _record_approval_action,
)


@frappe.whitelist()
def get_my_pending_approvals():
	"""Documents currently sitting at an approval step this user may act on
	— backs the "My Approvals" page. Who that is comes entirely from the
	Approval Chain Templates and Pathways Settings."""
	return get_pending_for_user()


@frappe.whitelist()
def record_approval_action(doctype, docname, action, remarks=None, channel="Digital"):
	return _record_approval_action(doctype, docname, action, remarks, channel)


@frappe.whitelist()
def get_approval_chain_status(doctype, docname):
	if doctype not in APPROVABLE_DOCTYPES:
		frappe.throw(_("{0} is not an approvable document type.").format(doctype))

	# frappe.get_doc() does not check permissions on its own; without this
	# a Candidate or unrelated staff role could read any Green Sheet.
	doc = frappe.get_doc(doctype, docname)
	doc.check_permission("read")
	return get_chain_status(doc)
