# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import now_datetime


class ApplicationDocument(Document):
	def validate(self):
		if self.attachment and not self.uploaded_on:
			self.uploaded_on = now_datetime()
