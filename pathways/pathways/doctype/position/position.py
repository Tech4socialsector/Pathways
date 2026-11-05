# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from pathways.pathways.doctype.job_opening.job_opening import validate_form_rows


class Position(Document):
	"""A post the University recruits for, identified by its Job Code. Each
	Job Opening advertises one Position and starts from its defaults."""

	def before_insert(self):
		# The Job Code is the record name, so normalise it before naming.
		self.job_code = (self.job_code or "").strip().upper()

	def validate(self):
		validate_form_rows(self)
		if not cint(self.ask_specialization):
			self.specialization_discipline = None
		if cint(self.ask_publications) and cint(self.min_publications) > cint(self.max_publications):
			frappe.throw(_("Minimum Publications cannot be more than Maximum Publications."))
		self.validate_onboarding_documents()

	def validate_onboarding_documents(self):
		seen = set()
		for row in self.onboarding_documents or []:
			if row.document_type in seen:
				frappe.throw(_("Onboarding document {0} is listed twice.").format(row.document_type))
			seen.add(row.document_type)
			if frappe.db.get_value("Document Type Master", row.document_type, "used_in") not in ("Onboarding", "Both"):
				frappe.throw(
					_("{0} is an application document. Set its Used In to Onboarding or Both in Master Setup › Document Types to use it here.").format(
						row.document_type
					)
				)
