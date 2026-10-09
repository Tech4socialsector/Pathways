# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Candidate(Document):
	def validate(self):
		self.email = (self.email or "").strip().lower()

	def on_update(self):
		# Keep the portal login's mobile number in step, so the candidate can
		# log in with the number on their profile.
		if self.has_value_changed("mobile_number"):
			from pathways.utils.candidate_account import sync_login_mobile

			sync_login_mobile(self.email, self.mobile_number)
