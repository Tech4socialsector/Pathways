# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from pathways.utils.approval import record_approval_action as _record_approval_action
from pathways.utils.approval import set_approval_chain_template


class PreRecruitmentGreenSheet(Document):
	def validate(self):
		if self.docstatus == 0 and self.job_opening:
			# Track always follows the Job Opening until submission, so a
			# job whose track is changed picks up the matching chain.
			job_track = frappe.db.get_value("Job Opening", self.job_opening, "track")
			if self.track != job_track:
				self.track = job_track
				self.approval_chain_template = None
		set_approval_chain_template(self, "Pre-Recruitment Green Sheet")

	def before_submit(self):
		if not self.approval_chain_template:
			frappe.throw(
				"No active Approval Chain Template found for this track. "
				"Configure one before submitting for approval."
			)
		self.status = "Under Approval"
		self.current_approval_level = 1

	def on_submit(self):
		sync_job_opening(self)

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
	sheet is returned or cancelled) — a job a System Manager has already
	advanced manually (Advertised, Closed, ...) is never pulled back.
	db.set_value is used because approvers usually have only read access
	on Job Opening.
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
	return _record_approval_action(
		"Pre-Recruitment Green Sheet", green_sheet_name, action, remarks, channel
	)
