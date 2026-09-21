# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CommunicationLog(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw("Communication Log records are immutable and cannot be edited.")

	def on_trash(self):
		frappe.throw("Communication Log records cannot be deleted.")
