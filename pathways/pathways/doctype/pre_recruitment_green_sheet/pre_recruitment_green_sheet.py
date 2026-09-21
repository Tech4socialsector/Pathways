# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from pathways.utils.approval import record_approval_action as _record_approval_action
from pathways.utils.approval import set_approval_chain_template


class PreRecruitmentGreenSheet(Document):
	def validate(self):
		set_approval_chain_template(self, "Pre-Recruitment Green Sheet")

	def before_submit(self):
		if not self.approval_chain_template:
			frappe.throw(
				"No active Approval Chain Template found for this track. "
				"Configure one before submitting for approval."
			)
		self.status = "Under Approval"
		self.current_approval_level = 1

	def on_cancel(self):
		self.status = "Draft"
		self.current_approval_level = 0


@frappe.whitelist()
def record_approval_action(green_sheet_name, action, remarks=None, channel="Digital"):
	return _record_approval_action(
		"Pre-Recruitment Green Sheet", green_sheet_name, action, remarks, channel
	)
