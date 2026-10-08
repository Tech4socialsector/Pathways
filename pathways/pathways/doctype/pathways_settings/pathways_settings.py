# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt
from frappe.utils.file_manager import get_max_file_size

from pathways.permissions import SCOPED_ROLES

FORMAT_PATTERN = re.compile(r"^[a-z0-9]{1,10}$")


NUMBER_FIELDS = (
	"acceptance_deadline_days",
	"default_shortlisting_ratio",
	"min_shortlisting_committee_size",
	"max_shortlisting_committee_size",
	"min_selection_committee_size",
	"max_selection_committee_size",
)
UPLOAD_FIELDS = ("application_max_file_size_mb", "application_allowed_formats")
ROLE_FIELDS = ("approval_override_role", "status_override_role", "document_verifier_roles", "corrigendum_signer_roles")


class PathwaysSettings(Document):
	def validate(self):
		# Install and migrate seed values on their own. Each check only runs
		# when its own fields change, so an old out-of-range value never
		# blocks an unrelated save (e.g. editing Pathways Roles).
		if frappe.flags.in_install or frappe.flags.in_migrate or frappe.flags.in_patch:
			return
		if self._changed(NUMBER_FIELDS):
			self.validate_numbers()
		if self._changed(UPLOAD_FIELDS):
			self.validate_upload_rules()
		if self._changed(ROLE_FIELDS):
			self.validate_roles()

	def _changed(self, fields):
		before = self.get_doc_before_save()
		if not before:
			return True
		for field in fields:
			now, then = self.get(field), before.get(field)
			if isinstance(now, list):
				now, then = [r.role for r in now], [r.role for r in then or []]
			if now != then:
				return True
		return False

	def validate_numbers(self):
		if not 1 <= cint(self.acceptance_deadline_days) <= 365:
			frappe.throw(_("Offer Acceptance Deadline must be between 1 and 365 days."))
		if cint(self.default_shortlisting_ratio) < 1:
			frappe.throw(_("Default Shortlisting Ratio must be at least 1."))

		for committee, low, high in (
			(_("Shortlisting"), "min_shortlisting_committee_size", "max_shortlisting_committee_size"),
			(_("Selection"), "min_selection_committee_size", "max_selection_committee_size"),
		):
			minimum, maximum = cint(self.get(low)), cint(self.get(high))
			if minimum < 1:
				frappe.throw(_("Min {0} Committee Size must be at least 1.").format(committee))
			if maximum < minimum:
				frappe.throw(
					_("Max {0} Committee Size ({1}) cannot be less than the minimum ({2}).").format(committee, maximum, minimum)
				)

	def validate_upload_rules(self):
		size = flt(self.application_max_file_size_mb)
		site_limit = get_max_file_size() / (1024 * 1024)
		if size <= 0:
			frappe.throw(_("Max Upload Size must be more than 0 MB."))
		if size > site_limit:
			frappe.throw(_("Max Upload Size cannot be more than this site's upload limit of {0} MB.").format(f"{site_limit:g}"))

		# Stored as "PDF, JPG, PNG"; read back by utils.application_form._formats.
		formats = []
		for part in (self.application_allowed_formats or "").split(","):
			fmt = part.strip().lower().lstrip(".")
			if not fmt:
				continue
			if not FORMAT_PATTERN.match(fmt):
				frappe.throw(_("'{0}' is not a file extension. List extensions such as PDF, JPG, PNG.").format(part.strip()))
			if fmt not in formats:
				formats.append(fmt)
		if not formats:
			frappe.throw(_("Allowed Upload Formats needs at least one file extension."))
		self.application_allowed_formats = ", ".join(f.upper() for f in formats)

	def validate_roles(self):
		"""Overrides and duties are staff powers; candidates and committee
		members only ever see their own scoped records."""
		chosen = {
			_("Approval Override Role"): [self.approval_override_role],
			_("Job Status Override Role"): [self.status_override_role],
			_("Document Verifier Roles"): [row.role for row in self.document_verifier_roles],
			_("Corrigendum Signer Roles"): [row.role for row in self.corrigendum_signer_roles],
		}
		for label, roles in chosen.items():
			scoped = sorted({r for r in roles if r in SCOPED_ROLES})
			if scoped:
				frappe.throw(_("{0} cannot include {1}.").format(label, ", ".join(scoped)))
