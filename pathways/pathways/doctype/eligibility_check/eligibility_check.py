# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class EligibilityCheck(Document):
	def validate(self):
		if not self.is_eligible and not self.ineligibility_reason:
			frappe.throw("Reason for Ineligibility is required when the candidate is marked not eligible.")
		self.checked_by = frappe.session.user
		self.checked_on = now_datetime()
