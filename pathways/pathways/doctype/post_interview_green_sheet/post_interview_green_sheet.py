# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from pathways.utils.approval import record_approval_action as _record_approval_action
from pathways.utils.approval import set_approval_chain_template


class PostInterviewGreenSheet(Document):
	def validate(self):
		set_approval_chain_template(self, "Post-Interview Green Sheet")
		self.validate_recommended_application()

	def validate_recommended_application(self):
		if not self.recommended_application:
			return
		app_job_opening = frappe.db.get_value("Application", self.recommended_application, "job_opening")
		if app_job_opening != self.job_opening:
			frappe.throw("Recommended Application does not belong to this Job Opening.")

		if self.waitlist_application:
			wl_job_opening = frappe.db.get_value("Application", self.waitlist_application, "job_opening")
			if wl_job_opening != self.job_opening:
				frappe.throw("Waitlist Application does not belong to this Job Opening.")

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
		"Post-Interview Green Sheet", green_sheet_name, action, remarks, channel
	)
