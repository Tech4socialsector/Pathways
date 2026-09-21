# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SelectionCommittee(Document):
	def validate(self):
		self.validate_committee_size()

	def validate_committee_size(self):
		settings = frappe.get_cached_doc("Pathways Settings")
		min_size = settings.min_selection_committee_size or 3
		max_size = settings.max_selection_committee_size or 5
		size = len(self.members)

		if size < min_size or size > max_size:
			frappe.throw(
				f"Selection Committee must have between {min_size} and {max_size} members "
				f"(currently has {size}). Final panels are always a panel, never a single interviewer."
			)

	def on_update(self):
		self.sync_member_roles()

	def sync_member_roles(self):
		for row in self.members:
			user = frappe.get_doc("User", row.member)
			if "Pathways Selection Committee Member" not in [r.role for r in user.roles]:
				user.append("roles", {"role": "Pathways Selection Committee Member"})
				user.save(ignore_permissions=True)
