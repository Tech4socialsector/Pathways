# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from pathways.utils.approval import freeze_steps, set_approval_chain_template
from pathways.utils.approval import record_approval_action as _record_approval_action


class PostInterviewGreenSheet(Document):
	def validate(self):
		# Also copies the track from the Job Opening — without it no
		# template could ever be matched.
		set_approval_chain_template(self, "Post-Interview Green Sheet")
		self.validate_recommended_application()

	def validate_recommended_application(self):
		if not self.recommended_application:
			return
		app_job_opening = frappe.db.get_value("Application", self.recommended_application, "job_opening")
		if app_job_opening != self.job_opening:
			frappe.throw(_("Recommended Application does not belong to this Job Opening."))

		if self.waitlist_application:
			if self.waitlist_application == self.recommended_application:
				frappe.throw(_("The waitlisted candidate must differ from the recommended candidate."))
			wl_job_opening = frappe.db.get_value("Application", self.waitlist_application, "job_opening")
			if wl_job_opening != self.job_opening:
				frappe.throw(_("Waitlist Application does not belong to this Job Opening."))

	def before_submit(self):
		freeze_steps(self)

	def on_submit(self):
		from pathways.utils.approval import get_current_step, notify_approvers

		step = get_current_step(self)
		if step:
			notify_approvers(self, step)

	def on_cancel(self):
		# Changes to self are not persisted after on_cancel, hence db_set.
		self.db_set({"status": "Draft", "current_approval_level": 0})


@frappe.whitelist()
def record_approval_action(green_sheet_name, action, remarks=None, channel="Digital"):
	return _record_approval_action("Post-Interview Green Sheet", green_sheet_name, action, remarks, channel)
