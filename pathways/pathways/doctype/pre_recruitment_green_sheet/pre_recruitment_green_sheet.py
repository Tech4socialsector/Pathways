# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from pathways.utils.approval import freeze_steps, set_approval_chain_template
from pathways.utils.approval import record_approval_action as _record_approval_action

# A job may have at most one sheet in any of these states at a time.
OPEN_STATUSES = ("Under Approval", "Approved", "Returned for Revision")


class PreRecruitmentGreenSheet(Document):
	def validate(self):
		set_approval_chain_template(self, "Pre-Recruitment Green Sheet")
		if self.docstatus == 0:
			self.validate_single_open_sheet(include_drafts=True)

	def before_submit(self):
		# Lock the job row so two sheets submitted at the same moment for
		# the same job are serialised, then re-check under the lock.
		frappe.db.get_value("Job Opening", self.job_opening, "name", for_update=True)
		self.validate_single_open_sheet(include_drafts=False)
		freeze_steps(self)

	def validate_single_open_sheet(self, include_drafts):
		others = frappe.get_all(
			"Pre-Recruitment Green Sheet",
			filters={"job_opening": self.job_opening, "name": ["!=", self.name or ""], "docstatus": ["<", 2]},
			fields=["name", "docstatus", "status"],
		)
		for other in others:
			if other.docstatus == 1 and other.status in OPEN_STATUSES:
				frappe.throw(
					_("Job Opening {0} already has an active Green Sheet ({1}, {2}).").format(
						self.job_opening, other.name, _(other.status)
					)
				)
			if include_drafts and other.docstatus == 0:
				frappe.throw(
					_("Job Opening {0} already has a draft Green Sheet ({1}).").format(self.job_opening, other.name)
				)

	def on_submit(self):
		sync_job_opening(self)
		from pathways.utils.approval import get_current_step, notify_approvers

		step = get_current_step(self)
		if step:
			notify_approvers(self, step)

	def on_update_after_submit(self):
		sync_job_opening(self)

	def on_cancel(self):
		# Changes to self are not persisted after on_cancel, hence db_set.
		self.db_set({"status": "Draft", "current_approval_level": 0})
		sync_job_opening(self)


def sync_job_opening(green_sheet):
	"""Mirror the Green Sheet's progress onto its Job Opening.

	Only moves the job along the approval part of its lifecycle
	(Draft -> Pending Approval -> Approved, and back to Draft when the
	sheet is returned or cancelled) — a job already advanced manually
	(Advertised, Closed, ...) is never pulled back. db.set_value is used
	because approvers usually have only read access on Job Opening.
	"""
	job = frappe.db.get_value(
		"Job Opening",
		green_sheet.job_opening,
		["name", "status", "pre_recruitment_green_sheet"],
		as_dict=True,
	)
	if not job:
		return

	updates = {}
	if green_sheet.docstatus == 2:
		if job.pre_recruitment_green_sheet == green_sheet.name and job.status in (
			"Pending Approval",
			"Approved",
		):
			updates["status"] = "Draft"
	elif green_sheet.status == "Under Approval":
		updates["pre_recruitment_green_sheet"] = green_sheet.name
		if job.status == "Draft":
			updates["status"] = "Pending Approval"
	elif green_sheet.status == "Approved":
		updates["pre_recruitment_green_sheet"] = green_sheet.name
		if job.status in ("Draft", "Pending Approval"):
			updates["status"] = "Approved"
	elif green_sheet.status == "Returned for Revision":
		if job.pre_recruitment_green_sheet == green_sheet.name and job.status == "Pending Approval":
			updates["status"] = "Draft"

	updates = {k: v for k, v in updates.items() if job.get(k) != v}
	if updates:
		frappe.db.set_value("Job Opening", job.name, updates)


@frappe.whitelist()
def record_approval_action(green_sheet_name, action, remarks=None, channel="Digital"):
	return _record_approval_action("Pre-Recruitment Green Sheet", green_sheet_name, action, remarks, channel)
