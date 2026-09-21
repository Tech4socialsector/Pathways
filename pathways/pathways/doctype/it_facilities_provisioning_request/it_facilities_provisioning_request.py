# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class ITFacilitiesProvisioningRequest(Document):
	def validate(self):
		if self.laptop_arranged and self.official_email_created:
			self.status = "Completed"
		elif self.laptop_arranged or self.official_email_created:
			self.status = "In Progress"
		else:
			self.status = "Pending"
