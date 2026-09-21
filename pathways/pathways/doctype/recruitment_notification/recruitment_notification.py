# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class RecruitmentNotification(Document):
	def validate(self):
		self.set_notification_number()

	def set_notification_number(self):
		if self.notification_type == "Formal" and not self.notification_number:
			self.notification_number = make_autoname("PWY-NOTIF-FORMAL-.YYYY.-.###")
