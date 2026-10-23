# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PanelJobFileShare(Document):
	"""Job-level files (notification, panel details, blank assessment sheets,
	shortlisting note, HR interaction notes, interview schedule) shared with
	one Selection Committee panellist (workflow step 16). One per job and panellist."""

	def validate(self):
		other = frappe.db.exists("Panel Job File Share", {"job_opening": self.job_opening, "panelist": self.panelist, "name": ["!=", self.name]})
		if other:
			frappe.throw(_("{0} already has a job file share for this job.").format(self.panelist))
