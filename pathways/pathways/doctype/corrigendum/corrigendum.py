# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime


class Corrigendum(Document):
	def validate(self):
		self.enforce_registrar_signoff()
		if self.recruitment_notification and not self.job_opening:
			self.job_opening = frappe.db.get_value("Recruitment Notification", self.recruitment_notification, "job_opening")
		if self.changed_field == "Closing Date" and self.is_new():
			if not self.new_value or get_datetime(self.new_value) <= now_datetime():
				frappe.throw(_("The new closing date must be in the future."))

	def enforce_registrar_signoff(self):
		from pathways.permissions import has_duty

		if not has_duty("corrigendum_signer_roles"):
			frappe.throw(
				"You are not authorised to create or sign a Corrigendum "
				"(see Pathways Settings > Corrigendum Signer Roles).",
				frappe.PermissionError,
			)
		self.signed_by = frappe.session.user

	def before_insert(self):
		if self.changed_field == "Closing Date" and self.job_opening:
			self.previous_value = str(frappe.db.get_value("Job Opening", self.job_opening, "application_deadline") or "")

	def after_insert(self):
		# Applied once, when issued: later edits to the record change nothing.
		if self.changed_field == "Closing Date":
			self.extend_deadline()
		if self.job_opening:
			from pathways.utils.communication import job_email_context, send_event

			context = job_email_context(frappe.get_doc("Job Opening", self.job_opening))
			context.update(
				{
					"change": _("deadline extended to {0}").format(context["deadline"])
					if self.changed_field == "Closing Date"
					else self.new_value,
					"remarks": self.remarks,
				}
			)
			send_event("corrigendum_issued", "Corrigendum", self.name, context, job_opening=self.job_opening)

	def extend_deadline(self):
		"""Move the job's application deadline (what actually opens and closes
		applications) and the notification's closing date; an ad that already
		auto-closed is advertised again."""
		new_deadline = get_datetime(self.new_value)
		if self.recruitment_notification:
			frappe.db.set_value("Recruitment Notification", self.recruitment_notification, "closing_datetime", new_deadline)
		if not self.job_opening:
			return
		job = frappe.get_doc("Job Opening", self.job_opening)
		job.application_deadline = new_deadline
		if job.status == "Closed":
			job.status = "Advertised"
			# Approved and advertised before; re-opening needs no new Green Sheet.
			job.flags.reopening = True
		job.save(ignore_permissions=True)
