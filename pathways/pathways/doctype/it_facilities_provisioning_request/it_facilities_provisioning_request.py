# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""What IT & Facilities set up for a new joiner (folder 12: "arrange for a
laptop, create NLS email ID, and share the same"; access card and seating
are tracked alongside). Created when the Joining is confirmed; completed
from the IT Requests page, which tells the recruitment team.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

TASKS = ("laptop_arranged", "official_email_created", "access_card_issued", "seating_arranged")


class ITFacilitiesProvisioningRequest(Document):
	def validate(self):
		if self.official_email_created and self.official_email:
			self.official_email = self.official_email.strip()
		if self.status == "Completed" or self.completed_on:
			self.status = "Completed"
		elif any(self.get(task) for task in TASKS) or self.official_email:
			self.status = "In Progress"
		else:
			self.status = "Pending"

	def complete(self):
		if not self.laptop_arranged:
			frappe.throw(_("Tick Laptop Arranged before completing the request."))
		if not (self.official_email_created and self.official_email):
			frappe.throw(_("Create the official email ID and enter it before completing the request."))
		self.status = "Completed"
		self.completed_by = frappe.session.user
		self.completed_on = now_datetime()
		self.save()

	def on_update(self):
		if self.status == "Completed" and self.has_value_changed("status") and not self.is_new():
			from pathways.utils.onboarding import on_it_request_completed

			on_it_request_completed(self)
