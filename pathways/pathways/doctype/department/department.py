# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Department(Document):
	def validate(self):
		self.check_not_own_parent()

	def check_not_own_parent(self):
		if self.parent_department and self.parent_department == self.department_name:
			frappe.throw("A Department cannot be its own parent.")
