# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime

# Statuses that may only be reached once the linked Pre-Recruitment Green
# Sheet has been fully approved (unless the user can override, see below).
STATUSES_REQUIRING_APPROVED_GREEN_SHEET = ("Approved", "Advertised")


def can_override_status(user=None):
	"""Holders of Pathways Settings > Job Status Override Role (System
	Manager by default) may set any Job Opening status directly, without
	going through the Pre-Recruitment Green Sheet approval chain.
	"""
	role = frappe.get_cached_doc("Pathways Settings").get("status_override_role")
	return bool(role) and role in frappe.get_roles(user or frappe.session.user)


class JobOpening(Document):
	def validate(self):
		self.validate_green_sheet_link()
		self.validate_status_transition()
		self.validate_application_form()

	def validate_application_form(self):
		for q in self.screening_questions or []:
			if q.answer_type == "Single Choice":
				options = [o.strip() for o in (q.options or "").splitlines() if o.strip()]
				if len(options) < 2:
					frappe.throw(_("Screening question {0}: give at least two choices, one per line.").format(q.idx))
				if len(options) != len(set(options)):
					frappe.throw(_("Screening question {0}: choices must be unique.").format(q.idx))
			if q.answer_type != "Yes/No":
				q.ask_details_if_yes = 0

		seen = set()
		for row in self.required_documents or []:
			if row.document_type in seen:
				frappe.throw(_("Required document {0} is listed twice.").format(row.document_type))
			seen.add(row.document_type)

		if self.status == "Advertised" and self.has_value_changed("status"):
			if not self.application_deadline:
				frappe.throw(_("Set an Application Deadline before advertising this job."))
			if get_datetime(self.application_deadline) <= now_datetime():
				frappe.throw(_("The Application Deadline must be in the future to advertise this job."))

	def validate_green_sheet_link(self):
		if not self.pre_recruitment_green_sheet or self.is_new():
			return
		sheet_job = frappe.db.get_value(
			"Pre-Recruitment Green Sheet", self.pre_recruitment_green_sheet, "job_opening"
		)
		if sheet_job != self.name:
			frappe.throw(
				f"Pre-Recruitment Green Sheet {self.pre_recruitment_green_sheet} "
				f"belongs to a different Job Opening."
			)

	def validate_status_transition(self):
		if self.status not in STATUSES_REQUIRING_APPROVED_GREEN_SHEET:
			return

		if not self.is_new():
			previous_status = frappe.db.get_value("Job Opening", self.name, "status")
			if previous_status == self.status:
				return

		if can_override_status():
			return

		if not self.pre_recruitment_green_sheet:
			frappe.throw(
				f"Job Opening cannot be moved to {self.status} without an approved "
				f"Pre-Recruitment Green Sheet."
			)
		green_sheet_status, green_sheet_docstatus = frappe.db.get_value(
			"Pre-Recruitment Green Sheet",
			self.pre_recruitment_green_sheet,
			["status", "docstatus"],
		)
		if green_sheet_docstatus != 1 or green_sheet_status != "Approved":
			frappe.throw(
				f"Cannot move this Job Opening to {self.status}: its Pre-Recruitment "
				f"Green Sheet is '{green_sheet_status}', not 'Approved'."
			)
