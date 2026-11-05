# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""One row per Selection Committee panellist of a job: when they were
thanked and, for external experts, their honorarium (workflow step 33).
Rows are created by "Send thank-you to panel" on the consolidated score
sheet; the recruitment team enters the amount, PAN and bank details on the
Honorarium page and sends them to the Finance team. Internal panellists'
rows are Not applicable and only track the thank-you."""

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
IFSC_PATTERN = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
ACCOUNT_PATTERN = re.compile(r"^[0-9]{6,18}$")


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
		if self.ifsc_code:
			self.ifsc_code = self.ifsc_code.strip().upper()
			if not IFSC_PATTERN.match(self.ifsc_code):
				frappe.throw(_("{0} is not a valid IFSC code (e.g. SBIN0001234).").format(self.ifsc_code))
		if self.bank_account_number:
			self.bank_account_number = re.sub(r"[\s-]", "", self.bank_account_number)
			if not ACCOUNT_PATTERN.match(self.bank_account_number):
				frappe.throw(_("The account number should be 6 to 18 digits."))
		if self.status == "Not applicable":
			self.amount = 0
