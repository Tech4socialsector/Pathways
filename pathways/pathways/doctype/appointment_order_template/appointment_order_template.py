# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Appointment order letters (workflow step 26). Each template is a Jinja
letter body rendered with the offer and application (see
pathways.api.offer.letter_context). Staff add or edit templates from Master
Setup, so a new kind of appointment never needs a code change."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.jinja import validate_template


class AppointmentOrderTemplate(Document):
	def validate(self):
		if not (self.letter_body or "").strip():
			frappe.throw(_("Letter Body is required."))
		# A broken placeholder would only surface when a letter is generated
		# for a real candidate; catch it while the template is being edited.
		validate_template(self.letter_body)
		seen = set()
		for row in self.designations or []:
			if row.designation in seen:
				frappe.throw(_("Designation {0} is listed twice.").format(row.designation))
			seen.add(row.designation)
