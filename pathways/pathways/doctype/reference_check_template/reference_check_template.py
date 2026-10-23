# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Question set a referee answers for one recruitment track (workflow step
21). Reference Checks copy the questions when they are created, so editing
a template never changes checks already sent out."""

import frappe
from frappe import _
from frappe.model.document import Document


class ReferenceCheckTemplate(Document):
	def validate(self):
		if not self.questions:
			frappe.throw(_("Add at least one question."))
		# Keep the order staff see in the grid unless they numbered it.
		for idx, row in enumerate(self.questions, start=1):
			if not row.sequence:
				row.sequence = idx
			row.question = (row.question or "").strip()
