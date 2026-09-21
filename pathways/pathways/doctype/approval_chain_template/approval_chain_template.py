# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ApprovalChainTemplate(Document):
	def validate(self):
		self.validate_step_sequence()

	def validate_step_sequence(self):
		if not self.steps:
			frappe.throw("At least one Approval Chain Step is required.")

		sequences = [step.sequence for step in self.steps]
		if len(sequences) != len(set(sequences)):
			frappe.throw("Approval Chain Steps must have unique sequence numbers.")

		self.steps.sort(key=lambda step: step.sequence)
