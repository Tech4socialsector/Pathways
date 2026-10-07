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
	"""Holders of Pathways Settings > Job Status Override Role may set any
	Job Opening status directly, without going through the Pre-Recruitment
	Green Sheet approval chain. System Manager always may, so setting the
	role to e.g. Pathways Admin adds admins rather than locking out the
	site's superusers.
	"""
	roles = frappe.get_roles(user or frappe.session.user)
	role = frappe.get_cached_doc("Pathways Settings").get("status_override_role")
	return "System Manager" in roles or (bool(role) and role in roles)


def get_advertisement_url(job_opening):
	"""Public job posting page in the candidate portal (served to guests
	by pathways.api.application.get_job_opening_detail while Advertised)."""
	return frappe.utils.get_url(f"/pathways/portal/jobs/{job_opening}")


def validate_form_rows(doc):
	"""Screening questions and required documents, as configured on a Job
	Opening or on the Position it starts from."""
	for q in doc.screening_questions or []:
		if q.answer_type == "Single Choice":
			options = [o.strip() for o in (q.options or "").splitlines() if o.strip()]
			if len(options) < 2:
				frappe.throw(_("Screening question {0}: give at least two choices, one per line.").format(q.idx))
			if len(options) != len(set(options)):
				frappe.throw(_("Screening question {0}: choices must be unique.").format(q.idx))
		if q.answer_type != "Yes/No":
			q.ask_details_if_yes = 0

	seen = set()
	for row in doc.required_documents or []:
		if row.document_type in seen:
			frappe.throw(_("Required document {0} is listed twice.").format(row.document_type))
		seen.add(row.document_type)


# Position field -> Job Opening field, filled only where the job leaves it empty.
POSITION_DEFAULTS = {
	"position_title": "job_title",
	"track": "track",
	"department": "department",
	"designation": "designation",
	"employment_type": "employment_type",
	"pay_level": "pay_level",
	"tenure_description": "tenure_description",
}
POSITION_TABLES = ("screening_questions", "required_documents")
# Which extra (academic) sections the apply form shows: taken from the
# Position whenever one is picked, then editable on the job.
FORM_SWITCHES = (
	"institution_list",
	"ask_specialization",
	"specialization_discipline",
	"ask_category_disability",
	"ask_phd",
	"ask_net",
	"ask_experience_months",
	"ask_admin_responsibilities",
	"ask_publications",
	"min_publications",
	"max_publications",
)
TABLE_ROW_FIELDS = {
	"screening_questions": ("question", "answer_type", "options", "is_mandatory", "ask_details_if_yes", "details_label"),
	"required_documents": ("document_type", "is_mandatory"),
}


class JobOpening(Document):
	def validate(self):
		self.apply_position_defaults()
		self.validate_green_sheet_link()
		self.validate_status_transition()
		self.validate_application_form()
		self.set_advertisement_url()

	def apply_position_defaults(self):
		"""When a Position is picked, start the job from it: empty fields and
		empty form tables are filled in, anything HR has already set is kept."""
		if not self.position or not (self.is_new() or self.has_value_changed("position")):
			return
		position = frappe.get_cached_doc("Position", self.position)

		for source, target in POSITION_DEFAULTS.items():
			if not self.get(target) and position.get(source):
				self.set(target, position.get(source))
		if self.is_new() and position.require_postgraduate:
			self.require_postgraduate = 1
		for field in FORM_SWITCHES:
			self.set(field, position.get(field))

		for table in POSITION_TABLES:
			if self.get(table):
				continue
			for row in position.get(table):
				self.append(table, {field: row.get(field) for field in TABLE_ROW_FIELDS[table]})

	def validate_application_form(self):
		validate_form_rows(self)

		if self.status == "Advertised" and self.has_value_changed("status"):
			if not self.application_deadline:
				frappe.throw(_("Set an Application Deadline before advertising this job."))
			if get_datetime(self.application_deadline) <= now_datetime():
				frappe.throw(_("The Application Deadline must be in the future to advertise this job."))

	def set_advertisement_url(self):
		# The posting page only serves Advertised jobs, so the link is kept
		# only while that is true. name is unset before the first insert.
		if self.status == "Advertised" and self.name:
			self.advertisement_url = get_advertisement_url(self.name)
		else:
			self.advertisement_url = None

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
