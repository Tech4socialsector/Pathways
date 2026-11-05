# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Panel Honorarium is now external experts only, ending with the details
sent to the Finance team: Approved / Paid records become Sent to Finance
(with when they were approved or paid), and external experts marked Not
applicable go back to Pending. Seeds the honorarium_to_finance email."""

import frappe

from pathways.utils.email_events import ensure_email_events


def execute():
	ensure_email_events()
	if not frappe.db.has_column("Panel Honorarium", "approved_on"):
		return
	for r in frappe.get_all(
		"Panel Honorarium",
		filters={"status": ["in", ["Approved", "Paid"]]},
		fields=["name", "approved_by", "approved_on", "paid_on"],
	):
		frappe.db.set_value(
			"Panel Honorarium",
			r.name,
			{"status": "Sent to Finance", "sent_to_finance_on": r.paid_on or r.approved_on, "sent_to_finance_by": r.approved_by},
			update_modified=False,
		)
	frappe.db.set_value("Panel Honorarium", {"is_external": 1, "status": "Not applicable"}, "status", "Pending", update_modified=False)
