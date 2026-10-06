# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Corrigendum(Document):
	def validate(self):
		self.enforce_registrar_signoff()
		self.apply_to_notification()

	def enforce_registrar_signoff(self):
		from pathways.permissions import has_duty

		if not has_duty("corrigendum_signer_roles"):
			frappe.throw(
				"You are not authorised to create or sign a Corrigendum "
				"(see Pathways Settings > Corrigendum Signer Roles).",
				frappe.PermissionError,
			)
		self.signed_by = frappe.session.user

	def apply_to_notification(self):
		if self.changed_field == "Closing Date" and self.recruitment_notification:
			frappe.db.set_value(
				"Recruitment Notification",
				self.recruitment_notification,
				"closing_datetime",
				self.new_value,
			)
