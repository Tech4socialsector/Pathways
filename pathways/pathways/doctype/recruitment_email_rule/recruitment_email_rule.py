# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import validate_email_address


class RecruitmentEmailRule(Document):
	"""Who gets one recruitment email, and with which template. Sent from
	pathways.utils.communication.send_event; edited on the Email Setup page."""

	def validate(self):
		for field in ("extra_recipients", "cc"):
			emails = [e.strip() for e in (self.get(field) or "").replace(";", ",").split(",") if e.strip()]
			for email in emails:
				if not validate_email_address(email):
					frappe.throw(_("{0}: {1} is not a valid email address.").format(self.meta.get_label(field), email))
			self.set(field, ", ".join(emails))
