# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ShortlistingCommittee(Document):
	def validate(self):
		self.validate_committee_size()

	def validate_committee_size(self):
		settings = frappe.get_cached_doc("Pathways Settings")
		min_size = settings.min_shortlisting_committee_size or 2
		max_size = settings.max_shortlisting_committee_size or 3
		size = len(self.members)

		if size < min_size or size > max_size:
			frappe.throw(
				f"Shortlisting Committee must have between {min_size} and {max_size} members "
				f"(currently has {size})."
			)

	def after_insert(self):
		from pathways.api.scoring import shortlisting_ratio
		from pathways.utils.communication import job_email_context, send_event

		job = frappe.get_doc("Job Opening", self.job_opening)
		context = job_email_context(job)
		context.update(
			{
				"application_count": frappe.db.count("Application", {"job_opening": job.name, "status": ["!=", "Withdrawn"]}),
				"ratio": shortlisting_ratio(job),
				"deadline": frappe.utils.formatdate(self.shortlisting_deadline) if self.shortlisting_deadline else "",
			}
		)
		send_event("committee_assigned", "Shortlisting Committee", self.name, context, job_opening=job.name)

	def on_update(self):
		self.sync_member_roles()

	def sync_member_roles(self):
		for row in self.members:
			user = frappe.get_doc("User", row.member)
			if "Pathways Shortlisting Committee Member" not in [r.role for r in user.roles]:
				user.append("roles", {"role": "Pathways Shortlisting Committee Member"})
				user.save(ignore_permissions=True)
