# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ApplicationStatusHistory(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw("Application Status History records are immutable and cannot be edited.")

	def on_trash(self):
		frappe.throw("Application Status History records cannot be deleted.")
