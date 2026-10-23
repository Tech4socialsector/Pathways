# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""One row per Selection Committee panellist of a job: when they were
thanked and where their honorarium is (workflow step 33). Rows are created
by "Send thank-you to panel" on the consolidated score sheet; finance
approves and records the payment from the Honorarium page."""

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


class PanelHonorarium(Document):
	def validate(self):
		other = frappe.db.exists(
			"Panel Honorarium", {"job_opening": self.job_opening, "panellist": self.panellist, "name": ["!=", self.name]}
		)
		if other:
			frappe.throw(_("{0} already has an honorarium record for this job.").format(self.panellist_name or self.panellist))
		if flt(self.amount) < 0:
			frappe.throw(_("The honorarium amount cannot be negative."))
		if self.pan_number:
			self.pan_number = self.pan_number.strip().upper()
			if not PAN_PATTERN.match(self.pan_number):
				frappe.throw(_("{0} is not a valid PAN (e.g. ABCDE1234F).").format(self.pan_number))
		if self.status == "Not applicable":
			self.amount = 0
		if self.status == "Paid" and not self.paid_on:
			self.paid_on = frappe.utils.today()
		if self.status == "Approved" and self.has_value_changed("status"):
			# Who may approve is configured in Pathways Settings > Honorarium.
			if not can_approve():
				frappe.throw(_("You are not an honorarium approver (Pathways Settings > Honorarium)."), frappe.PermissionError)
			self.approved_by = frappe.session.user
			self.approved_on = frappe.utils.now_datetime()
		if self.status == "Paid" and not self.approved_by:
			frappe.throw(_("Approve the honorarium before marking it paid."))
		if self.status == "Pending":
			self.approved_by = self.approved_on = None


def can_approve(user=None):
	from pathways.permissions import has_duty

	user = user or frappe.session.user
	return user == "Administrator" or "System Manager" in frappe.get_roles(user) or has_duty("honorarium_approver_roles", user)
