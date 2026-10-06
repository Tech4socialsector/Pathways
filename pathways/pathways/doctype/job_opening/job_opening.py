# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

# Statuses that may only be reached once the linked Pre-Recruitment Green
# Sheet has been fully approved (unless the user can override, see below).
STATUSES_REQUIRING_APPROVED_GREEN_SHEET = ("Approved", "Advertised")


def can_override_status(user=None):
	"""System Managers may set any Job Opening status directly, without
	going through the Pre-Recruitment Green Sheet approval chain.
	"""
	return "System Manager" in frappe.get_roles(user or frappe.session.user)


class JobOpening(Document):
	def validate(self):
		self.validate_green_sheet_link()
		self.validate_status_transition()

	def validate_green_sheet_link(self):
		if not self.pre_recruitment_green_sheet or self.is_new():
			return
		sheet_job = frappe.db.get_value(
			"Pre-Recruitment Green Sheet", self.pre_recruitment_green_sheet, "job_opening"
		)
		if sheet_job != self.name:
			frappe.throw(
				f"Pre-Recruitment Green Sheet {self.pre_recruitment_green_sheet} "
				f"belongs to a different Job Opening."
			)

	def validate_status_transition(self):
		if self.status not in STATUSES_REQUIRING_APPROVED_GREEN_SHEET:
			return

		if not self.is_new():
			previous_status = frappe.db.get_value("Job Opening", self.name, "status")
			if previous_status == self.status:
				return

		if can_override_status():
			return

		if not self.pre_recruitment_green_sheet:
			frappe.throw(
				f"Job Opening cannot be moved to {self.status} without an approved "
				f"Pre-Recruitment Green Sheet."
			)
		green_sheet_status, green_sheet_docstatus = frappe.db.get_value(
			"Pre-Recruitment Green Sheet",
			self.pre_recruitment_green_sheet,
			["status", "docstatus"],
		)
		if green_sheet_docstatus != 1 or green_sheet_status != "Approved":
			frappe.throw(
				f"Cannot move this Job Opening to {self.status}: its Pre-Recruitment "
				f"Green Sheet is '{green_sheet_status}', not 'Approved'."
			)
