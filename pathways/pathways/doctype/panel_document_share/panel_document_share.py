# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PanelDocumentShare(Document):
	"""Which of a candidate's documents the recruitment team shared with one
	Selection Committee panellist (Documents page > Share with panel)."""

	def validate(self):
		other = frappe.db.exists(
			"Panel Document Share", {"application": self.application, "panelist": self.panelist, "name": ["!=", self.name]}
		)
		if other:
			frappe.throw(_("{0} already has a share record for this application.").format(self.panelist))
