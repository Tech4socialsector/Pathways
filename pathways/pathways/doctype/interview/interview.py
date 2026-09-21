# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Interview(Document):
	def validate(self):
		self.validate_round_specific_fields()

	def validate_round_specific_fields(self):
		if self.round_type == "Final" and not self.selection_committee:
			frappe.throw("A Selection Committee must be linked for a Final round Interview.")
