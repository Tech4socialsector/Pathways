# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class JobOpening(Document):
	def validate(self):
		self.validate_status_transition()

	def validate_status_transition(self):
		if self.is_new():
			return

		previous_status = frappe.db.get_value("Job Opening", self.name, "status")
		if previous_status == self.status:
			return

		if self.status == "Advertised":
			if not self.pre_recruitment_green_sheet:
				frappe.throw(
					"Job Opening cannot be moved to Advertised without a linked Pre-Recruitment Green Sheet."
				)
			green_sheet_status = frappe.db.get_value(
				"Pre-Recruitment Green Sheet", self.pre_recruitment_green_sheet, "status"
			)
			if green_sheet_status != "Approved":
				frappe.throw(
					f"Cannot advertise this Job Opening: its Pre-Recruitment Green Sheet "
					f"is '{green_sheet_status}', not 'Approved'."
				)
