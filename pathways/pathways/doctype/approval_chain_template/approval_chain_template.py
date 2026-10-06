# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ApprovalChainTemplate(Document):
	def validate(self):
		self.validate_steps()
		self.validate_single_active_template()

	def validate_steps(self):
		if not self.steps:
			frappe.throw(_("At least one Approval Chain Step is required."))

		sequences = [step.sequence for step in self.steps]
		if any((s or 0) <= 0 for s in sequences):
			frappe.throw(_("Approval Chain Step sequence numbers must be positive."))
		if len(sequences) != len(set(sequences)):
			frappe.throw(_("Approval Chain Steps must have unique sequence numbers."))

		for step in self.steps:
			step.approver_type = step.approver_type or "Role"
			if step.approver_type == "User":
				if not step.approver_user:
					frappe.throw(_("Row {0}: choose the Approver User.").format(step.idx))
				step.approver_role = None
			else:
				if not step.approver_role:
					frappe.throw(_("Row {0}: choose the Approver Role.").format(step.idx))
				step.approver_user = None

		self.steps.sort(key=lambda step: step.sequence)
		for idx, step in enumerate(self.steps, start=1):
			step.idx = idx

	def validate_single_active_template(self):
		"""Only one active chain may answer a given track + document type +
		employment type, otherwise which chain a Green Sheet gets would be
		arbitrary."""
		if not self.is_active:
			return
		clash = frappe.db.exists(
			"Approval Chain Template",
			{
				"name": ["!=", self.name],
				"is_active": 1,
				"track": self.track,
				"applies_to": self.applies_to,
				"employment_type": self.employment_type or ["in", ["", None]],
			},
		)
		if clash:
			frappe.throw(
				_(
					"Approval Chain Template {0} is already active for this track, document type and "
					"employment type. Deactivate it first."
				).format(frappe.bold(clash))
			)
